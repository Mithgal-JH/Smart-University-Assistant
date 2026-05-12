from services.rag import get_relevant_docs
from services.router import llm_route
from services.user_service import get_student_data
from services.memory import (
    add_to_memory,
    get_memory,
    summarize_memory,
    get_summary,
    set_state,
    get_state,
    clear_state,
)
from services.llm import ask_llm_messages
from services.course_service import (
    add_course,
    get_courses_by_user,
    delete_course,
)
from services.intent import detect_intent
from services.extractor import extract_course_details, extract_course_name
from services.embedding_service import find_top_matches

# كلمات الإلغاء
CANCEL_WORDS = ["cancel", "إلغاء", "الغاء", "لا", "مسح", "خروج", "وقف", "stop"]


def chat(query, user_id):

    query = query.strip()

    history = get_memory(user_id)
    summary = get_summary(user_id)
    state = get_state(user_id)

    # =====================================
    # ⚡ FAST RESPONSES (NO LLM)
    # =====================================

    GREETINGS = {
        "مرحبا": "أهلاً 👋 كيف أقدر أساعدك؟",
        "السلام عليكم": "وعليكم السلام 🌸 كيف أقدر أساعدك؟",
        "هاي": "أهلاً 👋",
        "هلا": "ياهلا 👋",
        "hello": "Hello 👋 How can I help you?",
        "hi": "Hi 👋"
    }

    THANKS = {
        "شكرا": "العفو 🌸",
        "شكراً": "العفو 🌸",
        "يسلمو": "يسعدني مساعدتك 🌸",
        "thanks": "You're welcome 👋"
    }

    RESET_WORDS = [
        "الغاء",
        "إلغاء",
        "وقف",
        "خلاص",
        "توقف",
        "cancel",
        "reset"
    ]
    IDENTITY_QUESTIONS = {
    "من انت": "أنا المساعد الجامعي الذكي 🎓\nأساعدك في المواد، معلومات الجامعة، والخدمات الطلابية.",
    "مين انت": "أنا المساعد الجامعي الذكي 🎓",
    "شو انت": "أنا مساعد جامعي مدعوم بالذكاء الاصطناعي 🤖",
    "ما اسمك": "أنا المساعد الجامعي الذكي 🎓",
    "مين صنعك": "تم تطويري كمشروع مساعد جامعي ذكي لخدمة الطلاب 🎓"
    }
    # IDENTITY_QUESTIONS
    if query.lower() in IDENTITY_QUESTIONS:
        clear_state(user_id)
        return IDENTITY_QUESTIONS[query.lower()]

    # greetings
    if query.lower() in GREETINGS:
        clear_state(user_id)
        return GREETINGS[query.lower()]

    # thanks
    if query.lower() in THANKS:
        return THANKS[query.lower()]

    # reset
    if query.lower() in RESET_WORDS:
        clear_state(user_id)
        return "تم إلغاء العملية الحالية ✅"

    # =====================================
    # 🔴 HANDLE DELETE SELECTION
    # =====================================
    if state and state.get("step") == "choose_delete":

        try:
            choice = int(query) - 1
            course_id = state["options"][choice]
            course_name = state["names"][choice]

            delete_course(course_id, user_id)

            clear_state(user_id)

            return f"تم حذف مادة {course_name} بنجاح ✅"

        except (ValueError, IndexError):
            return "اختيار غير صحيح، اكتب رقم من القائمة."

    # =====================================
    # 🟡 HANDLE MISSING (add course flow)
    # =====================================
    if state and state.get("step") == "collect_missing":

        data = state["data"]
        missing = state["missing"]

        field = missing[0]

        data[field] = query

        missing.pop(0)

        if missing:
            set_state(user_id, {
                "step": "collect_missing",
                "data": data,
                "missing": missing
            })

            return ask_for_field(missing[0])

        success = add_course(
            user_id,
            data["course"],
            data["doctor"],
            data["days"],
            data["time"]
        )

        if not success:
            clear_state(user_id)
            return f"مادة {data['course']} مضافة مسبقاً ❗"

        clear_state(user_id)

        return format_course_response(
            "تم إضافة المادة بنجاح ✅",
            data
        )

    # =====================================
    # 🧠 INTENT
    # =====================================
    intent = detect_intent(query)

    # =====================================
    # 🟢 GET COURSES
    # =====================================
    if intent == "get_courses":

        courses = get_courses_by_user(user_id)

        if not courses:
            return "ما عندك مواد مسجلة حالياً."

        response = "📚 موادك الحالية:\n\n"

        for i, c in enumerate(courses, 1):

            doctor = c.doctor if c.doctor != "غير معروف" else "—"

            days = clean_days_display(c.days)

            time = clean_time_display(c.time)

            response += f"""🔹 {i}. {c.name}
👨‍🏫 {doctor}
📅 {days}
⏰ {time}

"""

        return response

    # =====================================
    # 🔴 DELETE COURSE
    # =====================================
    if intent == "delete_course":

        name = extract_course_name(query)

        if not name:
            return "ما فهمت اسم المادة، ممكن تحدد أكثر؟"

        courses = get_courses_by_user(user_id)

        # 1. exact match
        for c in courses:

            if name in c.name:

                delete_course(c.id, user_id)

                clear_state(user_id)

                return f"تم حذف مادة {c.name} بنجاح ✅"

        # 2. semantic match
        matches = find_top_matches(name, courses)

        if not matches:
            return "ما لقيت مادة قريبة من طلبك."

        if len(matches) == 1:

            target = matches[0][0]

            delete_course(target.id, user_id)

            clear_state(user_id)

            return f"تم حذف مادة {target.name} بنجاح ✅"

        # multiple matches
        set_state(user_id, {
            "step": "choose_delete",
            "options": [c.id for c, _ in matches],
            "names": [c.name for c, _ in matches]
        })

        msg = "لقيت أكثر من مادة:\n\n"

        for i, (c, _) in enumerate(matches, 1):
            msg += f"{i}. {c.name} ({c.doctor} - {c.days})\n"

        msg += "\nاكتب رقم المادة، أو اكتب 'إلغاء' للتراجع."

        return msg

    # =====================================
    # 🟡 ADD COURSE
    # =====================================
    if intent == "add_course":

        data = extract_course_details(query)

        missing = [
            field for field in ["course", "doctor", "days", "time"]
            if not data.get(field)
            or data[field] == "غير معروف"
        ]

        if missing:

            set_state(user_id, {
                "step": "collect_missing",
                "data": data,
                "missing": missing
            })

            return ask_for_field(missing[0])

        success = add_course(
            user_id,
            data["course"],
            data["doctor"],
            data["days"],
            data["time"]
        )

        if not success:
            return f"مادة {data['course']} مضافة مسبقاً ❗"

        clear_state(user_id)

        return format_course_response(
            "تم إضافة المادة مباشرة ✅",
            data
        )

    # =====================================
    # 🔥 NORMAL (RAG / PERSONAL / HYBRID)
    # =====================================
    route = llm_route(query)

    # =====================================
    # 👤 PERSONAL
    # =====================================
    if route == "personal":

        student = get_student_data(user_id)

        if not student:
            return "لا توجد بيانات محفوظة لك حالياً."

        prompt = f"""
أنت مساعد جامعي عربي.

بيانات الطالب:
- التخصص: {student['major']}
- المعدل: {student['gpa']}

سؤال المستخدم:
{query}

أجب بالعربية فقط.
"""

        return run_llm(prompt, history, summary, user_id, query)

    # =====================================
    # 📚 RAG
    # =====================================
    elif route == "rag":

        docs = get_relevant_docs(query)

        context = "\n\n---\n\n".join(
            [d.page_content for d in docs]
        )

        prompt = f"""
أنت مساعد جامعي ذكي يتحدث العربية فقط.

تعليمات مهمة:
- أجب بالعربية فقط
- استخدم المعلومات الموجودة في السياق فقط
- لا تخترع أي معلومة
- إذا كانت المعلومات بالإنجليزية قم بترجمتها للعربية
- اجعل الإجابة مرتبة وواضحة
- استخدم تعداداً نقطياً أو أرقاماً عند وجود عدة عناصر
- إذا لم تجد معلومات كافية قل:
"لا أملك معلومات كافية حول ذلك."

السياق:
{context}

سؤال المستخدم:
{query}

الإجابة:
"""

        return run_llm(prompt, history, summary, user_id, query)

    # =====================================
    # 🔀 HYBRID
    # =====================================
    elif route == "hybrid":

        student = get_student_data(user_id)

        if not student:
            return "لا توجد بيانات محفوظة لك حالياً."

        docs = get_relevant_docs(query)

        context = "\n\n---\n\n".join(
            [d.page_content for d in docs]
        )

        prompt = f"""
أنت مساعد جامعي عربي.

بيانات الطالب:
- التخصص: {student['major']}
- المعدل: {student['gpa']}

معلومات الجامعة:
{context}

تعليمات:
- أجب بالعربية فقط
- لا تخترع معلومات
- استخدم البيانات المتوفرة فقط
- اجعل الإجابة مرتبة وواضحة

سؤال المستخدم:
{query}

الإجابة:
"""

        return run_llm(prompt, history, summary, user_id, query)

    return "لم أفهم سؤالك."

# =====================================
# HELPERS
# =====================================

def ask_for_field(field):
    if field == "course":
        return "ما اسم المادة؟"
    if field == "doctor":
        return "مع أي دكتور؟"
    if field == "days":
        return "في أي أيام؟"
    if field == "time":
        return "في أي ساعة؟"


def format_course_response(title, data):
    return f"""{title}

📚 المادة: {data['course']}
👨‍🏫 الدكتور: {data['doctor']}
📅 الأيام: {data['days']}
⏰ الوقت: {data['time']}
"""


def run_llm(prompt, history, summary, user_id, query):
    system_messages = (
        [{"role": "system", "content": f"ملخص المحادثة السابقة: {summary}"}]
        if summary else []
    )

    messages = system_messages + history + [{"role": "user", "content": prompt}]

    response = ask_llm_messages(messages).strip()

    add_to_memory(user_id, "user", query)
    add_to_memory(user_id, "assistant", response)

    if len(get_memory(user_id)) >= 6:
        summarize_memory(user_id)

    return response


# =====================================
# 🔧 HELPERS (display cleaning)
# =====================================

def clean_days_display(days):
    if not days or days == "غير معروف":
        return "—"
    return days.replace("الأيام", "").strip()


def clean_time_display(time):
    if not time or time == "غير معروف":
        return "—"
    return time.replace("الساعة", "").strip()
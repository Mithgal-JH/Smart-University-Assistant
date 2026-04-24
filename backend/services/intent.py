from services.llm import ask_llm_messages

# =====================================
# KEYWORD MAPS (fast, no LLM needed)
# =====================================

ADD_KEYWORDS = [
    "أضف", "أضيف", "اضف", "إضافة", "اضافة",
    "سجل", "سجلني", "تسجيل", "ادرج", "ضيف"
]

DELETE_KEYWORDS = [
    "احذف", "حذف", "امسح", "مسح", "إلغاء تسجيل",
    "شيل", "ازل", "ازيل", "أزل"
]

GET_KEYWORDS = [
    "مواد", "موادي", "جدولي", "جدول",
    "عرض", "اعرض", "وين", "شو", "كم مادة",
    "المسجلة", "المواد المسجلة"
]


def detect_intent(query: str) -> str:
    query_stripped = query.strip()

    # =====================================
    # 1. KEYWORD CHECK
    # =====================================
    for kw in ADD_KEYWORDS:
        if kw in query_stripped:
            return "add_course"

    for kw in DELETE_KEYWORDS:
        if kw in query_stripped:
            return "delete_course"

    for kw in GET_KEYWORDS:
        if kw in query_stripped:
            return "get_courses"

    # =====================================
    # 2. LLM FALLBACK
    # =====================================
    prompt = f"""
صنّف نية المستخدم إلى واحدة من التالي فقط:

- add_course    → يريد إضافة مادة أو تسجيلها
- delete_course → يريد حذف مادة أو إلغاء تسجيلها
- get_courses   → يريد عرض مواده المسجلة
- normal        → سؤال عادي لا علاقة له بالمواد

أمثلة:
"أضف مادة رياضيات" → add_course
"احذف مادة الفيزياء" → delete_course
"وش موادي؟" → get_courses
"ما هي شروط التخرج؟" → normal

الرسالة:
{query_stripped}

أعد كلمة واحدة فقط من القائمة.
"""

    response = ask_llm_messages([
        {"role": "user", "content": prompt}
    ])

    intent = response.strip().lower()

    # normalization
    if "add_course" in intent:
        return "add_course"
    if "delete_course" in intent:
        return "delete_course"
    if "get_courses" in intent:
        return "get_courses"

    return "normal"
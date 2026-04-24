import json
import re
from services.llm import ask_llm_messages


# =====================================
# 🚀 MAIN FUNCTION
# =====================================

def extract_course_details(text: str):

    # 🔥 1. حاول regex أول (سريع)
    regex_data = regex_extract(text)

    # الرجوع فقط إذا لقى الكل — مش بس الاسم
    # (الرجوع المبكر بالاسم بس كان يمرر time خاطئ من أي رقم في الجملة)
    all_found = all(v != "غير معروف" for v in regex_data.values())
    if all_found:
        return regex_data

    # 🔥 2. fallback → LLM
    llm_data = llm_extract(text)

    # 🔥 3. validation (منع hallucination)
    # إذا regex لقى شي موثوق نستخدمه، وإلا نستخدم LLM المُتحقق
    validated = {}
    for field in ["course", "doctor", "days", "time"]:
        if regex_data.get(field) and regex_data[field] != "غير معروف":
            validated[field] = regex_data[field]
        else:
            validated[field] = validate(llm_data.get(field), text)

    return validated


# =====================================
# ⚡ REGEX EXTRACTOR
# =====================================

def regex_extract(text: str):

    # 🟡 course
    course_match = re.search(r"(?:مادة|مساق)\s+(.+?)(?:\s+مع|\s*$)", text)
    course = course_match.group(1).strip() if course_match else "غير معروف"

    # 🟡 doctor
    doctor_match = re.search(r"(?:مع\s+)?(?:الدكتور|دكتور|د\.)\s+(\S+(?:\s+\S+)?)", text)
    doctor = doctor_match.group(1).strip() if doctor_match else "غير معروف"

    # 🟡 days — يجمع أكثر من يوم لو موجودين
    day_names = ["الأحد", "الاثنين", "الثلاثاء", "الأربعاء", "الخميس", "الجمعة", "السبت"]
    found_days = re.findall("|".join(day_names), text)
    days = " و ".join(found_days) if found_days else "غير معروف"

    # 🟡 time — يشترط كلمة ساعة أو صباحاً أو مساءً بجانب الرقم
    # (منع استخراج أي رقم عشوائي في الجملة كـ "3 وحدات")
    time_match = re.search(r"(?:الساعة\s*)?(\d{1,2}(?::\d{2})?)\s*(?:صباحاً|مساءً|AM|PM|ص|م)", text)
    if not time_match:
        time_match = re.search(r"الساعة\s+(\d{1,2}(?::\d{2})?)", text)
    time = time_match.group(1).strip() if time_match else "غير معروف"

    return {
        "course": course,
        "doctor": doctor,
        "days": days,
        "time": time
    }


# =====================================
# 🧠 LLM EXTRACTOR
# =====================================

def llm_extract(text: str):
    prompt = f"""
استخرج المعلومات التالية من النص.

⚠️ قواعد صارمة:
- إذا المعلومة غير موجودة → اكتب "غير معروف"
- لا تخمّن
- لا تضف معلومات من عندك

الشكل:

{{
  "course": "...",
  "doctor": "...",
  "days": "...",
  "time": "..."
}}

النص:
{text}

أعد JSON فقط.
"""

    try:
        response = ask_llm_messages([
            {"role": "user", "content": prompt}
        ])

        cleaned = clean_response(response)
        return safe_json_load(cleaned)

    except Exception as e:
        print("❌ LLM ERROR:", e)
        return fallback()


# =====================================
# 🧠 CLEANING
# =====================================

def clean_response(response):
    cleaned = response.strip()
    cleaned = cleaned.replace("```json", "").replace("```", "")

    match = re.search(r"\{.*", cleaned, re.DOTALL)

    if not match:
        return "{}"

    json_text = match.group().strip()

    if not json_text.endswith("}"):
        json_text += "}"

    return json_text


def safe_json_load(json_text):
    try:
        return json.loads(json_text)
    except Exception:
        return {}


# =====================================
# 🛡️ VALIDATION (ANTI-HALLUCINATION)
# =====================================

def validate(value, text):
    if not value or value == "غير معروف":
        return "غير معروف"

    value_clean = str(value).lower().strip()
    text_lower = text.lower()

    if value_clean in text_lower:
        return value.strip()

    return "غير معروف"


# =====================================
# 🔴 FALLBACK
# =====================================

def fallback():
    return {
        "course": "غير معروف",
        "doctor": "غير معروف",
        "days": "غير معروف",
        "time": "غير معروف"
    }


# =====================================
# 🧠 COURSE NAME EXTRACT
# =====================================

def extract_course_name(text: str):
    # 🔥 regex سريع
    match = re.search(r"(?:مادة|مساق)\s+(.+)", text)

    if match:
        return match.group(1).strip()

    # fallback → LLM
    prompt = f"""
استخرج اسم المادة فقط من النص.
إذا ما في اسم واضح، أعد كلمة "غير معروف" فقط.

النص:
{text}

أعد الاسم فقط.
"""

    try:
        response = ask_llm_messages([
            {"role": "user", "content": prompt}
        ])

        name = response.strip().replace("مادة", "").strip()

        # إذا LLM رجع جملة طويلة أو "غير معروف"
        if name == "غير معروف" or len(name) > 60:
            return ""

        return name

    except Exception:
        return ""
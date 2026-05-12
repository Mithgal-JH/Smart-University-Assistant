from services.llm import ask_llm_messages

def llm_route(query: str):

    prompt = f"""
              أنت نظام تصنيف نوايا لمساعد جامعي.

              صنف السؤال إلى واحدة فقط من:

              - personal
              → إذا السؤال عن بيانات الطالب الشخصية فقط
              مثل:
              "ما معدلي؟"
              "ما تخصصي؟"
              "ما موادي؟"

              - rag
              → إذا السؤال عن معلومات الجامعة العامة
              مثل:
              "ما هي برامج الدراسات العليا؟"
              "ما هي كليات الجامعة؟"
              "متى يبدأ الفصل الدراسي؟"
              "ما هي قوانين الجامعة؟"

              - hybrid
              → إذا السؤال يحتاج بيانات الطالب + معلومات الجامعة
              مثل:
              "هل معدلي يسمح بالتخصص؟"

              السؤال:
              {query}

              أعد كلمة واحدة فقط:
              """
    response = ask_llm_messages([
      {"role": "user", "content": prompt}
    ])

    response = response.strip().lower()

    if "personal" in response:
        return "personal"
    elif "hybrid" in response:
        return "hybrid"
    else:
        return "rag"
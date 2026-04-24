from services.llm import ask_llm_messages

def llm_route(query: str):

    prompt = f"""
    صنّف السؤال التالي إلى واحدة من الفئات التالية فقط:

    - personal (إذا السؤال عن بيانات الطالب مثل التخصص، المعدل، المواد)
    - rag (إذا السؤال عن سياسات الجامعة أو معلومات عامة)
    - hybrid (إذا السؤال يحتاج الاثنين)

    السؤال:
    {query}

    الجواب يجب أن يكون كلمة واحدة فقط:
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
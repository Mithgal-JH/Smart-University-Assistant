import requests


def ask_llm_messages(messages):
    # استخدام /api/chat بدل /api/generate
    # لأن generate يفقد بنية الـ roles ويحولها لنص واحد
    try:
        response = requests.post(
            "http://localhost:11434/api/chat",
            json={
                "model": "llama3",
                "messages": messages,
                "stream": False
            },
            timeout=60
        )
        response.raise_for_status()
        return response.json()["message"]["content"]

    except requests.exceptions.Timeout:
        print("❌ LLM timeout")
        return "عذراً، النموذج لم يستجب في الوقت المحدد."

    except requests.exceptions.ConnectionError:
        print("❌ LLM connection error")
        return "عذراً، لا يمكن الاتصال بالنموذج حالياً."

    except Exception as e:
        print(f"❌ LLM error: {e}")
        return "عذراً، حدث خطأ أثناء معالجة طلبك."
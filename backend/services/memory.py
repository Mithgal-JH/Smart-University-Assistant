from services.llm import ask_llm_messages


memory_store = {}
summary_store = {}


def add_to_memory(user_id, role, content):
    if user_id not in memory_store:
        memory_store[user_id] = []

    memory_store[user_id].append({
        "role": role,
        "content": content
    })


    memory_store[user_id] = memory_store[user_id][-10:]


def get_memory(user_id):
    return memory_store.get(user_id, [])


def get_summary(user_id):
    return summary_store.get(user_id, "")


def summarize_memory(user_id):
    history = memory_store.get(user_id, [])

    if not history:
        return ""

    messages_text = ""
    for msg in history:
        messages_text += f"{msg['role']}: {msg['content']}\n"

    prompt = f"""
قم بتلخيص المحادثة التالية بشكل قصير وواضح:

{messages_text}

التلخيص:
"""

    summary = ask_llm_messages([
        {"role": "user", "content": prompt}
    ])

    summary_store[user_id] = summary.strip()
    
    memory_store[user_id] = memory_store[user_id][-2:]

    return summary


# =====================================
# STATE
# =====================================

state_store = {}


def set_state(user_id, state):
    state_store[user_id] = state


def get_state(user_id):
    return state_store.get(user_id)


def clear_state(user_id):
    if user_id in state_store:
        del state_store[user_id]
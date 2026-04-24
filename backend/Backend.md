# PPU Chatbot — Backend Documentation

A smart university chatbot backend built with FastAPI. Supports RAG-based Q&A, personal student data queries, and full course management through natural language.

---

## Table of Contents

- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Getting Started](#getting-started)
- [Architecture Overview](#architecture-overview)
- [Chat Flow](#chat-flow)
- [Intent Detection](#intent-detection)
- [Course Management](#course-management)
- [RAG & Routing](#rag--routing)
- [Memory & Summarization](#memory--summarization)
- [Extractor (Anti-Hallucination)](#extractor-anti-hallucination)
- [API Reference](#api-reference)
- [Database Models](#database-models)

---

## Tech Stack

| Layer | Technology |
|---|---|
| Framework | FastAPI |
| LLM | LLaMA 3 via Ollama |
| Vector Store | ChromaDB |
| Embeddings | `all-MiniLM-L6-v2` (sentence-transformers) |
| Database | SQLite + SQLAlchemy |
| Similarity | scikit-learn cosine similarity |

---

## Project Structure

```
backend/
├── main.py                  # App entry point, route registration
├── data/
│   └── policies.txt         # University policy documents (RAG source)
├── db/
│   ├── connection.py        # SQLAlchemy engine + session factory
│   └── models.py            # ORM models: User, Student, Course
├── routes/
│   ├── chat.py              # POST /chat
│   ├── courses.py           # GET /courses, DELETE /courses/{id}
│   ├── user.py              # User routes
│   └── rag.py               # RAG utility routes
├── services/
│   ├── chat.py              # Main chat logic + state machine
│   ├── intent.py            # LLM-based intent classification
│   ├── extractor.py         # Course detail extraction (regex + LLM + validation)
│   ├── router.py            # LLM-based RAG/personal/hybrid routing
│   ├── memory.py            # Conversation memory + summarization + state
│   ├── llm.py               # Ollama API wrapper
│   ├── rag.py               # ChromaDB retrieval
│   ├── embedding_service.py # Semantic similarity for course matching
│   ├── course_service.py    # Course DB operations
│   └── user_service.py      # Student data DB operations
└── vectorstore/             # ChromaDB persisted data
```

---

## Getting Started

**Prerequisites:** Python 3.10+, [Ollama](https://ollama.ai) running locally with LLaMA 3.

```bash
# 1. Install dependencies
pip install fastapi uvicorn sqlalchemy chromadb sentence-transformers scikit-learn requests

# 2. Pull the model
ollama pull llama3

# 3. Run the server
uvicorn main:app --reload
```

The API will be available at `http://localhost:8000`. Verify with:

```
GET http://localhost:8000/
→ {"message": "PPU Chatbot is running 🚀"}
```

---

## Architecture Overview

Every message passes through three layers in order:

**Layer 1 — State check.** If the user is mid-flow (adding a course step-by-step or confirming a delete), the message is handled by the state machine and returns early. No LLM call for intent is needed.

**Layer 2 — Intent detection.** If no active state, the message is classified by the LLM into one of five intents: `get_courses`, `delete_course`, `add_course`, `normal`. Each intent has its own handler.

**Layer 3 — RAG routing.** Only for `normal` messages: a second LLM call classifies the query into `personal`, `rag`, or `hybrid`, which determines what context is injected into the final prompt.

---

## Chat Flow

All routing logic lives in `services/chat.py`.

```
Incoming message
      │
      ▼
 Active state?  ──Yes──▶  State handler  ──▶  return
      │
      No
      │
      ▼
 detect_intent()
      │
      ├──▶ get_courses   → query DB, format list
      ├──▶ delete_course → extract name → exact/semantic match → confirm or delete
      ├──▶ add_course    → extract details → fill missing fields → save
      └──▶ normal        → llm_route() → personal / rag / hybrid
```

**Cancellation:** At any point in a multi-step flow, the user can type a cancel word (`إلغاء`, `cancel`, `لا`, `خروج`, etc.) to exit the flow and clear the state.

---

## Intent Detection

**File:** `services/intent.py`

A single LLM call classifies each incoming message into one label. The model is instructed to return one word only. The result is normalized with substring matching to guard against slight LLM variations in output.

| Intent | Triggered when |
|---|---|
| `get_courses` | User asks to see their courses |
| `delete_course` | User asks to remove a course |
| `add_course` | User wants to add a course (full or partial info) |
| `normal` | General university question or personal query |

---

## Course Management

### Adding a course

When `add_course` intent is detected, `extract_course_details()` attempts to pull four fields from the message: `course`, `doctor`, `days`, `time`.

Any field that comes back as `"غير معروف"` (unknown) is added to a `missing` list. If there are missing fields, the state machine stores the partial data and asks the user for each field one at a time. Once all fields are collected, the course is saved.

Duplicate prevention is done by exact name match per user before inserting.

### Deleting a course

The delete flow uses a two-step matching strategy:

1. **Exact match:** checks if the extracted course name is a substring of any stored course name. If found, deletes immediately.
2. **Semantic match:** if no exact match, computes cosine similarity between the query name and all stored course names using `all-MiniLM-L6-v2`. Returns matches above a 0.5 threshold.

If exactly one semantic match is found, it deletes automatically. If multiple matches are found, it presents a numbered list and waits for the user to choose.

### Getting courses

Queries all courses for the user and formats them into a readable list. Fields like `"غير معروف"` are replaced with `—` in the display.

---

## RAG & Routing

**Files:** `services/router.py`, `services/rag.py`

For `normal` intent messages, a second LLM call routes to one of three strategies:

| Route | Context injected into prompt |
|---|---|
| `personal` | Student's major and GPA from the database |
| `rag` | Retrieved document chunks from ChromaDB |
| `hybrid` | Both student data and retrieved documents |

Documents are ingested from `data/policies.txt` and stored in ChromaDB. Retrieval uses the default ChromaDB similarity search.

---

## Memory & Summarization

**File:** `services/memory.py`

Each user has an in-memory conversation history (last 10 messages). When the history reaches 6 messages, it is summarized by the LLM into a short paragraph, which replaces the full history. After summarization, only the last 2 messages are kept in the active history window.

The summary is prepended to every LLM call as a system message, so the model retains context across long conversations without exceeding token limits.

State (multi-step flows) is stored separately from memory and is always cleared as soon as a flow completes or is cancelled.

> **Note:** Memory and state are stored in-memory dictionaries and are reset when the server restarts. This is intentional for the current development stage.

---

## Extractor (Anti-Hallucination)

**File:** `services/extractor.py`

Course details are extracted through a layered pipeline designed to minimize hallucination:

**Step 1 — Regex fast path.** Attempts to extract all four fields using pattern matching. Only returns the regex result if *all four fields* were found. This prevents a partial regex result (e.g., found course name but extracted a random number as the time) from bypassing validation.

**Step 2 — LLM extraction.** If any field is missing, the LLM is prompted with strict instructions: return `"غير معروف"` for anything not explicitly stated in the text.

**Step 3 — Validation.** Every LLM-extracted value is checked against the original input text using substring matching. If the value does not appear in the original text, it is rejected and replaced with `"غير معروف"`. This is the primary hallucination guard.

Fields that were successfully extracted by regex in Step 1 are trusted and not re-validated — only the LLM-provided fields go through the validator.

---

## API Reference

### `POST /chat`

The main chat endpoint.

**Request body:**
```json
{
  "query": "أضف مادة رياضيات مع دكتور أحمد الاثنين الساعة 10 صباحاً",
  "user_id": 1
}
```

**Response:**
```json
{
  "response": "تم إضافة المادة مباشرة ✅\n\n📚 المادة: رياضيات\n..."
}
```

---

### `GET /courses`

Returns all courses for a user.

**Query params:** `user_id=1`

**Response:**
```json
[
  {
    "id": 1,
    "name": "رياضيات",
    "doctor": "أحمد",
    "days": "الاثنين",
    "time": "10"
  }
]
```

---

### `DELETE /courses/{course_id}`

Deletes a course by ID. Requires `user_id` as a query param to verify ownership.

**Query params:** `user_id=1`

**Response:**
```json
{ "message": "تم حذف المادة بنجاح ✅" }
```

---

## Database Models

**File:** `db/models.py` — SQLite via SQLAlchemy

```
User
├── id          Integer, PK
└── email       String, unique

Student
├── id          Integer, PK
├── user_id     FK → users.id
├── major       String
└── gpa         Float

Course
├── id          Integer, PK
├── user_id     FK → users.id
├── name        String
├── doctor      String
├── days        String
└── time        String
```

The database file is created automatically at `ppu.db` on first run via `Base.metadata.create_all()`.
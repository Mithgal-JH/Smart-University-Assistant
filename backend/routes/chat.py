from fastapi import APIRouter, Depends
from pydantic import BaseModel
from services.chat import chat
from services.firebase_auth import verify_firebase_token

router = APIRouter()


class ChatRequest(BaseModel):
    query: str
    # ⚠️ user_id اتشال من الـ body — بيجي الآن من Firebase token


@router.post("/chat")
def chat_endpoint(
    req: ChatRequest,
    uid: str = Depends(verify_firebase_token)   # ✅ Firebase UID تلقائي
):
    """
    - uid يجي من Firebase ID Token في الـ Authorization header
    - ما في حاجة للـ user_id في الـ body
    """
    response = chat(req.query, uid)
    return {"response": response}
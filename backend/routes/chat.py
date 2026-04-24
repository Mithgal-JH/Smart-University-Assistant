from fastapi import APIRouter
from services.chat import chat
from pydantic import BaseModel

router = APIRouter()

class ChatRequest(BaseModel):
    query: str
    user_id: int

@router.post("/chat")
def chat_endpoint(req: ChatRequest):
    response = chat(req.query, req.user_id)
    return {"response": response}
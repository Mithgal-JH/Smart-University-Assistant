from fastapi import FastAPI
from db.connection import engine
from db.models import Base
from routes import user
from routes import rag
from routes import chat
from routes import courses

app = FastAPI()

Base.metadata.create_all(bind=engine)

# Routes
app.include_router(user.router)
app.include_router(rag.router)
app.include_router(chat.router)
app.include_router(courses.router)

@app.get("/")
def root():
    return {"message": "PPU Chatbot is running 🚀"}
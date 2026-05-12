from fastapi import FastAPI
from db.connection import engine
from db.models import Base
from routes import user
from routes import rag
from routes import chat
from routes import courses
from routes import me
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


Base.metadata.create_all(bind=engine)

# Routes
app.include_router(user.router)
app.include_router(rag.router)
app.include_router(chat.router)
app.include_router(courses.router)
app.include_router(me.router)

@app.get("/")
def root():
    return {"message": "PPU Chatbot is running 🚀"}
from fastapi import APIRouter
from services.rag import load_and_store_docs

router = APIRouter()

@router.post("/ingest")
def ingest():
    load_and_store_docs()
    return {"message": "Docs stored successfully"}
from langchain_community.vectorstores import Chroma

from langchain_community.document_loaders import (
    DirectoryLoader,
    TextLoader,
    PyPDFLoader
)

from langchain_text_splitters import RecursiveCharacterTextSplitter

from langchain_huggingface import HuggingFaceEmbeddings


persist_directory = "./vectorstore"


def load_and_store_docs():

    # =========================
    # TXT FILES
    # =========================
    txt_loader = DirectoryLoader(
        "data",
        glob="**/*.txt",
        loader_cls=TextLoader
    )

    # =========================
    # PDF FILES
    # =========================
    pdf_loader = DirectoryLoader(
        "data/pdfs",
        glob="**/*.pdf",
        loader_cls=PyPDFLoader
    )

    txt_docs = txt_loader.load()
    pdf_docs = pdf_loader.load()

    documents = txt_docs + pdf_docs

    print(f"📄 Loaded {len(documents)} documents")

    # =========================
    # SPLITTING
    # =========================
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=150
    )

    docs = splitter.split_documents(documents)

    print(f"✂️ Split into {len(docs)} chunks")

    # =========================
    # EMBEDDINGS
    # =========================
    embedding = HuggingFaceEmbeddings(
        model_name="all-MiniLM-L6-v2"
    )

    # =========================
    # VECTOR DB
    # =========================
    vectordb = Chroma.from_documents(
        docs,
        embedding,
        persist_directory=persist_directory
    )

    print("✅ Vector DB created successfully")


def get_relevant_docs(query):

    embedding = HuggingFaceEmbeddings(
        model_name="all-MiniLM-L6-v2"
    )

    vectordb = Chroma(
        persist_directory=persist_directory,
        embedding_function=embedding
    )

    return vectordb.similarity_search(query, k=5)
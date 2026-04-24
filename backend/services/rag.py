from langchain_community.vectorstores import Chroma
from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import CharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings

persist_directory = "./vectorstore"


def load_and_store_docs():
    loader = TextLoader("data/policies.txt", encoding="utf-8")
    documents = loader.load()

    splitter = CharacterTextSplitter(chunk_size=800, chunk_overlap=100)
    docs = splitter.split_documents(documents)

    embedding = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

    vectordb = Chroma.from_documents(
        docs, embedding, persist_directory=persist_directory
    )

    vectordb.persist()


def get_relevant_docs(query):
    embedding = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

    vectordb = Chroma(persist_directory=persist_directory, embedding_function=embedding)

    return vectordb.similarity_search(query, k=3)

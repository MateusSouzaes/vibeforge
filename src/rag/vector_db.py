import chromadb
from chromadb.config import Settings

client = chromadb.Client(Settings(
    persist_directory="data/db"
))

collection = client.get_or_create_collection("akita")

def salvar(documento, embedding, id):
    collection.add(
        documents=[documento],
        embeddings=[embedding],
        ids=[id]
    )

def buscar(embedding, n=5):
    return collection.query(
        query_embeddings=[embedding],
        n_results=n
    )
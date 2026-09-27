import uuid
import chromadb

client = chromadb.PersistentClient(path="./chroma_db")

collection = client.get_or_create_collection(
    name="documents"
)


def reset_collection():
    global collection

    try:
        client.delete_collection(name="documents")
    except Exception:
        pass

    collection = client.get_or_create_collection(
        name="documents"
    )


def add_chunks(chunks, embeddings, metadatas):

    ids = [str(uuid.uuid4()) for _ in chunks]

    collection.add(
        ids=ids,
        documents=chunks,
        embeddings=embeddings,
        metadatas=metadatas
    )


def search_chunks(query_embedding, n_results=5):

    return collection.query(
        query_embeddings=[query_embedding],
        n_results=n_results
    )
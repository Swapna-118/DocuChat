from sentence_transformers import SentenceTransformer


model = SentenceTransformer("all-MiniLM-L6-v2")


def create_embeddings(chunks: list[str]):
    return model.encode(chunks).tolist()
if __name__ == "__main__":
    test_chunks = [
        "Computer organization deals with the structure of a computer.",
        "The CPU executes instructions."
    ]

    embeddings = create_embeddings(test_chunks)

    print("Number of embeddings:", len(embeddings))
    print("Vector size:", len(embeddings[0]))
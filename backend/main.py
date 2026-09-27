from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

import pymupdf
import ollama

from app.chunking import chunk_text
from app.embeddings import create_embeddings
from app.vector_store import (
    add_chunks,
    search_chunks,
    reset_collection,
)


app = FastAPI(title="DocuChat API")


# --------------------------------------------------
# CORS
# --------------------------------------------------

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --------------------------------------------------
# Chat request model
# --------------------------------------------------

class ChatRequest(BaseModel):
    question: str
    history: list[dict] = Field(default_factory=list)


# --------------------------------------------------
# Home
# --------------------------------------------------

@app.get("/")
def home():
    return {
        "message": "DocuChat API is running!"
    }


# --------------------------------------------------
# Upload PDF
# --------------------------------------------------

@app.post("/upload")
async def upload_pdf(file: UploadFile = File(...)):

    # Replace the previous PDF
    reset_collection()

    contents = await file.read()

    document = pymupdf.open(
        stream=contents,
        filetype="pdf"
    )

    page_count = len(document)

    all_chunks = []
    metadatas = []

    # Extract text page by page
    for page_number, page in enumerate(
        document,
        start=1
    ):

        text = page.get_text()

        if not text.strip():
            continue

        page_chunks = chunk_text(text)

        for chunk in page_chunks:

            all_chunks.append(chunk)

            metadatas.append({
                "filename": file.filename,
                "page": page_number
            })

    document.close()

    # Handle PDF with no readable text
    if not all_chunks:
        return {
            "filename": file.filename,
            "pages": page_count,
            "chunks": 0,
            "message": "No readable text was found in this PDF."
        }

    # Create embeddings
    embeddings = create_embeddings(
        all_chunks
    )

    # Store in ChromaDB
    add_chunks(
        all_chunks,
        embeddings,
        metadatas
    )

    return {
        "filename": file.filename,
        "pages": page_count,
        "chunks": len(all_chunks),
        "message": "PDF processed and stored successfully!"
    }


# --------------------------------------------------
# Chat
# --------------------------------------------------

@app.post("/chat")
def chat(request: ChatRequest):

    current_question = request.question
    history = request.history

    # --------------------------------------------------
    # Create a context-aware search query
    # --------------------------------------------------

    search_query = current_question

    if history:

        recent_history = history[-4:]

        previous_conversation = "\n".join(
            [
                f"{message.get('role')}: "
                f"{message.get('content')}"
                for message in recent_history
            ]
        )

        search_query = f"""
Previous conversation:

{previous_conversation}

Current question:

{current_question}
"""

    # --------------------------------------------------
    # Create query embedding
    # --------------------------------------------------

    query_embedding = create_embeddings(
        [search_query]
    )[0]

    # --------------------------------------------------
    # Search relevant PDF chunks
    # --------------------------------------------------

    results = search_chunks(
        query_embedding,
        n_results=5
    )

    relevant_chunks = results["documents"][0]
    metadata = results["metadatas"][0]

    # --------------------------------------------------
    # Build PDF context
    # --------------------------------------------------

    context_parts = []

    for chunk, meta in zip(
        relevant_chunks,
        metadata
    ):

        context_parts.append(
            f"""
Source: {meta['filename']}
Page: {meta['page']}

Content:
{chunk}
"""
        )

    context = "\n\n---\n\n".join(
        context_parts
    )

    # --------------------------------------------------
    # Build conversation history
    # --------------------------------------------------

    conversation = ""

    for message in history:

        role = message.get(
            "role",
            ""
        )

        content = message.get(
            "content",
            ""
        )

        conversation += f"""
{role}: {content}
"""

    # --------------------------------------------------
    # Create LLM prompt
    # --------------------------------------------------

    prompt = f"""
You are DocuChat, a PDF question-answering assistant.

Your job is to answer the user's question using
ONLY information supported by the PDF context.

You can use the previous conversation to understand
what the user means when they say things like:

- "it"
- "this"
- "that"
- "the previous answer"
- "explain it"
- "explain that"

However, your answer must still be grounded
in the PDF context.

If the answer cannot be found in the PDF context,
say:

"I couldn't find the answer in the uploaded documents."

Do not make up information.

Do not use outside knowledge.

Previous conversation:

{conversation}

PDF context:

{context}

Current user question:

{current_question}
"""

    # --------------------------------------------------
    # Ask Ollama
    # --------------------------------------------------

    response = ollama.chat(
        model="llama3.2:3b",
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ]
    )

    answer = response["message"]["content"]

    # --------------------------------------------------
    # Prepare sources
    # --------------------------------------------------

    sources = []

    for meta in metadata:

        source = {
            "filename": meta["filename"],
            "page": meta["page"]
        }

        if source not in sources:
            sources.append(source)

    # --------------------------------------------------
    # Return response
    # --------------------------------------------------

    return {
        "question": current_question,
        "answer": answer,
        "sources": sources
    }
# DocuChat

DocuChat is an AI-powered PDF question-answering application that allows users to upload a PDF and have a conversation with its contents.

The application uses Retrieval-Augmented Generation (RAG) to retrieve relevant sections from the uploaded document before generating an answer.

## Features

- Upload PDF documents
- Extract text from PDFs
- Split documents into smaller chunks
- Generate semantic embeddings
- Store embeddings in ChromaDB
- Retrieve relevant document sections using semantic search
- Ask questions about uploaded documents
- Conversational follow-up questions
- Source citations with PDF filename and page number
- Replace the active PDF without mixing document data
- Local LLM inference using Ollama

## Architecture

```text
PDF
 ↓
Text Extraction
 ↓
Chunking
 ↓
Embeddings
 ↓
ChromaDB
 ↓
Semantic Retrieval
 ↓
Relevant Context
 ↓
Ollama LLM
 ↓
Answer + Sources

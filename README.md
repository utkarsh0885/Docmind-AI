# 🧠 DocMind AI

Enterprise Knowledge Assistant powered by Google Gemini, ChromaDB, FastAPI and React.

DocMind AI is a production-grade Retrieval-Augmented Generation (RAG) application that enables users to upload documents and ask natural language questions. The system retrieves relevant document chunks using vector embeddings and generates grounded answers with source citations.

---

## 🚀 Live Demo

### Frontend
https://docmind-ai-phi.vercel.app/

### Backend API Docs
https://docmind-ai-backend-3ias.onrender.com/

---

## ✨ Features

- 📄 Upload PDF, TXT and Markdown documents
- 🔍 Semantic document search using vector embeddings
- 🤖 AI-powered question answering with Google Gemini
- 📚 Source-grounded responses with citations
- ⚡ FastAPI backend with REST APIs
- 🗄️ ChromaDB vector database integration
- 🎨 Modern React + TypeScript frontend
- ☁️ Deployed on Vercel and Render

---

## 🏗️ System Architecture

```text
User
  │
  ▼
React Frontend
  │
  ▼
FastAPI Backend
  │
  ├── Google Gemini
  │       │
  │       ▼
  │   Generate Answer
  │
  ▼
ChromaDB Vector Store
  │
  ▼
Document Embeddings
```

---

## 🛠️ Tech Stack

### Frontend

- React
- TypeScript
- Vite
- Tailwind CSS
- Framer Motion

### Backend

- FastAPI
- Python
- Google Gemini API
- ChromaDB
- LangChain

### Deployment

- Vercel
- Render

---

## 📂 Supported Document Types

| Format | Supported |
|----------|----------|
| PDF | ✅ |
| TXT | ✅ |
| Markdown | ✅ |

---

## 🔄 RAG Workflow

1. Upload a document
2. Extract and chunk content
3. Generate embeddings using Gemini
4. Store vectors in ChromaDB
5. User submits a query
6. Retrieve relevant chunks
7. Generate grounded response
8. Return answer with citations

---

## 📸 Key Capabilities

### Document Ingestion

- PDF parsing
- Text extraction
- Chunk generation
- Metadata tracking

### Semantic Retrieval

- Vector similarity search
- Context ranking
- Citation generation

### AI Responses

- Context-aware answers
- Grounded generation
- Hallucination reduction

---

## 📊 Project Highlights

- Production-ready RAG architecture
- Google Gemini Embeddings Integration
- FastAPI REST APIs
- Persistent ChromaDB Storage
- Source Citation Support
- Full Stack Deployment
- Enterprise-style UI

---

## 🔌 API Endpoints

### Health Check

```http
GET /api/health
```

### Upload Document

```http
POST /api/documents/upload
```

### List Documents

```http
GET /api/documents
```

### Delete Document

```http
DELETE /api/documents/{filename}
```

### Query Knowledge Base

```http
POST /api/chat/query
```

---

## 💼 Resume Worthy Skills Demonstrated

- Retrieval-Augmented Generation (RAG)
- Vector Databases
- Semantic Search
- LLM Integration
- FastAPI Development
- Full Stack Engineering
- Cloud Deployment
- REST API Design

---

## 👨‍💻 Author

Utkarsh Singh

B.Tech Computer Science

Built as part of AI and Enterprise Knowledge Management learning initiatives.

---

## ⭐ If you found this project interesting, consider giving it a star.

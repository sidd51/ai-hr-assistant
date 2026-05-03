# ⚓ HarborHR
### A safe port for all your HR needs

> An AI-powered HR assistant that lets employees query leave balances, understand company policies, and submit requests — all in plain English. Built with a LangChain agent that dynamically routes between a RAG policy engine and a live SQL database.

**[Live Demo](https://harborhr.vercel.app)** · **[Backend API Docs](https://harborhr-api.up.railway.app/docs)**

---

![HarborHR Screenshot](https://via.placeholder.com/900x500/080a0e/4ade9e?text=HarborHR+Screenshot)

---

## What it does

Most employees don't know where to find HR policies, and HR teams spend hours answering the same questions repeatedly. HarborHR fixes both sides of that problem.

An employee can open the app and ask:

- *"How many annual leave days do I have left?"* → queries the live database
- *"What is the maternity leave policy?"* → searches policy documents via RAG
- *"I want to apply for leave from March 10 to 14"* → submits a real request to the DB
- *"How do I claim expenses for a team lunch?"* → retrieves reimbursement rules

The agent decides which tool to use on its own. The employee just talks.

---

## Architecture

```
React (Vercel)
      │
      │  POST /chat
      ▼
FastAPI (Railway)
      │
      ▼
LangChain Agent  ──────────────────────────────────┐
      │                                             │
      │  routes dynamically to:                     │
      │                                             │
      ├──► RAG Tool                                 │
      │     └── LlamaIndex + ChromaDB               │
      │          └── HR policy documents            │
      │                                             │
      ├──► SQL Tool                                 │
      │     └── LangChain SQL chain                 │
      │          └── PostgreSQL (Neon)              │
      │               ├── employees                 │
      │               ├── leave_balance             │
      │               ├── leave_requests            │
      │               └── expense_claims            │
      │                                             │
      └──► Request Tool                             │
            └── SQLAlchemy ORM → PostgreSQL         │
                                                    │
LLM: Groq (llama-3.3-70b-versatile) ───────────────┘
Embeddings: HuggingFace (all-MiniLM-L6-v2)
```

---

## Tech stack

| Layer | Technology | Why |
|---|---|---|
| LLM | Groq `llama-3.3-70b` | Free, fast inference — near-instant responses |
| Agent framework | LangChain | Tool routing, prompt management, memory |
| RAG / document indexing | LlamaIndex | Chunks + indexes HR policy docs into ChromaDB |
| Vector store | ChromaDB | Persists embeddings for policy retrieval |
| Embeddings | HuggingFace `all-MiniLM-L6-v2` | Free, local, no API needed |
| Database | PostgreSQL (Neon) | Structured employee, leave and expense data |
| ORM | SQLAlchemy | Schema definition, migrations, session management |
| Backend | FastAPI | REST API with session management and CORS |
| Frontend | React + Vite | Chat UI with dark theme, CSS Modules |
| Deployment | Vercel + Railway | Frontend on Vercel, backend + DB on Railway/Neon |

---

## Key engineering decisions

**Why a LangChain agent instead of a simple chain?**
The core challenge is that a single employee question can require multiple data sources. "How many leave days do I have, and what's the policy if I need more?" needs both a SQL query and a RAG lookup. A chain would hard-code that flow. An agent decides dynamically — it reads the question, picks the right tool, and synthesizes the results.

**Why LlamaIndex for RAG instead of LangChain's built-in retriever?**
LlamaIndex has a significantly better document ingestion pipeline — better chunking strategies, cleaner metadata handling, and a simpler API for building persistent vector indexes. LangChain is used for what it's best at (agent orchestration), and LlamaIndex for what it's best at (document intelligence).

**Why Groq over OpenAI/Anthropic?**
Cost and speed. Groq's free tier runs `llama-3.3-70b` with near-zero latency. For a portfolio project that needs to be demo-able without burning API credits, it's the right call.

**Why SQLAlchemy over raw SQL or Prisma?**
LangChain's SQL tools are built on top of SQLAlchemy internally — using it directly gives full compatibility, clean ORM-style schema definitions, and easy migration support via Alembic. Prisma is Node.js-only and incompatible with a Python backend.

---

## Project structure

```
harborhr/
├── backend/
│   ├── main.py          # FastAPI app — 4 endpoints, session management
│   ├── agent.py         # LangChain agent + HRAssistant class with memory
│   ├── tools.py         # 4 agent tools: policy search, SQL query, leave submit, expense submit
│   ├── rag.py           # LlamaIndex pipeline — load, chunk, embed, persist, retrieve
│   ├── llm.py           # Groq LLM setup — centralised provider abstraction
│   ├── models.py        # SQLAlchemy ORM models — 4 tables with relationships
│   ├── database.py      # DB connection, session factory, schema reader
│   ├── seed_db.py       # One-time DB seeding script
│   ├── policies/        # HR policy text files indexed by LlamaIndex
│   │   ├── leave_policy.txt
│   │   ├── expense_policy.txt
│   │   └── code_of_conduct.txt
│   └── data/
│       └── chroma_store/  # Persisted ChromaDB vector index
└── frontend/
    └── src/
        ├── App.jsx        # Root — routes between Login and Chat
        ├── Login.jsx      # Employee profile selector
        ├── Chat.jsx       # Main chat interface with sidebar
        ├── Message.jsx    # Individual message bubble with loading state
        └── api.js         # All fetch calls to FastAPI
```

---

## Running locally

**Prerequisites:** Python 3.11+, Node 18+, Docker

```bash
# 1 — clone
git clone https://github.com/YOUR_USERNAME/harborhr.git
cd harborhr

# 2 — backend
python -m venv venv && source venv/bin/activate
cd backend
pip install -r requirements.txt

# 3 — environment
cp .env.example .env
# fill in GROQ_API_KEY and DATABASE_URL

# 4 — start PostgreSQL
docker run --name harborhr-postgres \
  -e POSTGRES_USER=hruser \
  -e POSTGRES_PASSWORD=hrpassword \
  -e POSTGRES_DB=hrdb \
  -p 5432:5432 -d postgres:15

# 5 — seed database + build RAG index
python seed_db.py
python rag.py

# 6 — start backend
uvicorn main:app --reload --port 8000

# 7 — frontend (new terminal)
cd ../frontend
npm install
npm run dev
```

Open `http://localhost:5173`

---

## API reference

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/health` | Health check + active session count |
| `POST` | `/chat` | Send a message, get agent response |
| `POST` | `/reset-session` | Clear conversation memory |
| `GET` | `/session/{id}/history` | Retrieve full chat history |

Full interactive docs at `/docs` (Swagger UI, auto-generated by FastAPI).

---

## What I learned building this

- **The difference between a chain and an agent** — chains are fixed pipelines, agents make decisions. Knowing when to use which is the most important architectural choice in LLM engineering.
- **Why RAG retrieval quality matters more than LLM quality** — garbage chunks in, garbage answers out. Chunk size, overlap, and embedding model choice affect answer quality more than which LLM you use.
- **LLM output is non-deterministic and you have to engineer around it** — the SQL tool bug I hit (LLM prepending explanation text before the SQL) taught me to always extract and validate LLM output rather than trusting it directly.
- **Session management is underrated** — giving each user their own `HRAssistant` instance with isolated memory is the difference between a toy demo and something usable.

---

## Deployment

| Service | Platform | Cost |
|---|---|---|
| React frontend | Vercel | Free |
| FastAPI backend | Railway | Free tier |
| PostgreSQL | Neon | Free serverless |
| Groq LLM | Groq Cloud | Free tier |
| Embeddings | HuggingFace | Free, runs locally on Railway |

---

## Roadmap

- [ ] Authentication — JWT-based login instead of profile selector
- [ ] HR admin dashboard — approve/reject leave requests
- [ ] PDF upload — let HR upload new policy docs via UI
- [ ] Email notifications — notify employees when requests are approved
- [ ] Streaming responses — stream agent output token by token

---

## Author

Built by **Siddhi Borawake** as a learning project exploring LLM engineering, RAG pipelines, and agentic AI systems.


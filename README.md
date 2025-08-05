# 🤖 AI Coding Assistant

An AI-powered coding assistant built with **FastAPI**, designed to run locally or on Render/Docker, with modular architecture, RAG memory, task orchestration, and developer tooling.  
This project will serve as the foundation for an **autonomous coding agent** that can:
- Generate and execute code
- Provide API endpoints
- Run background workers
- Store context and memory
- Scale with queues and persistence

 

🚀 Features 

### Core
- **FastAPI Backend**: High-performance Python API framework.
- **Auto-reload (Uvicorn)**: Instant development feedback.
- **Swagger & ReDoc**: Interactive API documentation.
- **Modular Structure**: Clean architecture with `api`, `core`, `services`.

### AI & Automation
- **RAG Memory**: FAISS/Chroma for vector-based memory retrieval.
- **Model Routing**: Supports OpenAI, Ollama, Claude (future-ready).
- **LangGraph/Flow Support**: Import and analyze Langflow-style JSON diagrams.
- **Task Orchestration**: Celery + Redis for async task execution.
- **Tooling Layer**: Add "tools" like code execution, shell commands, or API scrapers.
- **Environment Variables**: `.env` file support for config and API keys.

### Dev Experience
- **GitHub Copilot Ready**: Pre-documented structure for AI-assisted development.
- **Docker Support**: Local or containerized execution.
- **Script Runner**: CLI entry points for workers and API server.
- **Testing**: `pytest` integration (optional).

 📂 Project Structure
ai-coding-assistant/
│
├── app/
│ ├── init.py
│ ├── main.py # FastAPI entrypoint
│ ├── worker.py # Celery/Background worker
│ ├── api/ # API endpoints
│ │ ├── init.py
│ │ └── routes.py
│ ├── core/ # Core utilities (logging, config, memory)
│ │ ├── init.py
│ │ ├── config.py
│ │ └── memory.py
│ └── services/ # Business logic (agents, tools, integrations)
│ ├── init.py
│ └── agent.py
│
├── .env # Environment variables
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
├── README.md
└── tests/ # Unit tests
└── test_main.py


## 🛠 Tech Stack

| Component         | Usage                                      |
|-------------------|--------------------------------------------|
| FastAPI           | Backend API framework                      |
| Uvicorn           | ASGI server for FastAPI                    |
| FAISS/Chroma      | Vector DB for memory retrieval             |
| Celery + Redis    | Task queue and background processing       |
| LangGraph         | Agent orchestration (future integration)   |
| Python-dotenv     | Manage environment variables               |
| Docker            | Containerized deployment                   |

 

🔑 .env File Example 



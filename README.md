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
- **RAG Memory**: Simple keyword-based memory for conversation and code context storage.
- **Model Routing**: Supports OpenAI, with fallback to mock responses for development.
- **Task Orchestration**: Celery + Redis for async task execution.
- **Tooling Layer**: Code generation, review, and chat functionality.
- **Environment Variables**: `.env` file support for config and API keys.

### Dev Experience
- **GitHub Copilot Ready**: Pre-documented structure for AI-assisted development.
- **Docker Support**: Local or containerized execution.
- **Script Runner**: CLI entry points for workers and API server.
- **Testing**: `pytest` integration with comprehensive test suite.

 📂 Project Structure
```
ai-coding-assistant/
│
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI entrypoint
│   ├── worker.py              # Celery/Background worker
│   ├── api/                   # API endpoints
│   │   ├── __init__.py
│   │   └── routes.py
│   ├── core/                  # Core utilities (logging, config, memory)
│   │   ├── __init__.py
│   │   ├── config.py
│   │   └── memory.py
│   └── services/              # Business logic (agents, tools, integrations)
│       ├── __init__.py
│       └── agent.py
│
├── .env                       # Environment variables
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
├── README.md
└── tests/                     # Unit tests
    ├── __init__.py
    └── test_main.py
```


## 🛠 Tech Stack

| Component         | Usage                                      |
|-------------------|--------------------------------------------|
| FastAPI           | Backend API framework                      |
| Uvicorn           | ASGI server for FastAPI                    |
| Simple Memory     | Basic keyword-based memory (upgradeable)  |
| Celery + Redis    | Task queue and background processing       |
| Python-dotenv     | Manage environment variables               |
| Docker            | Containerized deployment                   |

 

🔑 .env File Example 

```bash
# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
DEBUG=true

# AI Model Configuration
OPENAI_API_KEY=your_openai_api_key_here
MODEL_NAME=gpt-3.5-turbo
MAX_TOKENS=2000

# Memory and Vector Database
MEMORY_TYPE=simple
VECTOR_DIMENSION=384
MAX_MEMORY_SIZE=1000

# Task Queue Configuration
REDIS_URL=redis://localhost:6379/0
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0

# Database Configuration
DATABASE_URL=sqlite:///./app.db

# Logging
LOG_LEVEL=INFO
LOG_FORMAT=json
```

## 🚀 Quick Start

### Local Development

1. **Clone and Setup**
   ```bash
   git clone <repository-url>
   cd ai-coding-assistant
   cp .env.example .env  # Edit with your API keys
   ```

2. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the API Server**
   ```bash
   python -m app.main
   # or
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

4. **Access the API**
   - API Documentation: http://localhost:8000/docs
   - Alternative Docs: http://localhost:8000/redoc
   - Health Check: http://localhost:8000/api/health

### Docker Deployment

1. **Build and Run with Docker Compose**
   ```bash
   docker-compose up --build
   ```

2. **Services Available**
   - API Server: http://localhost:8000
   - Flower (Celery Monitor): http://localhost:5555
   - Redis: localhost:6379

### API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Root information |
| `/api/health` | GET | Health check |
| `/api/generate-code` | POST | Generate code from prompt |
| `/api/chat` | POST | Chat with AI assistant |
| `/api/review-code` | POST | Review and analyze code |
| `/api/memory/stats` | GET | Memory statistics |
| `/api/memory/clear` | DELETE | Clear memory |
| `/api/memory/search` | GET | Search memory |

### Example Usage

**Generate Code:**
```bash
curl -X POST "http://localhost:8000/api/generate-code" \
     -H "Content-Type: application/json" \
     -d '{
       "prompt": "Create a Python function to calculate fibonacci numbers",
       "language": "python"
     }'
```

**Chat with Assistant:**
```bash
curl -X POST "http://localhost:8000/api/chat" \
     -H "Content-Type: application/json" \
     -d '{
       "message": "How do I optimize a Python function for performance?",
       "use_memory": true
     }'
```

## 🧪 Testing

Run the test suite:
```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=app --cov-report=html

# Run structure tests
python test_structure.py
```

## 🏗️ Development

### Adding New Features

1. **API Endpoints**: Add to `app/api/routes.py`
2. **Business Logic**: Add to `app/services/`
3. **Configuration**: Update `app/core/config.py`
4. **Tests**: Add to `tests/`

### Memory Backends

The system supports pluggable memory backends:
- **Simple**: Keyword-based matching (default)
- **FAISS**: Vector similarity search (requires `faiss-cpu`)
- **ChromaDB**: Vector database (requires `chromadb`)

To upgrade to advanced memory:
```bash
pip install faiss-cpu sentence-transformers
# or
pip install chromadb
```

Then update `MEMORY_TYPE` in your `.env` file.

### Background Tasks

Add new Celery tasks in `app/worker.py`:
```python
@celery_app.task
def my_background_task(param):
    # Your task logic here
    return result
```

## 🚢 Deployment

### Production Checklist

- [ ] Set production API keys in `.env`
- [ ] Configure Redis for production
- [ ] Set up proper logging
- [ ] Configure CORS settings
- [ ] Set up monitoring (Flower, logs)
- [ ] Configure SSL/HTTPS
- [ ] Set up backup for memory/database

### Environment Variables

See the `.env` file for all configuration options. Key variables for production:

- `OPENAI_API_KEY`: Your OpenAI API key
- `REDIS_URL`: Redis connection string
- `DEBUG`: Set to `false` in production
- `API_HOST`: Server host (0.0.0.0 for Docker)
- `LOG_LEVEL`: Set to `WARNING` or `ERROR` in production

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Run tests and ensure they pass
5. Submit a pull request

## 📄 License

This project is licensed under the terms specified in the LICENSE file.

## 🆘 Troubleshooting

**API not starting?**
- Check if port 8000 is available
- Verify Python dependencies are installed
- Check `.env` file configuration

**Memory not working?**
- Ensure Redis is running for Celery tasks
- Check memory backend configuration
- Verify sufficient memory available

**Tests failing?**
- Run `python test_structure.py` first
- Install test dependencies: `pip install pytest pytest-asyncio`
- Check if all required files exist

For more help, check the API documentation at `/docs` when the server is running.


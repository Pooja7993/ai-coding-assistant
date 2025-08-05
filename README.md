# 🤖 AI Coding Assistant

An **advanced AI-powered coding assistant** built with **FastAPI**, featuring multi-model routing, intelligent plugins, semantic memory, and comprehensive telemetry. Designed to run locally or in production with Docker, providing autonomous coding capabilities, real-time monitoring, and extensible architecture.

## 🚀 Key Features

### 🔥 Advanced AI Capabilities
- **Multi-Model Routing**: Automatically selects optimal models (OpenAI, Claude, Mistral, Ollama) based on cost and performance
- **Intelligent Fallbacks**: Seamless switching between providers when models fail
- **Semantic Memory**: FAISS + Redis hybrid memory for contextual code generation and chat
- **Auto-Model Selection**: Context-aware model selection for different task types

### 🛠 Developer Productivity
- **Plugin System**: Extensible architecture with built-in tools:
  - **Code Analyzer**: Quality assessment, complexity scoring, issue detection
  - **Test Generator**: Automatic unit test creation for functions
  - **Dependency Installer**: Auto-detection and installation of missing packages
- **Enhanced Code Generation**: Context-aware code generation with memory integration
- **Smart Chat Assistant**: Conversational AI with project context and memory

### 📊 Monitoring & Telemetry
- **Real-time Telemetry**: API usage tracking, model performance metrics, system health
- **Health Monitoring**: CPU, memory, error rates, response times
- **Model Analytics**: Usage statistics, token consumption, latency tracking
- **Comprehensive Logging**: Structured logging with configurable levels

### 🔌 API & Integration
- **RESTful API**: Comprehensive endpoints for all features
- **Streaming Support**: Real-time completions and responses
- **Tool Execution**: Dynamic tool discovery and execution
- **Memory Management**: Advanced search and context retrieval

## 📂 Project Structure

```
ai-coding-assistant/
│
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI app with telemetry integration
│   ├── worker.py              # Celery background worker
│   ├── api/                   # API endpoints
│   │   ├── __init__.py
│   │   └── routes.py          # Enhanced API routes
│   ├── core/                  # Core system components
│   │   ├── __init__.py
│   │   ├── config.py          # Multi-provider configuration
│   │   ├── memory.py          # Hybrid memory system (FAISS + Redis)
│   │   ├── model_router.py    # Multi-model routing and management
│   │   ├── plugins.py         # Plugin system and built-in tools
│   │   └── telemetry.py       # Telemetry and monitoring system
│   └── services/              # Business logic
│       ├── __init__.py
│       └── agent.py           # Enhanced AI agent with multi-model support
│
├── plugins/                   # Custom plugin directory
├── tests/                     # Comprehensive test suite
├── .env                       # Environment configuration
├── requirements.txt           # Enhanced dependencies
├── Dockerfile
├── docker-compose.yml
└── README.md
```

## 🛠 Tech Stack

| Component         | Usage                                      | Status |
|-------------------|--------------------------------------------|--------|
| **FastAPI**       | High-performance API framework             | ✅ Core |
| **Multi-Model Support** | OpenAI, Claude, Mistral, Ollama    | ✅ Advanced |
| **FAISS + Redis** | Hybrid semantic memory system            | ✅ Enhanced |
| **Plugin System** | Extensible tool architecture              | ✅ New |
| **Telemetry**     | Real-time monitoring and analytics        | ✅ New |
| **Celery + Redis** | Background task processing               | ✅ Core |
| **Docker**        | Containerized deployment                   | ✅ Core |

## 🔑 Environment Configuration

Create a `.env` file with your configuration:

```bash
# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
DEBUG=false

# AI Model Providers (configure one or more)
OPENAI_API_KEY=your_openai_api_key_here
ANTHROPIC_API_KEY=your_anthropic_api_key_here
MISTRAL_API_KEY=your_mistral_api_key_here
OLLAMA_URL=http://localhost:11434

# Model Selection Strategy
AUTO_MODEL_SELECTION=true
PREFERRED_PROVIDER=openai
MAX_COST_PER_TOKEN=0.03
MODEL_NAME=gpt-3.5-turbo
MAX_TOKENS=2000

# Memory Configuration (hybrid, faiss, or simple)
MEMORY_TYPE=hybrid
VECTOR_DIMENSION=384
MAX_MEMORY_SIZE=1000

# Redis Configuration (for hybrid memory and tasks)
REDIS_URL=redis://localhost:6379/0
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0

# Database
DATABASE_URL=sqlite:///./app.db

# Logging
LOG_LEVEL=INFO
LOG_FORMAT=json
```

## 🚀 Quick Start

### Option 1: Local Development

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

3. **Run the Enhanced API Server**
   ```bash
   python -m app.main
   ```

### Option 2: Docker Deployment

```bash
docker-compose up --build
```

### Services Available
- **API Server**: http://localhost:8000
- **Interactive Docs**: http://localhost:8000/docs
- **Alternative Docs**: http://localhost:8000/redoc
- **Flower (Celery Monitor)**: http://localhost:5555

## 📊 API Endpoints

### Core Features
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | System information and available endpoints |
| `/api/health` | GET | Health check |
| `/api/generate-code` | POST | Enhanced code generation with multi-model support |
| `/api/chat` | POST | Intelligent chat with memory and context |
| `/api/review-code` | POST | Code review and analysis |

### Memory Management
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/memory/stats` | GET | Memory system statistics |
| `/api/memory/clear` | DELETE | Clear all memory |
| `/api/memory/search` | GET | Search memory with semantic similarity |

### Multi-Model System  
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/models/info` | GET | Available models and provider status |
| `/api/models/generate` | POST | Generate with automatic model selection |
| `/api/models/stream` | POST | Stream completions in real-time |

### Plugin System
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/tools/list` | GET | List all available tools |
| `/api/tools/execute` | POST | Execute tools with parameters |
| `/api/tools/{tool_name}/schema` | GET | Get tool parameter schema |

### Telemetry & Monitoring
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/telemetry/stats` | GET | API usage statistics |
| `/api/telemetry/health` | GET | System health status |
| `/api/telemetry/models` | GET | Model usage analytics |
| `/api/telemetry/clear` | DELETE | Clear telemetry data |

## 💻 Usage Examples

### Enhanced Code Generation
```bash
curl -X POST "http://localhost:8000/api/generate-code" \
     -H "Content-Type: application/json" \
     -d '{
       "prompt": "Create a Python class for handling JWT tokens with validation",
       "language": "python"
     }'
```

### Intelligent Chat with Memory
```bash
curl -X POST "http://localhost:8000/api/chat" \
     -H "Content-Type: application/json" \
     -d '{
       "message": "How can I optimize the JWT class we just created?",
       "use_memory": true
     }'
```

### Tool Execution - Code Analysis
```bash
curl -X POST "http://localhost:8000/api/tools/execute" \
     -H "Content-Type: application/json" \
     -d '{
       "tool_name": "code_analyzer",
       "parameters": {
         "code": "def process_data(data):\n    return [x*2 for x in data]",
         "language": "python"
       }
     }'
```

### Test Generation
```bash
curl -X POST "http://localhost:8000/api/tools/execute" \
     -H "Content-Type: application/json" \
     -d '{
       "tool_name": "test_generator",
       "parameters": {
         "code": "def calculate_area(radius):\n    return 3.14 * radius ** 2",
         "framework": "pytest"
       }
     }'
```

### System Health Check
```bash
curl -X GET "http://localhost:8000/api/telemetry/health"
```

## 🔧 Advanced Configuration

### Multi-Model Routing

The system automatically selects the best model based on:
- **Task Type**: Different models excel at different tasks
- **Cost Constraints**: Stay within budget limits
- **Provider Availability**: Automatic failover to available models
- **Performance Metrics**: Historical latency and success rates

### Memory Backends

Choose your memory backend based on your needs:

- **Simple**: In-memory keyword matching (good for development)
- **FAISS**: Vector similarity search with semantic understanding
- **Hybrid**: FAISS + Redis for semantic search with fast state management

### Plugin Development

Create custom tools by extending the `BaseTool` class:

```python
from app.core.plugins import BaseTool, PluginMetadata, ToolResult

class MyCustomTool(BaseTool):
    @property
    def metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="my_tool",
            version="1.0.0",
            description="My custom tool",
            author="Your Name",
            category="custom"
        )
    
    async def execute(self, param1: str, param2: int = 10) -> ToolResult:
        # Your tool logic here
        return ToolResult(success=True, data={"result": "success"})
```

## 🧪 Testing

Run the comprehensive test suite:

```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=app --cov-report=html

# Run specific test categories
pytest tests/test_main.py::TestAIAgent -v
```

## 📊 Monitoring & Analytics

### Real-time Telemetry

Monitor your AI assistant's performance:
- **API Usage**: Track calls, response times, success rates
- **Model Performance**: Monitor token usage, latency, costs
- **System Health**: CPU, memory, error rates
- **Tool Usage**: Plugin execution statistics

### Health Dashboard

Access comprehensive system metrics:
```bash
# Get overall health status
curl http://localhost:8000/api/telemetry/health

# Get detailed API statistics
curl http://localhost:8000/api/telemetry/stats?hours=24

# Get model usage analytics
curl http://localhost:8000/api/telemetry/models
```

## 🚢 Production Deployment

### Docker Production Setup

1. **Configure Production Environment**
   ```bash
   # Set production variables
   export OPENAI_API_KEY=your_production_key
   export REDIS_URL=redis://your-redis-host:6379/0
   export DEBUG=false
   export LOG_LEVEL=WARNING
   ```

2. **Deploy with Docker Compose**
   ```bash
   docker-compose -f docker-compose.prod.yml up -d
   ```

### Production Checklist

- [ ] Configure production API keys for multiple providers
- [ ] Set up Redis cluster for production workloads
- [ ] Configure log aggregation (ELK, Datadog, etc.)
- [ ] Set up monitoring and alerting
- [ ] Configure SSL/HTTPS termination
- [ ] Set up backup strategy for memory/database
- [ ] Configure rate limiting and authentication
- [ ] Set up CI/CD pipeline for updates

## 🆕 What's New in This Version

### 🔥 Advanced AI Features
- **Multi-Model Support**: Route between OpenAI, Claude, Mistral, and Ollama
- **Intelligent Fallbacks**: Automatic model switching on failures
- **Cost Optimization**: Choose models based on cost constraints
- **Task-Specific Routing**: Optimize model selection for different use cases

### 🛠 Developer Experience
- **Plugin Architecture**: Extensible tool system with built-in utilities
- **Auto-Tool Discovery**: Runtime registration of new capabilities
- **Enhanced Memory**: Semantic search with FAISS and fast Redis state
- **Comprehensive APIs**: 20+ endpoints for all system features

### 📊 Monitoring & Operations
- **Real-time Telemetry**: Track everything from API calls to model performance
- **Health Monitoring**: System metrics, error rates, performance analytics
- **Production Ready**: Comprehensive logging, error handling, graceful degradation

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Add tests for new functionality
4. Ensure all tests pass (`pytest tests/ -v`)
5. Commit your changes (`git commit -m 'Add amazing feature'`)
6. Push to the branch (`git push origin feature/amazing-feature`)
7. Open a Pull Request

## 🆘 Troubleshooting

### Common Issues

**No models available?**
- Verify API keys are set in `.env`
- Check internet connectivity for downloading models
- Try setting `MEMORY_TYPE=simple` for offline operation

**Memory system not working?**
- Install sentence-transformers: `pip install sentence-transformers`
- Set up Redis for hybrid backend: `docker run -d -p 6379:6379 redis`
- Use `MEMORY_TYPE=simple` for basic operation

**Telemetry showing errors?**
- Check `/api/telemetry/health` for detailed diagnostics
- Review logs for specific error messages
- Ensure all dependencies are installed

**Performance issues?**
- Monitor `/api/telemetry/stats` for bottlenecks
- Consider using faster models for development
- Enable Redis caching for better performance

### Support

- Check the API documentation at `/docs` when the server is running
- Review telemetry endpoints for system diagnostics  
- Use the health check endpoint for quick status verification

For more help, examine the comprehensive telemetry dashboard and logs for detailed system insights.

## 📄 License

This project is licensed under the terms specified in the LICENSE file.

---

**Built with ❤️ for developers who want intelligent, extensible, and production-ready AI coding assistance.**


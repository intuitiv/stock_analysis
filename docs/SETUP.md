# Project Setup Guide

## Prerequisites

### System Requirements
- Python 3.9+
- PostgreSQL 13+
- Redis 6+
- Node.js 16+ (for frontend)

### Python Dependencies
```bash
# Core dependencies
python-poetry
asyncio
aiohttp
fastapi
uvicorn
sqlalchemy
alembic
pydantic
```

### Environment Setup

1. **Clone Repository**
```bash
git clone https://github.com/your-repo/naetra-project.git
cd naetra-project
```

2. **Create Virtual Environment**
```bash
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# or
.venv\Scripts\activate     # Windows
```

3. **Install Dependencies**
```bash
poetry install
```

4. **Database Setup**
```bash
# Create PostgreSQL database
createdb naetra_db

# Run migrations
alembic upgrade head
```

5. **Redis Setup**
```bash
# Install Redis (Ubuntu)
sudo apt-get install redis-server

# Start Redis
sudo service redis-server start

# Verify Redis
redis-cli ping  # Should return PONG
```

## Configuration

### 1. Environment Variables
Create a `.env` file in the project root:

```env
# Database
DATABASE_URL=postgresql://user:password@localhost:5432/naetra_db
REDIS_URL=redis://localhost:6379/0

# LLM Providers
OLLAMA_API_URL=http://localhost:11434
OPENAI_API_KEY=your-key-here
GEMINI_API_KEY=your-key-here

# Security
SECRET_KEY=your-secret-key
JWT_SECRET=your-jwt-secret

# Logging
LOG_LEVEL=INFO
LOG_FORMAT=json

# Services
MARKET_DATA_PROVIDER=yahoo_finance
ENABLE_REAL_TIME_DATA=true
```

### 2. Application Configuration
Create `config/app_config.yaml`:

```yaml
app:
  name: "NAETRA"
  version: "1.0.0"
  debug: false
  
chaetra:
  memory:
    short_term_ttl: 86400  # 24 hours
    validation_period: 7200 # 2 hours
    
  learning:
    confidence_threshold: 0.85
    minimum_validations: 3
    
  llm:
    default_provider: "ollama"
    temperature: 0.7
    max_tokens: 2048

naetra:
  market_data:
    providers:
      - name: yahoo_finance
        enabled: true
        config:
          api_key: ${YAHOO_FINANCE_API_KEY}
          
      - name: alpha_vantage
        enabled: false
        config:
          api_key: ${ALPHA_VANTAGE_API_KEY}
  
  analysis:
    technical:
      indicators:
        - type: "MA"
          periods: [20, 50, 200]
        - type: "RSI"
          period: 14
    
    patterns:
      recognition:
        confidence_threshold: 0.8
        minimum_samples: 5
    
  visualization:
    charts:
      default_type: "candlestick"
      timeframes: ["1D", "1W", "1M"]
      indicators: ["MA", "RSI", "MACD"]
```

## Project Structure

```
naetra-project/
├── app/
│   ├── chaetra/           # CHAETRA core
│   │   ├── brain.py
│   │   ├── memory.py
│   │   └── learning.py
│   │
│   ├── naetra/           # NAETRA application
│   │   ├── market.py
│   │   ├── analysis.py
│   │   └── portfolio.py
│   │
│   ├── core/             # Core components
│   │   ├── config.py
│   │   ├── database.py
│   │   └── logging.py
│   │
│   └── api/              # API endpoints
│       ├── routes/
│       └── controllers/
│
├── frontend/            # Frontend application
│   ├── src/
│   └── package.json
│
├── config/             # Configuration files
│   └── app_config.yaml
│
├── scripts/            # Utility scripts
│   ├── setup.sh
│   └── seed_data.py
│
├── tests/             # Test suite
│   ├── unit/
│   └── integration/
│
├── alembic/           # Database migrations
│   └── versions/
│
├── docs/             # Documentation
│   ├── README.md
│   └── API.md
│
├── poetry.lock       # Dependencies lock file
└── pyproject.toml    # Project configuration
```

## Development Setup

### 1. Backend Setup
```bash
# Install dependencies
poetry install

# Set up pre-commit hooks
pre-commit install

# Run migrations
alembic upgrade head

# Start development server
uvicorn app.main:app --reload
```

### 2. Frontend Setup
```bash
# Install dependencies
cd frontend
npm install

# Start development server
npm run dev
```

### 3. Local LLM Setup (Ollama)
```bash
# Install Ollama
curl https://ollama.ai/install.sh | sh

# Start Ollama service
ollama serve

# Pull required model
ollama pull llama2
```

## Running the Application

### 1. Development Mode
```bash
# Terminal 1: Backend
poetry shell
uvicorn app.main:app --reload

# Terminal 2: Frontend
cd frontend
npm run dev

# Terminal 3: Worker (if needed)
poetry shell
celery -A app.worker worker --loglevel=info
```

### 2. Production Mode
```bash
# Using Docker Compose
docker-compose up -d
```

## Testing

### 1. Unit Tests
```bash
# Run all tests
pytest

# Run specific test file
pytest tests/unit/test_chaetra.py

# Run with coverage
pytest --cov=app tests/
```

### 2. Integration Tests
```bash
# Run integration tests
pytest tests/integration/

# Run with specific mark
pytest -m "integration"
```

## Monitoring

### 1. Logging
Logs are written to:
- `logs/app.log` - Application logs
- `logs/access.log` - Access logs
- `logs/error.log` - Error logs

### 2. Metrics
Prometheus metrics available at:
- `http://localhost:8000/metrics`

### 3. Health Checks
Health check endpoints:
- `http://localhost:8000/health` - Basic health check
- `http://localhost:8000/health/live` - Liveness probe
- `http://localhost:8000/health/ready` - Readiness probe

## Troubleshooting

### Common Issues

1. **Database Connection Issues**
```bash
# Check database status
pg_isready -h localhost -p 5432

# Reset database
dropdb naetra_db
createdb naetra_db
alembic upgrade head
```

2. **Redis Connection Issues**
```bash
# Check Redis status
redis-cli ping

# Flush Redis cache
redis-cli flushall
```

3. **LLM Integration Issues**
```bash
# Check Ollama status
curl http://localhost:11434/api/tags

# Restart Ollama service
sudo systemctl restart ollama
```

### Debug Mode
Set `debug: true` in `config/app_config.yaml` for detailed logging.

## Maintenance

### 1. Database Maintenance
```bash
# Backup database
pg_dump naetra_db > backup.sql

# Restore database
psql naetra_db < backup.sql

# Run database optimizations
vacuum analyze;
```

### 2. Cache Maintenance
```bash
# Monitor Redis memory
redis-cli info memory

# Clear specific cache
redis-cli del "cache:patterns"
```

### 3. Log Rotation
```bash
# Configure logrotate
sudo nano /etc/logrotate.d/naetra

# Example configuration
/var/log/naetra/*.log {
    daily
    rotate 7
    compress
    delaycompress
    missingok
    notifempty
}
```

## Security

### 1. API Security
- Use HTTPS in production
- Implement rate limiting
- Set secure headers
- Use JWT authentication

### 2. Database Security
- Use strong passwords
- Limit database user permissions
- Enable SSL connections
- Regular security updates

### 3. Environment Security
- Secure environment variables
- Regular dependency updates
- Security audit logging
- Access control implementation

## Deployment

### 1. Docker Deployment
```bash
# Build images
docker-compose build

# Start services
docker-compose up -d

# Check logs
docker-compose logs -f

# Scale services
docker-compose up -d --scale worker=3
```

### 2. Kubernetes Deployment
```bash
# Apply configurations
kubectl apply -f k8s/

# Check status
kubectl get pods

# View logs
kubectl logs -f deployment/naetra
```

### 3. Manual Deployment
```bash
# Install production dependencies
poetry install --no-dev

# Run production server
gunicorn app.main:app --workers 4 --worker-class uvicorn.workers.UvicornWorker
```

## Additional Resources

1. **Documentation Links**
   - API Documentation: `/docs/api`
   - Architecture Overview: `/docs/architecture`
   - User Guide: `/docs/user-guide`

2. **Support Channels**
   - GitHub Issues
   - Support Email
   - Community Chat

3. **Contributing**
   - Contribution Guidelines
   - Code of Conduct
   - Development Process

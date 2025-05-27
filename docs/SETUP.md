# NAETRA Setup Guide

This guide explains how to set up the NAETRA application for development.

## Prerequisites

- Python 3.9 or higher
- PostgreSQL 13 or higher
- Redis 6 or higher
- Node.js 16 or higher
- Git

## Installation Steps

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/naetra.git
   cd naetra
   ```

2. Make the setup script executable:
   ```bash
   chmod +x scripts/setup.sh
   ```

3. Run the setup script:
   ```bash
   ./scripts/setup.sh
   ```

   This script will:
   - Create and activate a Python virtual environment
   - Install all required dependencies
   - Set up pre-commit hooks
   - Download required NLTK data
   - Initialize the database

4. Create and configure your environment file:
   ```bash
   cp .env.example .env
   ```
   Edit `.env` with your configuration settings.

## Required Dependencies

The application requires several Python packages, including:

### Core Dependencies
- FastAPI and related packages
- SQLAlchemy
- Redis (aioredis)
- JWT authentication
- Alembic for migrations

### Machine Learning Dependencies
- scikit-learn
- numpy
- pandas
- scipy
- statsmodels
- nltk
- textblob

### Market Data Integration
- yfinance
- alpha_vantage
- finnhub-python

## Development Setup

1. Activate the virtual environment:
   ```bash
   source venv/bin/activate
   ```

2. Start the development server:
   ```bash
   uvicorn app.main:app --reload
   ```

3. Set up frontend development:
   ```bash
   cd frontend
   npm install
   npm start
   ```

## Testing

Run tests using pytest:
```bash
pytest
```

Or use the test script:
```bash
./scripts/run_tests.sh
```

## Troubleshooting

If you encounter any issues:

1. Ensure all prerequisites are installed
2. Check your environment variables in `.env`
3. Check the logs in `logs/` directory
4. Make sure Redis and PostgreSQL services are running

For more detailed information, consult:
- [Architecture Documentation](ARCHITECTURE.md)
- [API Documentation](API.md)
- [Configuration Guide](CONFIGURATION.md)

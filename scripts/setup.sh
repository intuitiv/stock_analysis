#!/bin/bash

echo "Setting up NAETRA development environment..."

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Update pip
echo "Updating pip..."
pip install --upgrade pip

# Install core requirements
echo "Installing core dependencies..."
pip install -r requirements.txt

# Install test requirements
echo "Installing test dependencies..."
pip install -r requirements-test.txt

# Install pre-commit hooks if git is available
if command -v git >/dev/null 2>&1; then
    echo "Setting up pre-commit hooks..."
    pip install pre-commit
    pre-commit install
fi

# Download NLTK data
echo "Downloading NLTK data..."
python -c "import nltk; nltk.download('punkt'); nltk.download('averaged_perceptron_tagger'); nltk.download('vader_lexicon')"

# Initialize the database
echo "Initializing database..."
alembic upgrade head

echo "Setup complete! Activate the virtual environment with: source venv/bin/activate"

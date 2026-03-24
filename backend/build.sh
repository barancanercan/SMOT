#!/bin/bash
# Render Build Script for Meclis Istihbarat Sistemi

set -e

echo "Installing dependencies..."
pip install -r requirements-render.txt

echo "Creating data directory..."
mkdir -p ../data

echo "Initializing database..."
python -c "from app.core.database import init_database; init_database()"

echo "Build complete!"

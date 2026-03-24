#!/bin/bash
# Render Build Script for Meclis Istihbarat Sistemi

set -e

echo "Installing dependencies..."
pip install -r requirements-render.txt

echo "Creating data directory inside backend..."
mkdir -p ./data

echo "Copying database if exists..."
if [ -f "../data/meclis.db" ]; then
    cp ../data/meclis.db ./data/
    echo "Database copied to backend/data/"
fi

echo "Build complete!"

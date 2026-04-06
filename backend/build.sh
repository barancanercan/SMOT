#!/bin/bash
# Render Build Script for SMOT - Sosyal Medya Gozlem Araci

set -e

echo "Installing dependencies..."
pip install -r requirements-render.txt

echo "Creating data directory inside backend..."
mkdir -p ./data

echo "Copying database if exists..."
if [ -f "../data/smot.db" ]; then
    cp ../data/smot.db ./data/
    echo "Database copied to backend/data/"
fi

echo "Build complete!"

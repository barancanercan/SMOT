#!/bin/bash
# Render Build Script for SMOT - Sosyal Medya Gozlem Araci

set -e

echo "Installing dependencies..."
pip install -r requirements-render.txt

echo "Creating data directory inside backend..."
mkdir -p ./data

echo "Copying database..."
echo "Current dir: $(pwd)"
echo "Listing ../data/:"
ls -la ../data/ 2>&1 || echo "  ../data/ not found"
echo "Listing ./data/:"
ls -la ./data/ 2>&1 || echo "  ./data/ not found"

if [ -f "../data/smot.db" ]; then
    cp ../data/smot.db ./data/
    echo "Database copied from ../data/smot.db to ./data/"
    ls -la ./data/smot.db
else
    echo "WARNING: ../data/smot.db not found!"
    echo "Searching for any .db files:"
    find /opt/render/project/src -name "*.db" 2>/dev/null || true
fi

echo "Build complete!"

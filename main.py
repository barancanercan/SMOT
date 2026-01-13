#!/usr/bin/env python3
"""
Meclis İstihbarat Sistemi - Main Entry Point (Streamlit)
"""
import os
import sys
import streamlit as st

# Add src to python path to allow professional package imports
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
SRC_DIR = os.path.join(ROOT_DIR, "src")
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

# Import the actual UI logic
from meclis_istihbarat.ui.streamlit_app import main_ui

if __name__ == "__main__":
    main_ui()

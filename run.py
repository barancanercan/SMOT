#!/usr/bin/env python3
"""
Meclis İstihbarat Sistemi - Unified CLI Entry Point
"""
import os
import sys
import argparse

# Add src to python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

def run_scrape():
    # Import and run the scrape script logic
    from scripts import scrape
    scrape.main()

def run_ui():
    # Run streamlit
    import subprocess
    subprocess.run(["streamlit", "run", "main.py"])

def main():
    parser = argparse.ArgumentParser(description="Meclis İstihbarat Sistemi CLI")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Scrape command
    scrape_parser = subparsers.add_parser("scrape", help="Run the tweet scraper")
    scrape_parser.add_argument('--start', type=int, default=1, help='Starting index')
    scrape_parser.add_argument('--resume', action='store_true', help='Resume failed')

    # UI command
    subparsers.add_parser("ui", help="Launch the Streamlit UI")

    args = parser.parse_args()

    if args.command == "scrape":
        # Pass args to scrape script if needed, or just run it
        sys.argv = [sys.argv[0]]
        if args.start > 1:
            sys.argv.extend(["--start", str(args.start)])
        if args.resume:
            sys.argv.append("--resume")
        
        from scripts import scrape
        scrape.main()
    elif args.command == "ui":
        run_ui()
    else:
        parser.print_help()

if __name__ == "__main__":
    main()

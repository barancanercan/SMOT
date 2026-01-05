#!/usr/bin/env python3
"""
🏛️ Meclis İstihbarat Sistemi - UI Layer
Only Gradio interface, all logic in src/
"""

import gradio as gr
from models.database import init_database
from src.pipeline import scrape_and_analyze


# ============================================================================
# INITIALIZATION
# ============================================================================

def main():
    """Initialize database and launch UI"""
    print("🏛️ Meclis İstihbarat Sistemi")
    init_database()
    print("✅ Database ready")
    print("🌐 UI açılıyor: http://127.0.0.1:7860\n")

    # ========================================================================
    # GRADIO UI
    # ========================================================================

    with gr.Blocks(title="🏛️ Meclis İstihbarat") as demo:
        gr.Markdown("# 🏛️ Ankara Meclis İstihbarat Sistemi")
        gr.Markdown("*CSV → X Scraping → LLM Analysis → Report*")

        with gr.Column():
            # File upload
            csv_input = gr.File(
                label="📁 Meclis Üyeleri CSV'si",
                file_types=[".csv"],
                file_count="single"
            )

            # Process button
            process_btn = gr.Button(
                "🚀 BAŞLAT: Scrape & Analyze",
                variant="primary",
                size="lg"
            )

            # Report output
            report_output = gr.Markdown(label="📊 Rapor")

            # Event handler
            process_btn.click(scrape_and_analyze, csv_input, report_output)

    # Launch UI
    demo.launch(
        server_name="127.0.0.1",
        server_port=7860,
        show_error=True,
        share=False
    )


# ============================================================================
# RUN
# ============================================================================

if __name__ == "__main__":
    main()

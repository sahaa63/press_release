import gradio as gr
import os
import re
from databricks.sdk import WorkspaceClient

# ── Constants ─────────────────────────────────────────────────────────────────

SUPERVISOR_ENDPOINT = "mas-8821e19b-endpoint"

AVAILABLE_SHOWS = [
    "Sunday Football", "Crime Files", "Heartland Hospital", "The Baking Hour",
    "Quiz Champions", "Night Detectives", "Coast Guard Rescue", "Startup Stories",
    "Late Night Laughs", "Morning Brew", "Weekend Wrap", "Family Feud Live",
]

# ── Databricks client ─────────────────────────────────────────────────────────

def get_client() -> WorkspaceClient:
    return WorkspaceClient()

# ── Helper: Clean Agent Output ────────────────────────────────────────────────

def extract_final_press_release(raw_text: str) -> str:
    """
    Strips agent tags, tables, and knowledge base notes to return only the 
    actual press release starting from 'FOR IMMEDIATE RELEASE'.
    """
    # 1. Look for the last occurrence of 'FOR IMMEDIATE RELEASE'
    marker = "FOR IMMEDIATE RELEASE"
    if marker in raw_text:
        # Split and take the last part (the actual final draft)
        parts = raw_text.split(marker)
        final_draft = marker + parts[-1]
        
        # 2. Clean up any trailing agent names or footnotes if they exist
        final_draft = re.sub(r'<name>.*?</name>', '', final_draft)
        # Remove markdown footnotes like [^Vcny-1]
        final_draft = re.sub(r'\[\^.*?\]', '', final_draft)
        
        return final_draft.strip()
    
    return raw_text # Fallback if marker not found

# ── Core generation function ───────────────────────────────────────────────────

def generate_press_release(show_name: str) -> tuple[str, str]:
    if not show_name:
        return "", "Please select a show."

    try:
        w = get_client()
        payload = {
            "input": [
                {
                    "role": "user", 
                    "content": f"Generate a professional press release for '{show_name}'. Return ONLY the final press release text."
                }
            ]
        }

        endpoint_path = f"/serving-endpoints/{SUPERVISOR_ENDPOINT}/invocations"
        raw_response = w.api_client.do("POST", endpoint_path, body=payload)
        
        extracted_text = []
        if "output" in raw_response:
            for output_item in raw_response["output"]:
                if "content" in output_item:
                    for content_item in output_item["content"]:
                        text = content_item.get("text", "")
                        if text:
                            extracted_text.append(text)
        
        full_raw_output = " ".join(extracted_text)
        
        # Apply the cleaning logic to get ONLY the press release part
        clean_press_release = extract_final_press_release(full_raw_output)

        if not clean_press_release:
            clean_press_release = "Agent returned an empty response."

        return clean_press_release, "Generated successfully."

    except Exception as e:
        return "", f"Error: {str(e)}"

# ── UI Layout & Dynamic CSS ────────────────────────────────────────────────────

# Updated CSS to use standard Gradio Variables for Light/Dark mode compatibility
CSS = """
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@600;700&family=Source+Serif+4:wght@300;400&display=swap');

#masthead { 
    border-bottom: 2px solid var(--body-text-color); 
    padding-bottom: 12px; 
    margin-bottom: 24px; 
}
#masthead h1 { 
    font-family: 'Playfair Display', serif !important; 
    font-size: 2.2rem !important; 
    margin: 0 !important; 
}
#input-panel { 
    border: 1px solid var(--border-color-primary) !important; 
    border-radius: 8px !important; 
    padding: 20px !important; 
}
#output-body textarea { 
    font-family: 'Source Serif 4', serif !important; 
    font-size: 1.1rem !important; 
    line-height: 1.7 !important; 
    padding: 30px !important;
    border: none !important;
    background-color: var(--input-background-fill) !important;
    color: var(--body-text-color) !important;
}
/* Ensure status box and labels adapt to dark/light mode */
.gradio-container label span {
    font-weight: bold !important;
    text-transform: uppercase !important;
    letter-spacing: 0.05em !important;
}
"""

def build_ui() -> gr.Blocks:
    # Using 'Soft' theme as it handles dynamic Light/Dark switching very well
    with gr.Blocks(css=CSS, title="Press Release Generator", theme=gr.themes.Soft()) as app:
        gr.HTML("""
            <div id="masthead">
                <h1>Press Release Generator</h1>
                <p>Versant Innovation Pod &nbsp;·&nbsp; Powered by Databricks Multi-Agent Supervisor</p>
            </div>
        """)
        with gr.Row():
            with gr.Column(scale=1, elem_id="input-panel"):
                gr.Markdown("### Configuration")
                show_input = gr.Dropdown(choices=AVAILABLE_SHOWS, label="Select Show", value="Sunday Football")
                generate_btn = gr.Button("Generate Press Release", variant="primary", size="lg")
                status = gr.Textbox(label="System Status", interactive=False, lines=1)
                
                with gr.Accordion("System Details", open=False):
                    gr.Markdown("""
                    - **Engine:** Databricks Genie (SQL)
                    - **Styling:** Knowledge Assistant (RAG)
                    - **Inference:** Llama 3.3 70B
                    """)
            
            with gr.Column(scale=2, elem_id="output-body"):
                # Use a Markdown or Textbox. Textbox with lines=30 mimics the notebook feel.
                output = gr.Textbox(
                    label="Final Press Release Draft", 
                    lines=25, 
                    interactive=False, 
                    placeholder="The professional draft will appear here...", 
                    show_copy_button=True
                )

        generate_btn.click(
            fn=generate_press_release, 
            inputs=[show_input], 
            outputs=[output, status]
        )
        
    return app

if __name__ == "__main__":
    app = build_ui()
    app.launch(server_name="0.0.0.0", server_port=int(os.getenv("GRADIO_SERVER_PORT", 7860)))

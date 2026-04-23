import gradio as gr
import os
import re
import base64
from databricks.sdk import WorkspaceClient

# ── Constants ─────────────────────────────────────────────────────────────────
SUPERVISOR_ENDPOINT = "mas-8821e19b-endpoint"
AVAILABLE_SHOWS = [
    "Sunday Football", "Crime Files", "Heartland Hospital", "The Baking Hour",
    "Quiz Champions", "Night Detectives", "Coast Guard Rescue", "Startup Stories",
    "Late Night Laughs", "Morning Brew", "Weekend Wrap", "Family Feud Live",
]

# ── Image Handling ────────────────────────────────────────────────────────────
def get_base64_encoded_image(image_path):
    try:
        with open(image_path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode("utf-8")
    except Exception: return ""

logo_light_base64 = get_base64_encoded_image("VSNT_BIG.png")
logo_dark_base64 = get_base64_encoded_image("VSNT_BIG.D.png")

# ── Core Logic ────────────────────────────────────────────────────────────────

def extract_final_press_release(raw_text: str) -> str:
    """Strips agent tags and noise to return the clean press release text."""
    marker = "FOR IMMEDIATE RELEASE"
    if marker in raw_text:
        parts = raw_text.split(marker)
        final_draft = marker + parts[-1]
        final_draft = re.sub(r'<name>.*?</name>', '', final_draft)
        final_draft = re.sub(r'\[\^.*?\]', '', final_draft)
        return final_draft.strip()
    return raw_text

def generate_press_release(show_name: str) -> tuple[str, str]:
    if not show_name: return "", "Select a show."
    try:
        w = WorkspaceClient()
        # Pure show name input to allow the Supervisor's system prompt to work
        payload = {"input": [{"role": "user", "content": f"Generate a professional press release for '{show_name}'."}]}
        
        endpoint_path = f"/serving-endpoints/{SUPERVISOR_ENDPOINT}/invocations"
        raw_response = w.api_client.do("POST", endpoint_path, body=payload)
        
        extracted_text = []
        if "output" in raw_response:
            for output_item in raw_response["output"]:
                for content_item in output_item.get("content", []):
                    text = content_item.get("text", "")
                    if text: extracted_text.append(text)
        
        full_output = " ".join(extracted_text)
        clean_text = extract_final_press_release(full_output)
        return clean_text, "Generated successfully."
    except Exception as e:
        return "", f"Error: {str(e)}"

# ── UI Layout ──────────────────────────────────────────────────────────────────

CSS = """
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@700&family=Source+Serif+4:wght@400&display=swap');

#masthead { display: flex; align-items: center; border-bottom: 1px solid var(--border-color-primary); padding: 20px 0; margin-bottom: 24px; gap: 25px; }
#versant-logo { flex: 0 0 180px; }
#versant-logo img { width: 100%; height: auto; }

#logo-dark { display: none; }
@media (prefers-color-scheme: dark) { #logo-light { display: none; } #logo-dark { display: block; } }

#input-panel { 
    background: var(--block-background-fill); 
    border: 1px solid var(--border-color-primary); 
    border-radius: 8px; 
    padding: 16px; 
    min-height: 800px; 
}

#output-body textarea { 
    font-family: 'Source Serif 4', serif !important; 
    font-size: 1.1rem !important; 
    line-height: 1.7 !important; 
    padding: 30px !important;
}

.gradio-container label span { background: #6366f1 !important; color: white !important; border-radius: 4px; padding: 2px 8px; }
"""

def build_ui():
    with gr.Blocks(css=CSS, theme=gr.themes.Soft()) as app:
        # Build header manually to avoid f-string crashes
        header_html = '<div id="masthead"><div id="versant-logo">'
        header_html += '<img id="logo-light" src="data:image/png;base64,' + logo_light_base64 + '" />'
        header_html += '<img id="logo-dark" src="data:image/png;base64,' + logo_dark_base64 + '" /></div>'
        header_html += '<div id="masthead-text"><h1 style="margin:0; font-size: 2.2rem;">Press Release Generator</h1>'
        header_html += '<p style="margin:0; opacity:0.8;">Versant Innovation Pod &nbsp;·&nbsp; Databricks Supervisor</p></div></div>'
        gr.HTML(header_html)
        
        with gr.Row():
            with gr.Column(scale=1, elem_id="input-panel"):
                gr.Markdown("### Configuration")
                show_input = gr.Dropdown(choices=AVAILABLE_SHOWS, label="Select Show", value="Sunday Football")
                generate_btn = gr.Button("Generate Press Release", variant="primary")
                status = gr.Textbox(label="Status", interactive=False)
                
                with gr.Accordion("System Details", open=False):
                    gr.Markdown("""
                    **Technical Stack:**
                    * **Data Layer:** Synthetic TV performance stored in Delta tables 
                    * **Processing:** Supervisor routes to Genie Space for live metrics 
                    * **Style:** Grounded via Knowledge Assistant (RAG) 
                    * **Serving:** Databricks Apps (Gradio)
                    """)
            
            with gr.Column(scale=2, elem_id="output-body"):
                output = gr.Textbox(
                    label="Final Press Release Draft", 
                    lines=30, 
                    interactive=False, 
                    show_copy_button=True
                )

        generate_btn.click(fn=generate_press_release, inputs=[show_input], outputs=[output, status])
    return app

if __name__ == "__main__":
    app = build_ui()
    app.launch(server_name="0.0.0.0", server_port=int(os.getenv("GRADIO_SERVER_PORT", 7860)))

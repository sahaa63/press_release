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

# ── Image Handling (Base64 for Stability) ─────────────────────────────────────
def get_base64_encoded_image(image_path):
    try:
        with open(image_path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode('utf-8')
    except Exception:
        return ""

logo_light_base64 = get_base64_encoded_image("VSNT_BIG.png")
logo_dark_base64 = get_base64_encoded_image("VSNT_BIG.D.png")

# ── Core Logic ────────────────────────────────────────────────────────────────
def extract_final_press_release(raw_text: str) -> str:
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
        payload = {"input": [{"role": "user", "content": f"Generate a professional press release for '{show_name}'. Return ONLY the final press release text."}]}
        endpoint_path = f"/serving-endpoints/{SUPERVISOR_ENDPOINT}/invocations"
        raw_response = w.api_client.do("POST", endpoint_path, body=payload)
        
        extracted_text = []
        if "output" in raw_response:
            for output_item in raw_response["output"]:
                for content_item in output_item.get("content", []):
                    text = content_item.get("text", "")
                    if text: extracted_text.append(text)
        
        clean_text = extract_final_press_release(" ".join(extracted_text))
        return clean_text, "Generated successfully."
    except Exception as e:
        return "", f"Error: {str(e)}"

# ── CSS (Restoring Previous Look + Logo Fix) ──────────────────────────────────
CSS = """
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@700&family=Source+Serif+4:wght@400&display=swap');

#masthead { 
    display: flex; 
    align-items: center; 
    justify-content: center;
    border-bottom: 1px solid var(--border-color-primary); 
    padding: 20px 0; 
    margin-bottom: 24px;
}

#versant-logo { 
    flex: 0 0 180px; 
    margin-right: 20px;
}
#versant-logo img { width: 100%; height: auto; }

/* Dynamic Theme Switching */
#logo-dark { display: none; }
@media (prefers-color-scheme: dark) {
    #logo-light { display: none; }
    #logo-dark { display: block; }
}

#masthead-text { flex: none; text-align:center;}
#masthead-text h1 { 
    font-family: 'Playfair Display', serif !important; 
    font-size: 2.2rem !important; 
    margin: 0 !important; 
}

#input-panel { 
    background: var(--block-background-fill);
    border: 1px solid var(--border-color-primary) !important; 
    border-radius: 8px !important; 
    padding: 16px !important; 
}

#output-body textarea { 
    font-family: 'Source Serif 4', serif !important; 
    font-size: 1.1rem !important; 
    line-height: 1.7 !important; 
    padding: 30px !important;
}

/* Purple Label Accents */
.gradio-container label span {
    background: #6366f1 !important;
    color: white !important;
    border-radius: 4px;
    padding: 2px 8px;
    font-weight: bold !important;
}
"""

def build_ui() -> gr.Blocks:
    with gr.Blocks(css=CSS, theme=gr.themes.Soft()) as app:
        # Top Header with Logo on Left
        gr.HTML(f"""
            <div id="masthead">
                <div id="versant-logo">
                    <img id="logo-light" src="data:image/png;base64,{logo_light_base64}" />
                    <img id="logo-dark" src="data:image/png;base64,{logo_dark_base64}" />
                </div>
                <div id="masthead-text">
                    <h1>Press Release Generator</h1>
                    <p>Versant Innovation Pod &nbsp;·&nbsp; Databricks Multi-Agent Supervisor</p>
                </div>
            </div>
        """)
        
        with gr.Row():
            with gr.Column(scale=1, elem_id="input-panel"):
                gr.Markdown("### Configuration")
                show_input = gr.Dropdown(choices=AVAILABLE_SHOWS, label="Select Show", value="Sunday Football")
                generate_btn = gr.Button("Generate Press Release", variant="primary")
                
                status = gr.Textbox(label="System Status", interactive=False, placeholder="Waiting for input...")
                
                with gr.Accordion("System Details", open=False):
                    gr.Markdown("""
                    1. Fetches data via Genie
                    2. Style via Knowledge Asst
                    3. Model: Llama 3.3 70B
                    """)
            
            with gr.Column(scale=2, elem_id="output-body"):
                output = gr.Textbox(
                    label="Final Press Release Draft", 
                    lines=25, 
                    interactive=False, 
                    show_copy_button=True,
                    placeholder="The professional draft will appear here..."
                )

        generate_btn.click(fn=generate_press_release, inputs=[show_input], outputs=[output, status])
    return app

if __name__ == "__main__":
    app = build_ui()
    app.launch(server_name="0.0.0.0", server_port=int(os.getenv("GRADIO_SERVER_PORT", 7860)))

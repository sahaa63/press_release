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
            return base64.b64encode(img_file.read()).decode('utf-8')
    except Exception: return ""

logo_light_base64 = get_base64_encoded_image("VSNT_BIG.png")
logo_dark_base64 = get_base64_encoded_image("VSNT_BIG.D.png")

# ── Core Logic & Formatting ───────────────────────────────────────────────────

def format_as_press_release(raw_text: str, show_name: str) -> str:
    # Clean the agent noise
    marker = "FOR IMMEDIATE RELEASE"
    content = raw_text
    if marker in raw_text:
        content = marker + raw_text.split(marker)[-1]
    
    content = re.sub(r'<name>.*?</name>', '', content)
    content = re.sub(r'\[\^.*?\]', '', content)
    
    # Convert newlines to HTML breaks
    formatted_content = content.replace("\n", "<br>")

    return f"""
    <div class="pr-container">
        <div class="pr-header">
            <div class="pr-title">PRESS RELEASE</div>
            <div class="pr-subtitle">{show_name} | FOX | Week 20</div>
        </div>
        <div class="pr-content">
            {formatted_content}
        </div>
    </div>
    """

def generate_press_release(show_name: str) -> tuple[str, str]:
    if not show_name: return "", "Select a show."
    try:
        w = WorkspaceClient()
        # FIXED: Corrected f-string dictionary syntax
        payload = {
            "input": [
                {
                    "role": "user", 
                    "content": f"Generate a professional press release for '{show_name}'."
                }
            ]
        }
        
        endpoint_path = f"/serving-endpoints/{SUPERVISOR_ENDPOINT}/invocations"
        raw_response = w.api_client.do("POST", endpoint_path, body=payload)
        
        extracted_text = []
        if "output" in raw_response:
            for output_item in raw_response["output"]:
                for content_item in output_item.get("content", []):
                    text = content_item.get("text", "")
                    if text: extracted_text.append(text)
        
        raw_output = " ".join(extracted_text)
        return format_as_press_release(raw_output, show_name), "Generated successfully."
    except Exception as e:
        # FIXED: Corrected error reporting
        return "", f"Error: {str(e)}"

# ── CSS ───────────────────────────────────────────────────────────────────────
CSS = """
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@700&family=Source+Serif+4:wght@400&display=swap');

#masthead { display: flex; align-items: center; border-bottom: 1px solid var(--border-color-primary); padding: 20px 0; margin-bottom: 24px; gap: 25px; }
#versant-logo { flex: 0 0 180px; }
#versant-logo img { width: 100%; height: auto; }

#logo-dark { display: none; }
@media (prefers-color-scheme: dark) { #logo-light { display: none; } #logo-dark { display: block; } }

#input-panel { background: var(--block-background-fill); border: 1px solid var(--border-color-primary); border-radius: 8px; padding: 16px; }

.pr-container { background: transparent; padding: 10px; width: 100%; }
.pr-header { background: #e9e9e1; color: #1a1a1a; padding: 25px 35px; border-radius: 12px 12px 0 0; border-bottom: 1px solid #d1d1ca; }
.pr-title { font-family: 'Playfair Display', serif; font-size: 28px; font-weight: 800; letter-spacing: 1px; }
.pr-subtitle { font-family: 'Source Serif 4', serif; font-size: 16px; opacity: 0.7; margin-top: 5px; }
.pr-content { background: rgba(255,255,255,0.05); padding: 40px 35px; font-family: 'Source Serif 4', serif; font-size: 1.1rem; line-height: 1.8; color: var(--body-text-color); border-radius: 0 0 12px 12px; }

.gradio-container label span { background: #6366f1 !important; color: white !important; border-radius: 4px; padding: 2px 8px; }
"""

def build_ui() -> gr.Blocks:
    with gr.Blocks(css=CSS, theme=gr.themes.Soft()) as app:
        gr.HTML(f"""
            <div id="masthead">
                <div id="versant-logo">
                    <img id="logo-light" src="data:image/png;base64,{logo_light_base64}" />
                    <img id="logo-dark" src="data:image/png;base64,{logo_dark_base64}" />
                </div>
                <div id="masthead-text"><h1>Press Release Generator</h1><p>Versant Innovation Pod &nbsp;·&nbsp; Databricks Supervisor</p></div>
            </div>
        """)
        
        with gr.Row():
            with gr.Column(scale=1, elem_id="input-panel"):
                gr.Markdown("### Configuration")
                show_input = gr.Dropdown(choices=AVAILABLE_SHOWS, label="Select Show", value="Sunday Football")
                generate_btn = gr.Button("Generate Press Release", variant="primary")
                status = gr.Textbox(label="Status", interactive=False)
                with gr.Accordion("Details", open=False):
                    gr.Markdown("1. Genie 2. Knowledge Asst 3. Llama 3.3")
            
            with gr.Column(scale=2):
                output = gr.HTML(label="Final Press Release Draft")

        generate_btn.click(fn=generate_press_release, inputs=[show_input], outputs=[output, status])
    return app

if __name__ == "__main__":
    app = build_ui()
    app.launch(server_name="0.0.0.0", server_port=int(os.getenv("GRADIO_SERVER_PORT", 7860)))

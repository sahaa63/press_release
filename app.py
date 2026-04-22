"""
Press Release Generator — Databricks App
Final Optimized Version for Multi-Agent Supervisor
"""

import gradio as gr
import os
import json
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

# ── Helper to find text in the Supervisor's complex response ──────────────────

def extract_content(data):
    """Recursively searches for the actual text in the agent's response."""
    if isinstance(data, str):
        return data
    
    if isinstance(data, dict):
        # Priority 1: Agent Bricks 'output' field
        if "output" in data: return extract_content(data["output"])
        # Priority 2: OpenAI-style 'content'
        if "content" in data: return data["content"]
        # Priority 3: Standard Model Serving 'predictions'
        if "predictions" in data and data["predictions"]: 
            return extract_content(data["predictions"][0])
        # Priority 4: Chat 'choices'
        if "choices" in data and data["choices"]:
            return extract_content(data["choices"][0])
        if "message" in data:
            return extract_content(data["message"])
            
        # If it's a dict but no keys match, return the first value that's a string/dict
        for val in data.values():
            res = extract_content(val)
            if res: return res
            
    if isinstance(data, list) and len(data) > 0:
        return extract_content(data[0])
        
    return None

# ── Core generation function ───────────────────────────────────────────────────

def generate_press_release(show_name: str) -> tuple[str, str]:
    if not show_name:
        return "", "Please select a show."

    try:
        w = get_client()
        
        # This payload structure satisfies the 'input field is required' error
        payload = {
            "input": [
                {"role": "user", "content": f"Generate a professional press release for '{show_name}'."}
            ]
        }

        # Use extra_params to ensure the 'input' key is at the top level of the POST body
        # This bypasses the SDK's default behavior of wrapping inputs for batching.
        response = w.serving_endpoints.query(
            name=SUPERVISOR_ENDPOINT,
            extra_params=payload
        )

        # Convert the object to a dictionary so we can parse it
        res_dict = response.as_dict()
        
        # Deep-crawl the response to find the generated text
        press_release = extract_content(res_dict)

        if not press_release:
            # Fallback: if we can't find text, show the raw JSON for debugging
            press_release = f"Could not find text in response. Raw data:\n{json.dumps(res_dict, indent=2)}"

        return press_release, "Generated successfully."

    except Exception as e:
        print(f"DEBUG: {str(e)}")
        return "", f"Error: {str(e)}"

# ── UI Layout ──────────────────────────────────────────────────────────────────

CSS = """
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@600;700&family=Source+Serif+4:wght@300;400&display=swap');
:root {
    --ink: #1a1a1a; --ink-muted: #666666; --rule: #d0c9bf; --bg: #faf8f5;
    --bg-card: #ffffff; --accent: #1a1a2e; --font-head: 'Playfair Display', Georgia, serif;
    --font-body: 'Source Serif 4', Georgia, serif;
}
body, .gradio-container { background: var(--bg) !important; font-family: var(--font-body) !important; color: var(--ink) !important; }
#masthead { border-bottom: 2px solid var(--ink); padding-bottom: 12px; margin-bottom: 8px; }
#masthead h1 { font-family: var(--font-head) !important; font-size: 2rem !important; color: var(--ink) !important; margin: 0 !important; }
#input-panel { background: var(--bg-card) !important; border: 1px solid var(--rule) !important; padding: 20px !important; }
#generate-btn { background: var(--accent) !important; color: #ffffff !important; padding: 12px 24px !important; width: 100% !important; margin-top: 8px !important; }
#output-body textarea { font-family: var(--font-body) !important; font-size: 0.95rem !important; line-height: 1.9 !important; padding: 24px !important; }
"""

def build_ui() -> gr.Blocks:
    with gr.Blocks(css=CSS, title="Press Release Generator") as app:
        gr.HTML("""
            <div id="masthead">
                <h1>Press Release Generator</h1>
                <p>Versant Innovation Pod &nbsp;·&nbsp; Powered by Databricks Multi-Agent Supervisor</p>
            </div>
        """)
        with gr.Row():
            with gr.Column(scale=1, elem_id="input-panel"):
                gr.Markdown("### Generate")
                show_input = gr.Dropdown(choices=AVAILABLE_SHOWS, label="Select Show", value="Sunday Football")
                generate_btn = gr.Button("Generate Press Release", elem_id="generate-btn", variant="primary")
                status = gr.Textbox(label="Status", interactive=False, lines=1)
                gr.Markdown("---\n**System Architecture**\n1. Genie Space (Live Data)\n2. Knowledge Asst (Style)\n3. Orchestrator (Llama 3.3)")
            with gr.Column(scale=2, elem_id="output-body"):
                output = gr.Textbox(label="Press Release", lines=28, interactive=False, placeholder="Press Release will appear here...", show_copy_button=True)

        generate_btn.click(fn=generate_press_release, inputs=[show_input], outputs=[output, status])
    return app

if __name__ == "__main__":
    app = build_ui()
    app.launch(server_name="0.0.0.0", server_port=int(os.getenv("GRADIO_SERVER_PORT", 7860)))

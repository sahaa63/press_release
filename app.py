"""
Press Release Generator — Databricks App
Final Version: Specifically tuned for AgentBricks 'Responses' API.
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

# ── Core generation function ───────────────────────────────────────────────────

def generate_press_release(show_name: str) -> tuple[str, str]:
    if not show_name:
        return "", "Please select a show."

    try:
        w = get_client()
        
        # The API guide confirms the endpoint expects this exact structure:
        # A root 'input' key with a list of message objects.
        payload = {
            "input": [
                {
                    "role": "user", 
                    "content": f"Generate a professional press release for '{show_name}'."
                }
            ]
        }

        # Path for AgentBricks 'responses' API
        # This matches the 'https://.../serving-endpoints' base_url from your guide
        endpoint_path = f"/serving-endpoints/{SUPERVISOR_ENDPOINT}/invocations"

        # We use the authenticated api_client.do to send the raw POST.
        # This bypasses the SDK's internal schema mapping and uses the exact payload.
        raw_response = w.api_client.do("POST", endpoint_path, body=payload)
        
        # PARSING LOGIC: Based on your print() example:
        # response.output -> list of outputs
        # output.content -> list of content objects (usually has .text)
        
        extracted_text = []
        if "output" in raw_response:
            for output_item in raw_response["output"]:
                if "content" in output_item:
                    for content_item in output_item["content"]:
                        # Pull 'text' field if available
                        text = content_item.get("text", "")
                        if text:
                            extracted_text.append(text)
        
        press_release = " ".join(extracted_text)

        if not press_release:
            # Fallback in case of an unusual structure
            press_release = "Agent returned an empty response. Please check endpoint logs."

        return press_release, "Generated successfully."

    except Exception as e:
        # This will catch and display the 'input field is required' if the structure fails
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
#input-panel { background: var(--bg-card) !important; border: 1px solid var(--rule) !important; border-radius: 2px !important; padding: 20px !important; }
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
                gr.Markdown("---\n**System Details**\n1. Fetches data via Genie\n2. Style via Knowledge Asst\n3. Model: Llama 3.3 70B")
            with gr.Column(scale=2, elem_id="output-body"):
                output = gr.Textbox(label="Press Release", lines=28, interactive=False, placeholder="Your press release will appear here...", show_copy_button=True)

        generate_btn.click(fn=generate_press_release, inputs=[show_input], outputs=[output, status])
    return app

if __name__ == "__main__":
    app = build_ui()
    app.launch(server_name="0.0.0.0", server_port=int(os.getenv("GRADIO_SERVER_PORT", 7860)))

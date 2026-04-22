"""
Press Release Generator — Databricks App
Calls the press-release-supervisor endpoint and renders output.

Architecture:
- UI: Gradio (hosted on Databricks Apps)
- Backend: Databricks SDK → Supervisor Agent endpoint
- Auth: Workspace-native (no API key needed)
"""

import gradio as gr
import os
from databricks.sdk import WorkspaceClient
#from databricks.sdk.service.serving import ChatMessage, ChatMessageRole

# ── Constants ─────────────────────────────────────────────────────────────────

SUPERVISOR_ENDPOINT = "mas-8821e19b-endpoint"

AVAILABLE_SHOWS = [
    "Sunday Football",
    "Crime Files",
    "Heartland Hospital",
    "The Baking Hour",
    "Quiz Champions",
    "Night Detectives",
    "Coast Guard Rescue",
    "Startup Stories",
    "Late Night Laughs",
    "Morning Brew",
    "Weekend Wrap",
    "Family Feud Live",
]

# ── Databricks client (uses workspace credentials automatically) ───────────────

def get_client() -> WorkspaceClient:
    return WorkspaceClient()


# ── Core generation function ───────────────────────────────────────────────────

def generate_press_release(show_name: str) -> tuple[str, str]:
    if not show_name:
        return "", "Please select a show."

    try:
        import os
        from openai import OpenAI

        token = (
            os.environ.get("DATABRICKS_TOKEN") or
            os.environ.get("DATABRICKS_RUNTIME_TOKEN") or  
            os.environ.get("DATABRICKS_AAD_TOKEN")
        )
        
        client = OpenAI(
            api_key=token,
            base_url="https://dbc-840651e6-3fc0.cloud.databricks.com/serving-endpoints"
        )

        press_release = " ".join(
            getattr(content, "text", "")
            for output in response.output
            for content in getattr(output, "content", [])
        )

        return press_release, "Generated successfully."

    except Exception as e:
        return "", f"Error: {str(e)}"


# ── UI Layout ──────────────────────────────────────────────────────────────────

CSS = """
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@600;700&family=Source+Serif+4:wght@300;400&display=swap');

:root {
    --ink:        #1a1a1a;
    --ink-muted:  #666666;
    --rule:       #d0c9bf;
    --bg:         #faf8f5;
    --bg-card:    #ffffff;
    --accent:     #1a1a2e;
    --font-head:  'Playfair Display', Georgia, serif;
    --font-body:  'Source Serif 4', Georgia, serif;
}

@media (prefers-color-scheme: dark) {
    :root {
        --ink:     #e8e4df;
        --ink-muted: #999999;
        --rule:    #333333;
        --bg:      #1a1a1a;
        --bg-card: #242424;
        --accent:  #e8e4df;
    }
    #generate-btn {
        background: #e8e4df !important;
        color: #1a1a1a !important;
    }
    #masthead h1 {
        color: #e8e4df !important;
    }
}

body, .gradio-container {
    background: var(--bg) !important;
    font-family: var(--font-body) !important;
    color: var(--ink) !important;
}

#masthead {
    border-bottom: 2px solid var(--ink);
    padding-bottom: 12px;
    margin-bottom: 8px;
}

#masthead h1 {
    font-family: var(--font-head) !important;
    font-size: 2rem !important;
    font-weight: 700 !important;
    color: var(--ink) !important;
    margin: 0 !important;
}

#masthead p {
    font-size: 0.8rem !important;
    color: var(--ink-muted) !important;
    letter-spacing: 2px !important;
    text-transform: uppercase !important;
    margin: 4px 0 0 !important;
}

#input-panel {
    background: var(--bg-card) !important;
    border: 1px solid var(--rule) !important;
    border-radius: 2px !important;
    padding: 20px !important;
}

#generate-btn {
    background: var(--accent) !important;
    color: #ffffff !important;
    border: none !important;
    border-radius: 2px !important;
    font-family: var(--font-body) !important;
    font-size: 0.85rem !important;
    letter-spacing: 1.5px !important;
    text-transform: uppercase !important;
    padding: 12px 24px !important;
    width: 100% !important;
    margin-top: 8px !important;
}

#generate-btn:hover {
    background: #2d2d4a !important;
}

#output-body textarea {
    font-family: var(--font-body) !important;
    font-size: 0.95rem !important;
    line-height: 1.9 !important;
    color: var(--ink) !important;
    background: var(--bg-card) !important;
    border: 1px solid var(--rule) !important;
    padding: 24px !important;
}

label {
    font-family: var(--font-body) !important;
    font-size: 0.8rem !important;
    letter-spacing: 1px !important;
    text-transform: uppercase !important;
    color: var(--ink-muted) !important;
}
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

            # Input panel
            with gr.Column(scale=1, elem_id="input-panel"):
                gr.Markdown("### Generate")

                show_input = gr.Dropdown(
                    choices=AVAILABLE_SHOWS,
                    label="Select Show",
                    value="Sunday Football",
                    interactive=True,
                )

                generate_btn = gr.Button(
                    "Generate Press Release",
                    elem_id="generate-btn",
                    variant="primary",
                )

                status = gr.Textbox(
                    label="Status",
                    interactive=False,
                    lines=1,
                )

                gr.Markdown("""
                    ---
                    **How it works**

                    1. Supervisor fetches live performance data via Genie Space
                    2. Knowledge Assistant retrieves historical style context
                    3. Llama 3.3 70B generates the press release
                    4. Output rendered here
                """)

            # Output panel
            with gr.Column(scale=2, elem_id="output-body"):
                output = gr.Textbox(
                    label="Press Release",
                    lines=28,
                    interactive=False,
                    placeholder="Your press release will appear here...",
                    show_copy_button=True,
                )

        # Event
        generate_btn.click(
            fn=generate_press_release,
            inputs=[show_input],
            outputs=[output, status],
        )

    return app


# ── Entry point ────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    app = build_ui()
    app.launch(
        server_name="0.0.0.0",
        server_port=int(os.getenv("GRADIO_SERVER_PORT", 7860)),
        show_error=True,
    )

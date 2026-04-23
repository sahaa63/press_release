"""
Versant Press Release Generator
Version 3.0: Fixed permissions, added dynamic Light/Dark mode Versant logos.
"""

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
        
        # NOTE: Your endpoint now must handle the On-Behalf-Of authentication.
        # Ensure your Databricks App config is set to use OBO.
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
        clean_press_release = extract_final_press_release(full_raw_output)

        if not clean_press_release:
            clean_press_release = "Agent returned an empty response."

        return clean_press_release, "Generated successfully."

    except Exception as e:
        return "", f"Error: {str(e)}"

# ── Advanced Dynamic CSS with Media Queries ────────────────────────────────────

CSS = """
/* Import Fonts */
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@600;700&family=Source+Serif+4:wght@300;400&display=swap');

/* Main Container Flex Layout */
#masthead { 
    display: flex;
    align-items: center;
    border-bottom: 2px solid var(--body-text-color); 
    padding-bottom: 20px; 
    margin-bottom: 24px; 
}

/* 1. Dynamic Logo Area */
#versant-logo {
    flex: 0 0 150px; /* Fixed width of 150px, no growing */
    margin-right: 30px;
}

#versant-logo img {
    max-width: 100%;
    height: auto;
    border-radius: 8px; /* Suitable background effect */
    transition: opacity 0.3s ease;
}

/* THE LOGO SWITCHING MAGIC */
#logo-dark { 
    display: none; /* Default to hidden */
}

/* If the user's system requests a dark theme: */
@media (prefers-color-scheme: dark) {
    #logo-light { display: none; }
    #logo-dark { display: block; }
}

/* 2. Centered Content Area */
#masthead-text {
    flex: 1; /* Take all remaining space */
    text-align: middle;
}

#masthead-text h1 { 
    font-family: 'Playfair Display', serif !important; 
    font-size: 2.2rem !important; 
    margin: 0 !important; 
    line-height: 1.2;
}

#masthead-text p {
    font-family: 'Source Serif 4', serif !important;
    font-size: 1.1rem;
    margin: 5px 0 0 0;
    opacity: 0.8;
}

/* Adapt Panels & Textarea to Themes */
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

.gradio-container label span {
    font-weight: bold !important;
    text-transform: uppercase !important;
    letter-spacing: 0.05em !important;
}
"""

def build_ui() -> gr.Blocks:
    with gr.Blocks(css=CSS, title="Versant AI: Press Release Generator", theme=gr.themes.Soft()) as app:
        
        # UPDATED MASTHEAD: Now with flexible layout and dynamic icons
        gr.HTML(f"""
            <div id="masthead">
                <div id="versant-logo">
                    <img id="logo-light" src="file/VSNT_BIG.png" alt="Versant Logo" />
                    <img id="logo-dark" src="file/VSNT_BIG.D.png" alt="Versant Logo" />
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
                generate_btn = gr.Button("Generate Press Release", variant="primary", size="lg")
                status = gr.Textbox(label="System Status", interactive=False, lines=1)
                
                with gr.Accordion("System Details", open=False):
                    gr.Markdown("""
                    - **Auth:** On-Behalf-Of (OBO)
                    - **Engine:** Genie (SQL Warehouse)
                    - **Styling:** Knowledge Assistant (RAG)
                    - **Inference:** Llama 3.3 70B
                    """)
            
            with gr.Column(scale=2, elem_id="output-body"):
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

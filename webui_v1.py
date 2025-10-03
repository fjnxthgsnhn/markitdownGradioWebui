import gradio as gr
from markitdown import MarkItDown

def convert_to_markdown(file):
    md = MarkItDown(enable_plugins=False)
    result = md.convert(file.name)
    return result.text_content

with gr.Blocks() as demo:
    gr.Markdown("### MarkItDown Gradio WebUI: Office/PDF/画像→Markdown変換")
    file_input = gr.File(label="変換するファイルをアップロード")
    output = gr.Textbox(label="Markdown結果", lines=20)
    gr.Button("変換").click(fn=convert_to_markdown, inputs=file_input, outputs=output)

demo.launch()

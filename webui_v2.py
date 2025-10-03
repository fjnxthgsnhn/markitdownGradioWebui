import tempfile
import gradio as gr
from markitdown import MarkItDown
import zipfile
import io
import os

def convert_and_zip(file):
    md = MarkItDown(enable_plugins=True)
    result = md.convert(file.name, keep_data_uris=True)
    print(result.__dict__)  # ←ここで全属性確認
    md_text = result.text_content

    # 画像の抽出
    images = {}
    # 正規表現でbase64エンコードされた画像データを抽出
    # 例: ![](data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAA...)
    img_pattern = re.compile(r"!\[.*?\]\((data:(?P<mime>image/[^;]+);base64,(?P<data>[^)]+))\)")
    
    # 新しいmd_textを構築し、元のmd_textからbase64画像を削除
    new_md_text = md_text
    for i, match in enumerate(img_pattern.finditer(md_text)):
        full_match = match.group(0)
        mime_type = match.group("mime")
        base64_data = match.group("data")
        
        try:
            img_bytes = base64.b64decode(base64_data)
            # ファイル名と拡張子を決定
            ext = mime_type.split('/')[-1]
            img_name = f"image_{i+1}.{ext}"
            images[img_name] = img_bytes
            
            # Markdownからbase64画像を相対パスに置き換える
            new_md_text = new_md_text.replace(full_match, f"![{img_name}]({img_name})")
        except Exception as e:
            print(f"Error decoding base64 image: {e}")
            continue

    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w") as zf:
        zf.writestr("output.md", new_md_text) # 修正されたMarkdownを書き込む
        for img_name, img_bytes in images.items():
            zf.writestr(img_name, img_bytes)
    zip_buffer.seek(0)

    # 一時ファイルとして保存し、そのパスを返す
    with tempfile.NamedTemporaryFile(delete=False, suffix=".zip") as tmp:
        tmp.write(zip_buffer.getvalue())
        tmp_path = tmp.name

    return tmp_path

with gr.Blocks() as demo:
    gr.Markdown("### MarkItDown: Office/PDF→Markdown＋図抽出zipダウンロード")
    file_input = gr.File(label="変換ファイルをアップロード")
    output_zip = gr.File(label="Markdown+画像付きZIP", type="filepath")
    gr.Button("変換してZIPダウンロード").click(fn=convert_and_zip, inputs=file_input, outputs=output_zip)

demo.launch()

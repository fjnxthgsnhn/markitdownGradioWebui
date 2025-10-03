import gradio as gr
from markitdown import MarkItDown
import os
import zipfile
import re
import base64
import requests
import shutil
import tempfile
import mimetypes

def convert_and_zip(file_obj, url_input):
    md = MarkItDown(enable_plugins=False)
    markdown_content = ""
    output_files = {} # filename: content (bytes)

    if file_obj:
        # Handle file upload
        file_path = file_obj.name
        result = md.convert(file_path, keep_data_uris=True)
        markdown_content = result.text_content
        output_files["converted.md"] = markdown_content.encode('utf-8')
    elif url_input:
        # Handle URL input
        try:
            result = md.convert(url_input, keep_data_uris=True)
            markdown_content = result.text_content
            output_files["converted.md"] = markdown_content.encode('utf-8')
        except Exception as e:
            return f"URL変換エラー: {e}", None # Return None for download_zip in case of error

    # Extract and process images from markdown_content
    # Regex for Base64 images: ![alt text](data:image/png;base64,...)
    base64_image_pattern = re.compile(r"!\[.*?\]\((data:image/(?:png|jpeg|gif|bmp|webp);base64,[^)]+)\)")
    # Regex for URL images: ![alt text](http://example.com/image.png) or ![alt text](/path/to/image.jpg)
    url_image_pattern = re.compile(r"!\[.*?\]\((https?://[^)]+\.(?:png|jpeg|jpg|gif|bmp|webp))|(/[^)]+\.(?:png|jpeg|jpg|gif|bmp|webp))\)")

    # Process Base64 images
    for i, match in enumerate(base64_image_pattern.finditer(markdown_content)):
        data_uri = match.group(1)
        header, encoded = data_uri.split(",", 1)
        mime_type = header.split(":")[1].split(";")[0]
        extension = mimetypes.guess_extension(mime_type)
        if not extension:
            extension = ".bin" # Fallback
        
        image_data = base64.b64decode(encoded)
        image_filename = f"image_base64_{i}{extension}"
        output_files[image_filename] = image_data
        # Replace data URI with local file reference in markdown
        markdown_content = markdown_content.replace(data_uri, image_filename)

    # Process URL images (simple download for now, relative paths are tricky without context)
    for i, match in enumerate(url_image_pattern.finditer(markdown_content)):
        image_url = match.group(1) or match.group(2) # Group 1 for http/https, Group 2 for relative path (not fully supported yet)
        if image_url and image_url.startswith("http"): # Only download absolute URLs for now
            try:
                response = requests.get(image_url, stream=True)
                response.raise_for_status()
                
                content_type = response.headers.get('content-type')
                extension = mimetypes.guess_extension(content_type)
                if not extension:
                    extension = os.path.splitext(image_url)[1] or ".bin"
                
                image_filename = f"image_url_{i}{extension}"
                output_files[image_filename] = response.content
                # Replace URL with local file reference in markdown
                markdown_content = markdown_content.replace(image_url, image_filename)
            except Exception as e:
                print(f"Failed to download image from {image_url}: {e}")
                # Keep original URL in markdown if download fails

    # Create a temporary file for the zip archive
    # NamedTemporaryFile ensures the file exists until explicitly closed/deleted
    with tempfile.NamedTemporaryFile(delete=False, suffix=".zip") as tmp_zip_file:
        zip_file_path = tmp_zip_file.name
        with zipfile.ZipFile(zip_file_path, 'w') as zf:
            for filename, content in output_files.items():
                if filename == "converted.md":
                    # Update the markdown content with local image references before writing to zip
                    zf.writestr(filename, markdown_content.encode('utf-8'))
                else:
                    zf.writestr(filename, content)
    
    # Return the markdown content and the path to the temporary zip file
    # Gradio will handle serving this file for download.
    return markdown_content, zip_file_path


# Define accepted file types for gr.File
# Based on converters list:
# .csv, .docx, .epub, .html, .jpg, .jpeg, .png, .ipynb, .msg, .pdf, .pptx, .txt, .xlsx, .zip, .mp3, .wav, .ogg
# Note: .zip is for input, not output. Audio types are inferred.
ACCEPTED_FILE_TYPES = [
    ".csv", ".doc", ".docx", ".epub", ".html", ".htm", ".jpeg", ".jpg", ".png", ".gif", ".bmp", ".webp",
    ".ipynb", ".msg", ".pdf", ".ppt", ".pptx", ".txt", ".text", ".xlsx", ".xls", ".zip",
    ".mp3", ".wav", ".ogg", ".flac", ".aac" # Common audio formats
]

with gr.Blocks() as demo:
    gr.Markdown("### MarkItDown Gradio WebUI: Office/PDF/画像/URL→Markdown変換 & Zipダウンロード")

    with gr.Tabs() as tabs:
        with gr.TabItem("ファイルアップロード", id=0):
            file_input = gr.File(label="変換するファイルをアップロード", file_types=ACCEPTED_FILE_TYPES)
        with gr.TabItem("URL入力", id=1):
            url_input = gr.Textbox(label="変換するURLを入力 (例: RSS, Wikipedia, YouTube, Bing SERP)", placeholder="https://example.com/article.html")
    
    output_markdown = gr.Textbox(label="Markdown結果", lines=20)
    download_zip = gr.File(label="変換結果をダウンロード (Markdownと画像)", file_count="single", interactive=False)

    gr.Button("変換").click(
        fn=convert_and_zip, 
        inputs=[file_input, url_input], 
        outputs=[output_markdown, download_zip]
    )

demo.launch()

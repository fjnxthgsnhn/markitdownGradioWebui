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
import json
import base64
import hashlib
from cryptography.fernet import Fernet

# 設定ファイルのパス
CONFIG_FILE = "config.json"

def generate_key():
    """暗号化キーを生成（マシン固有のキーを使用）"""
    machine_id = hashlib.sha256(os.environ.get('COMPUTERNAME', 'default').encode()).digest()
    return base64.urlsafe_b64encode(machine_id[:32])

def encrypt_data(data, key):
    """データを暗号化"""
    fernet = Fernet(key)
    return fernet.encrypt(data.encode()).decode()

def decrypt_data(encrypted_data, key):
    """データを復号化"""
    try:
        fernet = Fernet(key)
        return fernet.decrypt(encrypted_data.encode()).decode()
    except:
        return ""

def save_config(gemini_api_key, selected_model):
    """設定をファイルに保存"""
    key = generate_key()
    config = {
        "gemini_api_key": encrypt_data(gemini_api_key, key) if gemini_api_key else "",
        "selected_model": selected_model
    }
    with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
        json.dump(config, f, ensure_ascii=False, indent=2)

def load_config():
    """設定をファイルから読み込み"""
    if not os.path.exists(CONFIG_FILE):
        return "", "gemini-pro-vision"
    
    try:
        key = generate_key()
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        api_key = decrypt_data(config.get("gemini_api_key", ""), key) if config.get("gemini_api_key") else ""
        selected_model = config.get("selected_model", "gemini-pro-vision")
        
        return api_key, selected_model
    except Exception as e:
        print(f"設定読み込みエラー: {e}")
        return "", "gemini-pro-vision"

def extract_page_images_from_pdf(pdf_path):
    """Extract each page as a single image from PDF using PyMuPDF and return as base64 encoded data"""
    try:
        import fitz  # PyMuPDF
    except ImportError:
        print("PyMuPDF (fitz) is not installed. Please install it with: pip install pymupdf")
        return []
    
    page_images = []
    try:
        doc = fitz.open(pdf_path)
        for page_num in range(len(doc)):
            page = doc[page_num]
            
            # Render the entire page as an image
            mat = fitz.Matrix(2, 2)  # 2x zoom for better quality
            pix = page.get_pixmap(matrix=mat)
            
            # Convert to PNG bytes
            img_data = pix.tobytes("png")
            mime_type = "image/png"
            
            # Convert to base64
            b64_data = base64.b64encode(img_data).decode('utf-8')
            page_images.append({
                'data': b64_data,
                'mime_type': mime_type,
                'page': page_num + 1
            })
            
            pix = None
        
        doc.close()
        return page_images
    except Exception as e:
        print(f"Error extracting page images from PDF: {e}")
        return []

def check_image_file(file_obj):
    """画像ファイルがアップロードされたかチェックし、警告メッセージを返す"""
    if not file_obj:
        return ""
    
    file_path = file_obj.name
    file_extension = os.path.splitext(file_path)[1].lower()
    
    if file_extension in ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp']:
        warning_message = "⚠️ 警告: 画像ファイルが検出されました\n"
        warning_message += "画像ファイルはLLM（Google Geminiなど）に送信され、画像の説明が生成されます\n"
        warning_message += "プライバシーに配慮が必要な画像の場合は変換を中止してください\n\n"
        return warning_message
    
    return ""

def get_available_models(gemini_api_key):
    """利用可能なGeminiモデルリストを取得"""
    if not gemini_api_key:
        return gr.Dropdown(choices=["gemini-pro-vision"], value="gemini-pro-vision")
    
    try:
        import google.generativeai as genai
        genai.configure(api_key=gemini_api_key)
        models = genai.list_models()
        available_models = []
        for model in models:
            if 'generateContent' in model.supported_generation_methods:
                available_models.append(model.name.split('/')[-1])
        
        if available_models:
            # 画像処理に適したモデルを優先的に選択
            preferred_models = [model for model in available_models if 'vision' in model.lower() or 'flash' in model.lower()]
            default_model = preferred_models[0] if preferred_models else available_models[0]
            return gr.Dropdown(choices=available_models, value=default_model)
        else:
            return gr.Dropdown(choices=["gemini-pro-vision"], value="gemini-pro-vision")
    except Exception as e:
        print(f"モデルリスト取得エラー: {e}")
        return gr.Dropdown(choices=["gemini-pro-vision"], value="gemini-pro-vision")

def convert_and_zip(file_obj, url_input, gemini_api_key, selected_model):
    markdown_content = ""
    output_files = {} # filename: content (bytes)
    
    # MarkItDownの初期化
    md = MarkItDown(enable_plugins=False)
    warning_message = ""
    
    # 画像ファイルの場合はLLMを使用するか確認
    file_extension = None
    if file_obj:
        file_path = file_obj.name
        file_extension = os.path.splitext(file_path)[1].lower()
    
    # 画像ファイルの場合はLLMを使用（APIキーが設定されている場合）
    if file_obj and file_extension in ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp'] and gemini_api_key:
        try:
            import google.generativeai as genai
            import PIL.Image
            genai.configure(api_key=gemini_api_key)
            # 選択されたモデルを使用
            model = genai.GenerativeModel(selected_model)
            warning_message = f"Google Gemini ({selected_model})を使用して画像の説明を生成します...\n\n"
            
            # 画像を読み込んでGeminiで処理
            img = PIL.Image.open(file_path)
            response = model.generate_content([
                "この画像を詳細に説明してください。画像に含まれるテキストがあればOCRで抽出し、画像の内容を詳しく説明してください。",
                img
            ])
            
            # Geminiの応答をMarkdownに追加
            gemini_description = f"## 画像の説明 (Google Gemini {selected_model})\n\n{response.text}\n\n---\n\n"
            markdown_content = gemini_description
            # 通常の変換は行わず、Geminiの説明のみを使用
            skip_normal_conversion = True
            
        except ImportError:
            warning_message = "Google Generative AIパッケージがインストールされていません。通常の変換を行います。\n\n"
            skip_normal_conversion = False
        except Exception as e:
            warning_message = f"Google Geminiの処理に失敗しました: {e}。通常の変換を行います。\n\n"
            skip_normal_conversion = False
    else:
        skip_normal_conversion = False

    if file_obj:
        # Handle file upload
        file_path = file_obj.name
        file_extension = os.path.splitext(file_path)[1].lower()
        file_basename = os.path.splitext(os.path.basename(file_path))[0]
        
        # For PDF files, extract page images first
        pdf_images = []
        if file_extension == '.pdf':
            pdf_images = extract_page_images_from_pdf(file_path)
        
        # Gemini APIが成功した場合は通常の変換をスキップ
        if not skip_normal_conversion:
            # Convert to markdown
            try:
                result = md.convert(file_path, keep_data_uris=True)
                markdown_content = result.text_content
            except Exception as e:
                error_msg = f"ファイル変換エラー: {e}\n"
                if "API key" in str(e) or "authentication" in str(e).lower():
                    error_msg += "Google Gemini APIキーが無効です。通常の変換を試みます。\n"
                    # 通常のMarkItDownで再試行
                    md_normal = MarkItDown(enable_plugins=False)
                    result = md_normal.convert(file_path, keep_data_uris=True)
                    markdown_content = error_msg + result.text_content
                elif "quota" in str(e).lower() or "rate limit" in str(e).lower():
                    error_msg += "Google Gemini APIの利用制限に達しました。通常の変換を試みます。\n"
                    # 通常のMarkItDownで再試行
                    md_normal = MarkItDown(enable_plugins=False)
                    result = md_normal.convert(file_path, keep_data_uris=True)
                    markdown_content = error_msg + result.text_content
                else:
                    markdown_content = error_msg + "変換に失敗しました。"
        
        # 警告メッセージをMarkdownの先頭に追加
        if warning_message:
            markdown_content = warning_message + markdown_content
            
        output_files[f"{file_basename}.md"] = markdown_content.encode('utf-8')
        
        # Add PDF images to output and insert image references at the end of each page
        # Group images by page
        page_images_dict = {}
        for img in pdf_images:
            page_num = img['page']
            if page_num not in page_images_dict:
                page_images_dict[page_num] = []
            page_images_dict[page_num].append(img)
        
        # Insert image references at appropriate positions in markdown
        # Use a simpler approach: insert images after each page's content
        markdown_lines = markdown_content.split('\n')
        new_markdown_lines = []
        current_page = 1
        
        # Process each line and insert images at page boundaries
        for line_num, line in enumerate(markdown_lines):
            new_markdown_lines.append(line)
            
            # Check for page breaks - look for form feed character (0x0C) which indicates page break
            if '\x0c' in line:
                # Insert images for current page before the page break
                if current_page in page_images_dict:
                    for i, img in enumerate(page_images_dict[current_page]):
                        extension = mimetypes.guess_extension(img['mime_type']) or ".png"
                        image_filename = f"{file_basename}_page{current_page}_{i}{extension}"
                        image_data = base64.b64decode(img['data'])
                        output_files[image_filename] = image_data
                        
                        # Add image reference
                        image_ref = f"\n\n<!-- PDF Image from page {current_page} -->\n![PDF Image {i}]({image_filename})\n"
                        new_markdown_lines.append(image_ref)
                
                current_page += 1
        
        # Insert images for the last page
        if current_page in page_images_dict:
            for i, img in enumerate(page_images_dict[current_page]):
                extension = mimetypes.guess_extension(img['mime_type']) or ".png"
                image_filename = f"{file_basename}_page{current_page}_{i}{extension}"
                image_data = base64.b64decode(img['data'])
                output_files[image_filename] = image_data
                
                # Add image reference
                image_ref = f"\n\n<!-- PDF Image from page {current_page} -->\n![PDF Image {i}]({image_filename})\n"
                new_markdown_lines.append(image_ref)
        
        markdown_content = '\n'.join(new_markdown_lines)
        
    elif url_input:
        # Handle URL input
        try:
            result = md.convert(url_input, keep_data_uris=True)
            markdown_content = result.text_content
            # Create URL-based filename
            url_basename = "converted_from_url"
            if url_input:
                # Extract domain name for filename
                from urllib.parse import urlparse
                parsed_url = urlparse(url_input)
                if parsed_url.netloc:
                    url_basename = parsed_url.netloc.replace('.', '_')
            output_files[f"{url_basename}.md"] = markdown_content.encode('utf-8')
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
        # Use appropriate basename based on input type
        if file_obj:
            image_filename = f"{file_basename}_base64_{i}{extension}"
        else:
            image_filename = f"{url_basename}_base64_{i}{extension}"
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
                
                # Use appropriate basename based on input type
                if file_obj:
                    image_filename = f"{file_basename}_url_{i}{extension}"
                else:
                    image_filename = f"{url_basename}_url_{i}{extension}"
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
                # Determine the correct markdown filename
                markdown_filename = None
                if file_obj:
                    markdown_filename = f"{file_basename}.md"
                else:
                    markdown_filename = f"{url_basename}.md"
                
                if filename == markdown_filename:
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

def save_settings(gemini_api_key, selected_model):
    """設定を保存"""
    save_config(gemini_api_key, selected_model)
    return "設定を保存しました"

# 設定を読み込み
loaded_api_key, loaded_model = load_config()

with gr.Blocks() as demo:
    gr.Markdown("### MarkItDown Gradio WebUI: Office/PDF/画像/URL→Markdown変換 & Zipダウンロード")

    with gr.Tabs() as tabs:
        with gr.TabItem("ファイルアップロード", id=0):
            file_input = gr.File(label="変換するファイルをアップロード", file_types=ACCEPTED_FILE_TYPES)
            image_warning = gr.Textbox(label="画像ファイル警告", lines=3, interactive=False, visible=False)
        with gr.TabItem("URL入力", id=1):
            url_input = gr.Textbox(label="変換するURLを入力 (例: RSS, Wikipedia, YouTube, Bing SERP)", placeholder="https://example.com/article.html")
        with gr.TabItem("設定", id=2):
            gr.Markdown("### Google Gemini API設定")
            with gr.Row():
                gemini_api_key = gr.Textbox(
                    label="Google Gemini APIキー (画像ファイルのLLM処理に必要)",
                    placeholder="AIza...",
                    type="password",
                    value=loaded_api_key,
                    info="画像ファイルのLLM処理にはGoogle Gemini APIキーが必要です。取得方法: https://aistudio.google.com/app/apikey"
                )
            
            with gr.Row():
                model_dropdown = gr.Dropdown(
                    label="使用するモデル",
                    choices=["gemini-pro-vision"],  # 初期値
                    value=loaded_model,
                    info="APIキーを設定すると利用可能なモデルリストが表示されます"
                )
            
            save_status = gr.Textbox(label="保存ステータス", interactive=False, visible=False)
            
            gr.Button("設定を保存").click(
                fn=save_settings,
                inputs=[gemini_api_key, model_dropdown],
                outputs=[save_status]
            )
    
    # 出力コンポーネントは設定タブの外に配置
    output_markdown = gr.Textbox(label="Markdown結果", lines=20)
    download_zip = gr.File(label="変換結果をダウンロード (Markdownと画像)", file_count="single", interactive=False)

    # ファイル入力時のリアルタイム警告
    file_input.change(
        fn=check_image_file,
        inputs=[file_input],
        outputs=[image_warning]
    )

    # APIキー変更時にモデルリストを更新
    gemini_api_key.change(
        fn=get_available_models,
        inputs=[gemini_api_key],
        outputs=[model_dropdown]
    )

    gr.Button("変換").click(
        fn=convert_and_zip, 
        inputs=[file_input, url_input, gemini_api_key, model_dropdown], 
        outputs=[output_markdown, download_zip]
    )

demo.launch()

# MarkItDown Web UI

MarkItDownプロジェクトのWebベースユーザーインターフェーススクリプトです。ブラウザから直感的にファイル変換を行うことができます。

## 使用方法

### Windowsでの実行
```bash
run_webui.bat
```

または直接Pythonスクリプトを実行：
```bash
python webui.py
```

### その他のOSでの実行
```bash
python webui.py
```

## 機能

- ファイルのドラッグ＆ドロップによるアップロード
- 複数のファイル形式のサポート（PDF, DOCX, PPTX, XLSX, 画像など）
- リアルタイム変換プレビュー
- 変換結果のダウンロード
- レスポンシブデザイン

## 対応ファイル形式

- **PDF** - テキスト抽出とページ画像の埋め込み
- **Word (.docx)** - 文書構造の保持と画像抽出
- **PowerPoint (.pptx)** - スライドコンテンツの変換
- **Excel (.xlsx)** - 表データの変換
- **画像** - Google Gemini APIによる高度な画像認識と説明生成
- **音声ファイル** - Google Speech Recognition APIによる文字起こし（MP3, WAV, OGG, FLAC, AAC, M4A）
- **HTML** - マークダウンへの変換
- **テキストファイル** - 各種形式（CSV, JSON, XMLなど）

## Google Gemini APIの設定

画像ファイルの高度な処理と音声ファイルの文字起こしには、Google Gemini APIキーの設定が必要です。

### Gemini APIキーの取得方法

1. [Google AI Studio](https://aistudio.google.com/app/apikey)にアクセス
2. Googleアカウントでログイン
3. 「APIキーを作成」をクリック
4. プロジェクトを選択または新規作成
5. APIキーが生成されるのでコピー

### Web UIでの設定方法

1. Web UIの「設定」タブを開く
2. 「Google Gemini APIキー」欄に取得したAPIキーを入力
3. 「モデルリスト更新」ボタンをクリックして利用可能なモデルを取得
4. 「設定を保存」ボタンをクリック

### 対応モデル

- **gemini-pro-vision** - 画像認識とテキスト生成
- **gemini-1.5-flash** - 高速なマルチモーダル処理
- **gemini-1.5-pro** - 高精度なマルチモーダル処理
- その他利用可能なGeminiモデル

### プライバシーとセキュリティ

- APIキーはローカルマシンで暗号化されて保存されます
- 画像ファイルはGoogleのサーバーに送信され、画像の説明が生成されます
- プライバシーに配慮が必要な画像の場合は変換を中止してください

## 必要条件

- Python 3.10以上

## インストール方法

## Windowsの場合
### ステップ1: リポジトリのクローン
```bash
git clone https://github.com/fjnxthgsnhn/markitdownGradioWebui.git
cd markitdown
```
### ステップ2: webui.batの起動
```
run_webui.bat
```
必要なライブラリが自動的にインストールされ仮想環境が作られ、webuiが自動的に立ち上がります。

## Windows以外の場合
### ステップ1: リポジトリのクローン
```bash
git clone https://github.com/fjnxthgsnhn/markitdownGradioWebui.git
cd markitdown
```

### ステップ2: 仮想環境の作成と有効化（推奨）
```bash
# 仮想環境の作成
python -m venv venv

# macOS/Linux
source venv/bin/activate
```

### ステップ3: 依存関係のインストール

#### 方法1: requirements.txtを使用（推奨）
```bash
pip install -r requirements.txt
```

#### 方法2: 個別インストール
```bash
pip install 'markitdown[all]' gradio pymupdf Pillow requests python-magic
```

## 注意事項

- 大容量ファイルの変換には時間がかかる場合があります
- 変換品質は元ファイルの構造と内容に依存します

## トラブルシューティング

**Web UIが起動しない場合：**
1. Pythonと必要なパッケージがインストールされているか確認
2. ポート5000が使用されていないか確認
3. ファイアウォールの設定を確認

**ファイル変換に失敗する場合：**
1. ファイル形式がサポートされているか確認
2. ファイルが破損していないか確認
3. 十分なメモリがあるか確認

## ライセンス

このプロジェクトはMicrosoft MarkItDownプロジェクトの一部です。詳細なライセンス情報については、元のREADME.mdを参照してください。

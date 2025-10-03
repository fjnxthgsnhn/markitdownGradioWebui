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

- **PDF** - テキスト抽出
- **Word (.docx)** - 文書構造の保持
- **PowerPoint (.pptx)** - スライドコンテンツの変換
- **Excel (.xlsx)** - 表データの変換
- **画像** - OCRによるテキスト抽出
- **HTML** - マークダウンへの変換
- **テキストファイル** - 各種形式（CSV, JSON, XMLなど）

## 必要条件

- Python 3.10以上

## インストール方法

## Windowsの場合
### ステップ1: リポジトリのクローン
```bash
git clone https://github.com/あなたのユーザー名/markitdown.git
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
git clone https://github.com/あなたのユーザー名/markitdown.git
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

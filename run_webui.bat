@echo off
chcp 65001 >nul
title MarkItDown WebUI Launcher

echo ========================================
echo   MarkItDown WebUI 自動起動スクリプト
echo ========================================
echo.

REM カレントディレクトリをスクリプトのある場所に設定
cd /d "%~dp0"

REM venvディレクトリの存在確認
if not exist "venv" (
    echo venvディレクトリが見つかりません
    echo 自動的にPython仮想環境を作成します...
    echo.
    
    REM Pythonのバージョンチェック
    python --version >nul 2>&1
    if %ERRORLEVEL% neq 0 (
        echo [エラー] Pythonがインストールされていないか、PATHに設定されていません
        echo Python 3.10以上をインストールしてから再度実行してください
        pause
        exit /b 1
    )
    
    REM 仮想環境の作成
    echo 仮想環境を作成しています...
    python -m venv venv
    if %ERRORLEVEL% neq 0 (
        echo [エラー] 仮想環境の作成に失敗しました
        echo Pythonのインストール状態を確認してください
        pause
        exit /b 1
    )
    echo 仮想環境が正常に作成されました
    echo.
)

REM venvのactivateスクリプトの存在確認
if not exist "venv\Scripts\activate.bat" (
    echo [エラー] venv\Scripts\activate.batが見つかりません
    echo 仮想環境が正しく作成されているか確認してください
    pause
    exit /b 1
)

REM webui.pyの存在確認
if not exist "webui.py" (
    echo [エラー] webui.pyが見つかりません
    pause
    exit /b 1
)

echo venv仮想環境を有効化しています...
call venv\Scripts\activate.bat

if %ERRORLEVEL% neq 0 (
    echo [エラー] 仮想環境の有効化に失敗しました
    pause
    exit /b 1
)

echo 仮想環境が正常に有効化されました
echo.

echo Pythonパッケージの依存関係を確認しています...
python -c "import gradio, markitdown, fitz, PIL, requests, magic" >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo 必要なパッケージがインストールされていません
    echo インストールを開始します...
    
    REM requirements.txtが存在する場合はそれを使用
    if exist "requirements.txt" (
        echo requirements.txtを使用して依存関係をインストールします...
        pip install -r requirements.txt
    ) else (
        echo 個別にパッケージをインストールします...
        pip install gradio markitdown[all] pymupdf Pillow requests python-magic
    )
    
    if %ERRORLEVEL% neq 0 (
        echo [警告] パッケージのインストール中に問題が発生しました
        echo 一部のパッケージが正常にインストールされていない可能性があります
        echo 手動で確認してください: pip install -r requirements.txt
        echo.
    ) else (
        echo パッケージのインストールが完了しました
        echo.
    )
)

echo ========================================
echo   MarkItDown WebUI を起動します
echo ========================================
echo.
echo ブラウザを自動で開きます...
echo 終了する場合は Ctrl+C を押してください
echo.

REM バックグラウンドでブラウザを開く
start "" "http://127.0.0.1:7860"

REM WebUIを起動
python webui.py

REM スクリプト終了時に仮想環境を無効化
call venv\Scripts\deactivate.bat

echo.
echo MarkItDown WebUI が終了しました
pause

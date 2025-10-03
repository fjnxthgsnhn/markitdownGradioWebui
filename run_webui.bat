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
    echo [エラー] venvディレクトリが見つかりません
    echo Python仮想環境を作成してください
    echo python -m venv venv
    pause
    exit /b 1
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
python -c "import gradio, markitdown" >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo 必要なパッケージがインストールされていません
    echo インストールを開始します...
    pip install gradio markitdown pymupdf requests
    if %ERRORLEVEL% neq 0 (
        echo [エラー] パッケージのインストールに失敗しました
        pause
        exit /b 1
    )
    echo パッケージのインストールが完了しました
    echo.
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

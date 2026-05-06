#!/usr/bin/env pwsh
$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

Write-Host "YouTube トレンド分析ツール セットアップ"
Write-Host "----------------------------------------"

if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    Write-Host "[ERROR] python が見つかりません。"
    Write-Host "        https://www.python.org/downloads/ からインストールしてください。"
    exit 1
}

if (-not (Test-Path ".venv")) {
    Write-Host "[1/3] 仮想環境を作成中..."
    python -m venv .venv
} else {
    Write-Host "[1/3] 既存の仮想環境を使用"
}

Write-Host "[2/3] 依存パッケージをインストール中..."
& .venv\Scripts\pip.exe install --quiet --upgrade pip
& .venv\Scripts\pip.exe install --quiet -r requirements.txt

$secrets = ".streamlit\secrets.toml"
New-Item -ItemType Directory -Path ".streamlit" -Force | Out-Null

$needsKey = $true
if (Test-Path $secrets) {
    if (Select-String -Path $secrets -Pattern "^YOUTUBE_API_KEY" -Quiet) {
        $needsKey = $false
    }
}

if ($needsKey) {
    Write-Host ""
    Write-Host "[3/3] YouTube Data API v3 のキーを入力してください"
    Write-Host "      取得方法: https://console.cloud.google.com/"
    Write-Host "                → APIとサービス → 認証情報"
    Write-Host ""
    $apiKey = Read-Host "APIキー"
    if (-not $apiKey) {
        Write-Host "[ERROR] APIキーが入力されませんでした。"
        exit 1
    }
    "YOUTUBE_API_KEY = `"$apiKey`"" | Set-Content -Path $secrets -Encoding UTF8
    Write-Host "  -> $secrets を作成しました"
} else {
    Write-Host "[3/3] $secrets は既に存在します(スキップ)"
}

Write-Host ""
Write-Host "セットアップ完了。以下で起動できます:"
Write-Host ""
Write-Host "    .venv\Scripts\Activate.ps1; streamlit run app.py"
Write-Host ""

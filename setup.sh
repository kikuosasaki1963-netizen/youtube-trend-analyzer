#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"

echo "YouTube トレンド分析ツール セットアップ"
echo "----------------------------------------"

if ! command -v python3 >/dev/null 2>&1; then
  echo "[ERROR] python3 が見つかりません。"
  echo "        https://www.python.org/downloads/ からインストールしてください。"
  exit 1
fi

if [ ! -d ".venv" ]; then
  echo "[1/3] 仮想環境を作成中..."
  python3 -m venv .venv
else
  echo "[1/3] 既存の仮想環境を使用"
fi

echo "[2/3] 依存パッケージをインストール中..."
.venv/bin/pip install --quiet --upgrade pip
.venv/bin/pip install --quiet -r requirements.txt

SECRETS=".streamlit/secrets.toml"
mkdir -p .streamlit
if [ ! -f "$SECRETS" ] || ! grep -q "^YOUTUBE_API_KEY" "$SECRETS"; then
  echo ""
  echo "[3/3] YouTube Data API v3 のキーを入力してください"
  echo "      取得方法: https://console.cloud.google.com/"
  echo "                → APIとサービス → 認証情報"
  echo ""
  read -r -p "APIキー: " API_KEY
  if [ -z "$API_KEY" ]; then
    echo "[ERROR] APIキーが入力されませんでした。"
    exit 1
  fi
  printf 'YOUTUBE_API_KEY = "%s"\n' "$API_KEY" > "$SECRETS"
  echo "  -> $SECRETS を作成しました"
else
  echo "[3/3] $SECRETS は既に存在します(スキップ)"
fi

echo ""
echo "セットアップ完了。以下で起動できます:"
echo ""
echo "    source .venv/bin/activate && streamlit run app.py"
echo ""

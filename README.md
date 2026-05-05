# YouTube トレンド & 競合分析ツール

YouTube の急上昇/ジャンル別/サジェスト/バズ動画分析と、Google Trends による検索ボリューム調査を一つの Streamlit アプリで提供します。

## 機能

- 急上昇トレンド (日本)
- ジャンル別ランキング
- サジェストキーワード(アルファベットスープ)
- バズ動画分析 (V/S比率フィルタ)
- トレンド調査 (Google Trends 検索ボリューム推移 + 関連キーワード)
- Google検索ワードランキング
- SNSバズニュース

## 動作環境

- Python 3.9 以上
- YouTube Data API v3 のキー

## セットアップ手順 (別PCに展開する場合)

### 1. リポジトリを取得

```bash
git clone https://github.com/kikuosasaki1963-netizen/youtube-trend-analyzer.git
cd youtube-trend-analyzer
```

### 2. 仮想環境を作成して依存をインストール

**macOS / Linux**

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

**Windows (PowerShell)**

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### 3. YouTube API キーを設定

`.streamlit/secrets.toml` を作成し、以下を記入:

```toml
YOUTUBE_API_KEY = "ここにAPIキーを貼り付け"
```

APIキー取得手順:

1. [Google Cloud Console](https://console.cloud.google.com/) でプロジェクトを作成
2. 「APIとサービス」 → 「ライブラリ」 → **YouTube Data API v3** を有効化
3. 「APIとサービス」 → 「認証情報」 → 「認証情報を作成」 → APIキー

### 4. 起動

```bash
streamlit run app.py
```

ブラウザが自動で開きます (デフォルト: http://localhost:8501)。

## トラブルシューティング

### Google Trends で「データ取得に失敗しました: 429」が出る

短時間に多くのリクエストを送ると Google から一時的にブロックされます。
本ツールは自動リトライ(指数バックオフ)と6時間キャッシュを実装済みですが、それでも 429 が解消しない場合は **5〜30分待ってから**再度お試しください。
同じキーワードの結果はキャッシュされるため、2回目以降は瞬時に表示されます。

### YouTube Data API のクォータ超過

YouTube Data API v3 は1日10,000ユニットまで無料です。サイドバーの「クォータ状況」で残量を確認できます。
超過した場合は翌日(太平洋時間00:00)にリセットされます。

## テスト

```bash
pytest tests/
```

## ライセンス

個人利用想定。

# YouTubeトレンド＆競合分析ツール 要件定義書

## 1. プロジェクト概要

- **プロジェクト名**: YouTubeトレンド＆競合分析ツール
- **技術スタック**: Python 3.9 / Streamlit / YouTube Data API v3 / Google Trends / Googleサジェスト
- **リポジトリ**: youtube-trend-analyzer

## 2. 既存機能一覧（実装済み）

### タブ0: 急上昇トレンド（日本）
- 全カテゴリ（15種）の急上昇動画取得
- バズキーワードランキング TOP30（タイトルからの頻出ワード抽出）
- カテゴリ分布分析
- サムネイル一覧・データテーブル・CSVダウンロード

### タブ1: ジャンル別ランキング
- ジャンル選択（全ジャンル or 個別カテゴリ）
- 期間選択（7/30/90/365日）
- キーワード検索（任意）
- バズキーワードランキング・人気動画TOP15・CSVダウンロード

### タブ2: サジェストキーワード収集
- 基本サジェスト取得（Googleサジェスト非公式API）
- アルファベットスープ法（50音46 + 英字26 + 数字10 = 82サフィックス）
- 統合・重複排除・CSVダウンロード

### タブ3: バズ動画分析（V/S比率）
- V/S比率 = 再生数 / 登録者数
- 検索 → 動画詳細 → チャンネル詳細 → V/S比率計算
- フィルタ（登録者数上限、再生数下限、V/S比率下限、期間）
- サムネイルグリッド・データテーブル・CSVダウンロード

### タブ4: トレンド調査（Google Trends）
- 急上昇検索ワードTOP10 + 関連ニュース
- キーワード別検索ボリューム推移（ピーク日・現在値）
- 関連キーワード（急上昇/人気）

## 3. リファクタリング要件

### 3.1 機能要件
- 既存の全機能が正常に動作すること（回帰なし）
- UIの見た目・操作感に変更なし

### 3.2 非機能要件

#### 構造改善（Phase 1）
- app.py を約80行に縮小（現688行）
- タブごとにモジュール分離（src/tabs/）
- 重複コードの共通化（サムネイル表示3箇所、CSV出力4箇所）
- マジックナンバーの定数化（src/constants.py）
- ビジネスロジック層から不要な Streamlit 依存を除去

#### テスト品質（Phase 2）
- テスト数: 35個 → 68個以上
- trending.py: 0テスト → 14テスト
- trends_api.py: 0テスト → 12テスト
- ui_components.py: 0テスト → 5テスト

#### 堅牢性（Phase 3）
- session_state キーの定数化（文字列ハードコード排除）
- Google Trends RSS のエラーハンドリング強化
- fetch_and_analyze() の責務分離
- 型ヒントの網羅性向上

#### 運用品質（Phase 4）
- ログ機構の導入（src/logger.py）
- API呼び出しのログ出力
- デバッグ・障害追跡の容易化

## 4. 型定義（実装済み）

→ 詳細は「5. 型設計」セクション参照

## 5. 型設計（リファクタリングで追加・整備）

### 新規追加型

```python
# src/session_keys.py
class SessionKeys:
    """セッションステート管理キーの定数クラス."""
    QUOTA_TRACKER: str
    TRENDING_VIDEOS: str
    TRENDING_BY_CATEGORY: str
    GENRE_VIDEOS: str
    GENRE_LABEL: str
    ANALYZED_VIDEOS: str
    BASE_SUGGESTIONS: str
    ALL_SUGGESTIONS: str
    TRENDING_SEARCHES: str
    TREND_INTEREST: str
    TREND_RELATED: str
    TREND_KEYWORD: str
```

### 既存型の整備

```python
# src/youtube_api.py - 変更なし（既存のまま）
@dataclass
class VideoInfo:
    video_id: str
    title: str
    channel_id: str
    channel_title: str
    published_at: str
    thumbnail_url: str
    view_count: int = 0
    subscriber_count: int = 0
    vs_ratio: float = 0.0

@dataclass
class QuotaTracker:
    used: int = 0
    daily_limit: int = 10_000

class QuotaExceededError(Exception): ...
```

### 関数シグネチャの型ヒント追加

```python
# src/analyzer.py - 内部関数の型明示化
def _extract_search_info(
    search_results: list[dict],
) -> tuple[list[VideoInfo], list[str], set[str]]: ...

def _calculate_vs_ratios(
    videos: list[VideoInfo],
    video_stats: dict[str, dict],
    channel_stats: dict[str, dict],
) -> None: ...

# src/suggest_api.py - コールバック型明示化
progress_callback: Callable[[int, int], None] | None = None

# src/constants.py - 定数辞書の型明示化
PERIOD_OPTIONS: dict[str, Optional[int]]
GENRE_PERIOD_OPTIONS: dict[str, int]
TREND_PERIOD_MAP: dict[str, str]
```

### Python 3.9 互換性注記

- `from __future__ import annotations` を全モジュールで使用
- ランタイム型（定数の型注釈等）には `Optional[X]` を使用（`X | None` は3.10+）
- 文字列アノテーション内では `X | None` 使用可

## 6. 設計判断

### app.py をタブごとに分離する理由
- 688行の単一ファイルは保守性が低い
- 各タブは独立した機能であり、責務が明確に分かれる
- タブ単位でのテスト・修正が容易になる

### ビジネスロジック層から Streamlit を除去する理由
- analyzer.py, suggest_api.py は `import streamlit` しているが未使用
- trending.py は `@st.cache_data` で使用 → キャッシュ層として残す
- ロジック層がUI層に依存すると、テスト困難・再利用不可

### セッションキーを定数化する理由
- 12個のキーが文字列ハードコード
- リファクタ時の修正漏れリスクが高い
- IDE補完・型チェックが効かない

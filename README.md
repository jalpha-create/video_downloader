# 📺 YouTube Video Downloader

現代的なUIと安全性を重視したYouTube動画ダウンロードツールです。Streamlitで構築され、クラウドデプロイに対応しています。

## ✨ 主な機能

- 🎬 **高品質動画ダウンロード**: 1080p以上の高画質対応
- 🎵 **音声のみダウンロード**: MP3/MP4形式
- 🔄 **自動マージ**: 動画と音声の自動結合
- 📊 **詳細情報表示**: ファイルサイズ、再生時間、投稿者情報
- ⚠️ **安全性重視**: URL検証、ファイルサイズ制限、タイムアウト処理
- 🎨 **モダンUI**: 直感的で美しいインターフェース

## 🚀 クイックスタート

### ローカル実行

1. **リポジトリをクローン**
   ```bash
   git clone <your-repo-url>
   cd video_downloader
   ```

2. **依存関係をインストール**
   ```bash
   pip install -r requirements.txt
   ```

3. **アプリを起動**
   ```bash
   streamlit run app.py
   ```

### 🌐 デプロイ方法

#### Streamlit Community Cloud（推奨）

1. **GitHubにコードをプッシュ**
   ```bash
   git add .
   git commit -m "Deploy ready version"
   git push origin main
   ```

2. **Streamlit Cloudでデプロイ**
   - [share.streamlit.io](https://share.streamlit.io) にアクセス
   - GitHubアカウントでサインアップ
   - リポジトリを選択して「Deploy」

3. **設定が自動で読み込まれます**
   - `packages.txt`: システム依存関係（ffmpeg）
   - `.streamlit/config.toml`: アプリ設定
   - `requirements.txt`: Python依存関係

#### その他のデプロイオプション

<details>
<summary>Railway でのデプロイ</summary>

1. [Railway](https://railway.app) にサインアップ
2. GitHubリポジトリを接続
3. 環境変数を設定（必要に応じて）
4. 自動デプロイ開始

</details>

<details>
<summary>Render でのデプロイ</summary>

1. [Render](https://render.com) にサインアップ
2. 「New Web Service」を選択
3. GitHubリポジトリを接続
4. ビルドコマンド: `pip install -r requirements.txt`
5. 起動コマンド: `streamlit run app.py --server.port $PORT`

</details>

## 🛡️ セキュリティ機能

- ✅ **URL検証**: YouTubeの正規URLのみ受付
- ⏱️ **タイムアウト制御**: 長時間処理の防止
- 📏 **ファイルサイズ制限**: 500MB上限
- ⏰ **動画時間制限**: 1時間上限
- 🧹 **一時ファイル管理**: 自動クリーンアップ

## ⚙️ 設定

### 制限値の変更

`app.py`の上部で制限値を調整できます：

```python
MAX_DURATION = 3600  # 最大動画時間（秒）
MAX_FILE_SIZE = 500 * 1024 * 1024  # 最大ファイルサイズ（バイト）
TIMEOUT = 300  # タイムアウト時間（秒）
```

### テーマのカスタマイズ

`.streamlit/config.toml`でUIテーマを変更できます。

## 📦 依存関係

- **streamlit**: Webアプリフレームワーク
- **pytube**: YouTubeダウンロードライブラリ
- **moviepy**: 動画編集ライブラリ
- **imageio-ffmpeg**: 動画コーデック

## 🔧 トラブルシューティング

### よくある問題

1. **"ダウンロードに失敗しました"**
   - 動画が削除されているか、プライベート設定の可能性
   - 異なるURLで再試行してください

2. **"マージに失敗しました"**
   - システムメモリ不足の可能性
   - より短い動画で試してください

3. **"ファイルサイズが大きすぎます"**
   - より低い解像度を選択してください
   - 音声のみのダウンロードを検討してください

### デプロイ時の問題

1. **ffmpeg関連エラー**
   - `packages.txt`に`ffmpeg`が含まれていることを確認
   - Streamlit Cloudの場合、自動でインストールされます

2. **メモリ不足エラー**
   - ファイルサイズ制限を下げてください
   - より小さなインスタンスタイプを使用してください

## ⚖️ 使用上の注意

- 著作権で保護されたコンテンツのダウンロードは法的に問題となる場合があります
- 個人的な使用に留め、再配布は避けてください
- YouTubeの利用規約を遵守してください

## 🤝 コントリビューション

改善提案やバグ報告は、GitHubのIssueからお願いします。

## 📄 ライセンス

このプロジェクトは教育目的で作成されています。商用利用については十分ご注意ください。

---

**開発者向け情報**

このアプリケーションは以下の改良が施されています：
- セキュリティ強化（URL検証、制限機能）
- エラーハンドリング改善
- モダンUIデザイン
- デプロイ最適化（設定ファイル、依存関係管理）
- パフォーマンス改善（メモリ管理、リソース解放）

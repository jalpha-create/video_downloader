import streamlit as st
from pytube import YouTube
import os
import tempfile
import re
import time
from urllib.parse import urlparse, parse_qs

# 設定
MAX_DURATION = 3600  # 最大1時間
MAX_FILE_SIZE = 500 * 1024 * 1024  # 500MB
TIMEOUT = 300  # 5分のタイムアウト

def is_valid_youtube_url(url):
    """YouTubeのURLが有効かチェック"""
    youtube_regex = re.compile(
        r'(https?://)?(www\.)?(youtube|youtu|youtube-nocookie)\.(com|be)/'
        r'(watch\?v=|embed/|v/|.+\?v=)?([^&=%\?]{11})'
    )
    return youtube_regex.match(url) is not None

def format_duration(seconds):
    """秒を時:分:秒の形式に変換"""
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    seconds = seconds % 60
    if hours > 0:
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
    else:
        return f"{minutes:02d}:{seconds:02d}"

def format_file_size(bytes_size):
    """バイトサイズを読みやすい形式に変換"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if bytes_size < 1024.0:
            return f"{bytes_size:.1f} {unit}"
        bytes_size /= 1024.0
    return f"{bytes_size:.1f} TB"

def create_youtube_object(url):
    """YouTubeオブジェクトを作成（User-Agent設定付き）"""
    try:
        # User-Agentを設定してブロックを回避
        yt = YouTube(
            url,
            use_oauth=False,
            allow_oauth_cache=False
        )
        return yt
    except Exception as e:
        st.error(f"YouTube接続エラー: {str(e)}")
        return None

def download_stream(stream, output_path):
    """ストリームをダウンロード"""
    try:
        start_time = time.time()
        file_path = stream.download(output_path=output_path)
        elapsed_time = time.time() - start_time
        
        if elapsed_time > TIMEOUT:
            raise TimeoutError("ダウンロードがタイムアウトしました")
            
        return file_path
    except Exception as e:
        st.error(f"ダウンロードに失敗しました: {str(e)}")
        return None

# Streamlitアプリの設定
st.set_page_config(
    page_title="YouTube Video Downloader",
    page_icon="📺",
    layout="wide"
)

# カスタムCSS
st.markdown("""
<style>
    .main-header {
        text-align: center;
        color: #ff4b4b;
        font-size: 3rem;
        margin-bottom: 2rem;
    }
    .info-box {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 10px;
        border-left: 5px solid #ff4b4b;
        margin: 1rem 0;
    }
    .warning-box {
        background-color: #fff3cd;
        padding: 1rem;
        border-radius: 10px;
        border-left: 5px solid #ffc107;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

# ヘッダー
st.markdown('<h1 class="main-header">📺 YouTube Video Downloader</h1>', unsafe_allow_html=True)

# 使用上の注意
st.markdown("""
<div class="warning-box">
⚠️ <strong>重要な注意事項</strong><br>
• 著作権で保護されたコンテンツのダウンロードは法的に問題となる場合があります<br>
• 個人的な使用に留め、再配布は避けてください<br>
• 最大ファイルサイズ: 500MB、最大時間: 1時間
</div>
""", unsafe_allow_html=True)

# デバッグ情報表示
st.info("🔧 デバッグ版：詳細なエラー情報を表示します")

# URL入力
url = st.text_input(
    "YouTubeのURLを入力してください", 
    placeholder="https://www.youtube.com/watch?v=...",
    help="YouTubeの動画URLを貼り付けてください"
)

if url:
    # URL検証
    if not is_valid_youtube_url(url):
        st.error("❌ 有効なYouTubeのURLを入力してください")
        st.stop()
    
    try:
        with st.spinner("動画情報を取得しています..."):
            st.info(f"🔍 接続中: {url}")
            yt = create_youtube_object(url)
            
            if not yt:
                st.error("❌ YouTube接続に失敗しました")
                st.stop()
            
            # 動画情報の取得を試行
            try:
                title = yt.title
                st.info(f"✅ タイトル取得成功: {title}")
            except Exception as e:
                st.error(f"❌ タイトル取得失敗: {str(e)}")
                st.stop()
            
            # 動画情報の表示
            col1, col2 = st.columns([1, 2])
            
            with col1:
                try:
                    st.image(yt.thumbnail_url, use_column_width=True)
                except Exception as e:
                    st.warning(f"サムネイル表示エラー: {str(e)}")
            
            with col2:
                st.subheader(yt.title)
                
                # 動画の詳細情報
                try:
                    st.markdown(f"""
                    <div class="info-box">
                    <strong>📊 動画情報</strong><br>
                    • 投稿者: {yt.author}<br>
                    • 再生時間: {format_duration(yt.length)}<br>
                    • 再生回数: {yt.views:,} 回<br>
                    • 投稿日: {yt.publish_date.strftime('%Y年%m月%d日') if yt.publish_date else 'N/A'}
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # 時間制限チェック
                    if yt.length > MAX_DURATION:
                        st.error(f"❌ 動画が長すぎます（最大{MAX_DURATION//60}分）")
                        st.stop()
                        
                except Exception as e:
                    st.warning(f"詳細情報取得エラー: {str(e)}")
        
        # ストリーム情報の取得と表示
        st.subheader("📥 ダウンロード形式を選択")
        
        try:
            # プログレッシブストリーム（音声+動画）のみ使用
            st.info("🔍 利用可能なストリームを検索中...")
            progressive_streams = yt.streams.filter(progressive=True, file_extension='mp4').order_by('resolution').desc()
            audio_streams = yt.streams.filter(only_audio=True).order_by('abr').desc()
            
            st.info(f"✅ プログレッシブストリーム: {len(progressive_streams)}個")
            st.info(f"✅ 音声ストリーム: {len(audio_streams)}個")
            
        except Exception as e:
            st.error(f"❌ ストリーム取得エラー: {str(e)}")
            st.stop()
        
        # ストリームオプションの作成
        stream_options = []
        
        # プログレッシブストリーム
        for stream in progressive_streams:
            try:
                size = format_file_size(stream.filesize) if hasattr(stream, 'filesize') and stream.filesize else "不明"
                stream_options.append((f"🎬 {stream.resolution} - 動画+音声 ({size})", stream))
            except Exception as e:
                st.warning(f"ストリーム情報取得エラー: {str(e)}")
        
        # 音声ストリーム
        for stream in audio_streams[:3]:  # 上位3つまで
            try:
                size = format_file_size(stream.filesize) if hasattr(stream, 'filesize') and stream.filesize else "不明"
                abr = stream.abr if hasattr(stream, 'abr') and stream.abr else "不明"
                stream_options.append((f"🎵 音声のみ - {abr} ({size})", stream))
            except Exception as e:
                st.warning(f"音声ストリーム情報取得エラー: {str(e)}")
        
        if not stream_options:
            st.error("❌ ダウンロード可能なストリームが見つかりませんでした")
            st.stop()
        
        st.success(f"✅ {len(stream_options)}個のダウンロードオプションが見つかりました")
        
        stream_dict = {option: stream for option, stream in stream_options}
        selected_option = st.selectbox(
            "品質を選択してください", 
            list(stream_dict.keys()),
            help="プログレッシブストリーム（動画+音声が一緒）のみ使用"
        )
        selected_stream = stream_dict[selected_option]
        
        # ファイルサイズチェック
        if hasattr(selected_stream, 'filesize') and selected_stream.filesize:
            if selected_stream.filesize > MAX_FILE_SIZE:
                st.error(f"❌ ファイルサイズが大きすぎます（最大{MAX_FILE_SIZE//1024//1024}MB）")
                st.stop()
        
        # ダウンロードボタン
        if st.button("⬇️ ダウンロード開始", type="primary", use_container_width=True):
            with tempfile.TemporaryDirectory() as temp_dir:
                title_safe = "".join([c if c.isalnum() or c in "._- " else "_" for c in yt.title])[:50]
                
                with st.spinner("ダウンロード中..."):
                    st.info(f"📁 一時フォルダ: {temp_dir}")
                    file_path = download_stream(selected_stream, temp_dir)
                    
                    if file_path:
                        st.success("✅ ダウンロード完了！")
                        st.info(f"📁 ファイルパス: {file_path}")
                        
                        with open(file_path, "rb") as file:
                            if "音声のみ" in selected_option:
                                file_extension = "mp3" if "mp3" in str(selected_stream.mime_type).lower() else "mp4"
                                st.download_button(
                                    "📥 音声ファイルをダウンロード",
                                    data=file,
                                    file_name=f"{title_safe}_audio.{file_extension}",
                                    mime=f"audio/{file_extension}",
                                    use_container_width=True
                                )
                            else:
                                st.download_button(
                                    "📥 動画ファイルをダウンロード",
                                    data=file,
                                    file_name=f"{title_safe}.mp4",
                                    mime="video/mp4",
                                    use_container_width=True
                                )
    
    except Exception as e:
        st.error(f"❌ エラーが発生しました: {str(e)}")
        st.error(f"🔍 エラータイプ: {type(e).__name__}")
        import traceback
        st.error(f"🔍 詳細エラー: {traceback.format_exc()}")
        st.info("💡 別のURLを試すか、しばらく時間をおいてから再試行してください")

# フッター
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #666; margin-top: 2rem;">
⚠️ このツールは教育目的で作成されています。著作権を尊重してご利用ください。
</div>
""", unsafe_allow_html=True) 
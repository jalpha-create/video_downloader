import streamlit as st
import yt_dlp
import os
import tempfile
import re
import time
from urllib.parse import urlparse, parse_qs
import json

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
    if not bytes_size:
        return "不明"
    for unit in ['B', 'KB', 'MB', 'GB']:
        if bytes_size < 1024.0:
            return f"{bytes_size:.1f} {unit}"
        bytes_size /= 1024.0
    return f"{bytes_size:.1f} TB"

def get_video_info(url):
    """yt-dlpで動画情報を取得"""
    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
        'extract_flat': False,
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            return info
    except Exception as e:
        st.error(f"動画情報取得エラー: {str(e)}")
        return None

def download_video(url, format_id, output_path):
    """yt-dlpで動画をダウンロード"""
    try:
        ydl_opts = {
            'format': format_id,
            'outtmpl': os.path.join(output_path, '%(title)s.%(ext)s'),
            'quiet': True,
            'no_warnings': True,
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
            
        # ダウンロードされたファイルを見つける
        for file in os.listdir(output_path):
            if file.endswith(('.mp4', '.webm', '.mkv', '.mp3', '.m4a')):
                return os.path.join(output_path, file)
        
        return None
    except Exception as e:
        st.error(f"ダウンロードエラー: {str(e)}")
        return None

# Streamlitアプリの設定
st.set_page_config(
    page_title="YouTube Video Downloader (yt-dlp)",
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
    .success-box {
        background-color: #d4edda;
        padding: 1rem;
        border-radius: 10px;
        border-left: 5px solid #28a745;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

# ヘッダー
st.markdown('<h1 class="main-header">📺 YouTube Video Downloader</h1>', unsafe_allow_html=True)
st.markdown('<p style="text-align: center; color: #666;">⚡ yt-dlp powered - 高安定性版</p>', unsafe_allow_html=True)

# 使用上の注意
st.markdown("""
<div class="warning-box">
⚠️ <strong>重要な注意事項</strong><br>
• 著作権で保護されたコンテンツのダウンロードは法的に問題となる場合があります<br>
• 個人的な使用に留め、再配布は避けてください<br>
• 最大ファイルサイズ: 500MB、最大時間: 1時間
</div>
""", unsafe_allow_html=True)

# 改良情報
st.markdown("""
<div class="success-box">
✅ <strong>yt-dlp版の特徴</strong><br>
• YouTubeの仕様変更に強い • 高品質ダウンロード対応 • 豊富な形式オプション • 安定性重視
</div>
""", unsafe_allow_html=True)

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
    
    with st.spinner("動画情報を取得しています..."):
        st.info(f"🔍 yt-dlpで接続中: {url}")
        info = get_video_info(url)
        
        if not info:
            st.error("❌ 動画情報の取得に失敗しました")
            st.stop()
        
        st.success("✅ 動画情報取得成功！")
    
    # 動画情報の表示
    col1, col2 = st.columns([1, 2])
    
    with col1:
        if 'thumbnail' in info:
            st.image(info['thumbnail'], use_column_width=True)
    
    with col2:
        st.subheader(info.get('title', 'タイトル不明'))
        
        # 動画の詳細情報
        duration = info.get('duration', 0)
        uploader = info.get('uploader', '不明')
        view_count = info.get('view_count', 0)
        upload_date = info.get('upload_date', '')
        
        # 時間制限チェック
        if duration and duration > MAX_DURATION:
            st.error(f"❌ 動画が長すぎます（最大{MAX_DURATION//60}分）")
            st.stop()
        
        # 投稿日の整形
        formatted_date = f"{upload_date[:4]}-{upload_date[4:6]}-{upload_date[6:8]}" if upload_date else '不明'
        
        st.markdown(f"""
        <div class="info-box">
        <strong>📊 動画情報</strong><br>
        • 投稿者: {uploader}<br>
        • 再生時間: {format_duration(duration) if duration else '不明'}<br>
        • 再生回数: {view_count:,} 回<br>
        • 投稿日: {formatted_date}
        </div>
        """, unsafe_allow_html=True)
    
    # フォーマット情報の取得
    st.subheader("📥 ダウンロード形式を選択")
    
    formats = info.get('formats', [])
    if not formats:
        st.error("❌ ダウンロード可能なフォーマットが見つかりませんでした")
        st.stop()
    
    # フォーマットオプションの作成
    format_options = []
    
    # 動画フォーマット（音声付き）
    for fmt in formats:
        if fmt.get('vcodec') != 'none' and fmt.get('acodec') != 'none':
            ext = fmt.get('ext', 'mp4')
            quality = fmt.get('format_note', fmt.get('height', '不明'))
            filesize = fmt.get('filesize') or fmt.get('filesize_approx')
            size_str = format_file_size(filesize) if filesize else "不明"
            
            if quality != '不明':
                format_options.append((
                    f"🎬 {quality}p - {ext.upper()} ({size_str})",
                    fmt['format_id']
                ))
    
    # 音声のみフォーマット
    for fmt in formats:
        if fmt.get('vcodec') == 'none' and fmt.get('acodec') != 'none':
            ext = fmt.get('ext', 'mp3')
            quality = fmt.get('format_note', fmt.get('abr', '不明'))
            filesize = fmt.get('filesize') or fmt.get('filesize_approx')
            size_str = format_file_size(filesize) if filesize else "不明"
            
            format_options.append((
                f"🎵 音声のみ - {quality} {ext.upper()} ({size_str})",
                fmt['format_id']
            ))
            break  # 1つの音声フォーマットのみ表示
    
    if not format_options:
        st.error("❌ 利用可能なフォーマットが見つかりませんでした")
        st.stop()
    
    st.success(f"✅ {len(format_options)}個のダウンロードオプションが見つかりました")
    
    # フォーマット選択
    format_dict = {option: format_id for option, format_id in format_options}
    selected_option = st.selectbox(
        "品質を選択してください", 
        list(format_dict.keys()),
        help="yt-dlpによる高品質ダウンロード"
    )
    selected_format = format_dict[selected_option]
    
    # ダウンロードボタン
    if st.button("⬇️ ダウンロード開始", type="primary", use_container_width=True):
        with tempfile.TemporaryDirectory() as temp_dir:
            with st.spinner("yt-dlpでダウンロード中..."):
                st.info(f"📁 フォーマット: {selected_format}")
                file_path = download_video(url, selected_format, temp_dir)
                
                if file_path and os.path.exists(file_path):
                    st.success("✅ ダウンロード完了！")
                    st.info(f"📁 ファイル: {os.path.basename(file_path)}")
                    
                    with open(file_path, "rb") as file:
                        file_data = file.read()
                        file_name = os.path.basename(file_path)
                        
                        # MIMEタイプの決定
                        if file_name.endswith(('.mp4', '.webm', '.mkv')):
                            mime_type = "video/mp4"
                        elif file_name.endswith(('.mp3', '.m4a')):
                            mime_type = "audio/mpeg"
                        else:
                            mime_type = "application/octet-stream"
                        
                        st.download_button(
                            "📥 ファイルをダウンロード",
                            data=file_data,
                            file_name=file_name,
                            mime=mime_type,
                            use_container_width=True
                        )
                else:
                    st.error("❌ ダウンロードに失敗しました")

# フッター
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #666; margin-top: 2rem;">
⚠️ このツールは教育目的で作成されています。著作権を尊重してご利用ください。<br>
🚀 Powered by yt-dlp - より安定した YouTube ダウンロード体験
</div>
""", unsafe_allow_html=True) 
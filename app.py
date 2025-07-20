import streamlit as st
from pytube import YouTube
import os
import tempfile
import re
import time
from moviepy.editor import VideoFileClip, AudioFileClip
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

def download_stream(stream, output_path, progress_bar=None):
    """ストリームをダウンロード（プログレスバー付き）"""
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

def merge_audio_video(video_path, audio_path, output_path, progress_callback=None):
    """動画と音声をマージ"""
    try:
        with st.spinner("動画と音声をマージしています..."):
            video_clip = VideoFileClip(video_path)
            audio_clip = AudioFileClip(audio_path)
            final_clip = video_clip.set_audio(audio_clip)
            
            # プログレスコールバック付きで書き出し
            final_clip.write_videofile(
                output_path, 
                codec='libx264',
                audio_codec='aac',
                verbose=False,
                logger=None
            )
            
            # リソースを解放
            video_clip.close()
            audio_clip.close()
            final_clip.close()
            
        return output_path
    except Exception as e:
        st.error(f"マージに失敗しました: {str(e)}")
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
            yt = YouTube(url)
            
            # 動画情報の表示
            col1, col2 = st.columns([1, 2])
            
            with col1:
                st.image(yt.thumbnail_url, use_column_width=True)
            
            with col2:
                st.subheader(yt.title)
                
                # 動画の詳細情報
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
        
        # ストリーム情報の取得と表示
        st.subheader("📥 ダウンロード形式を選択")
        
        # プログレッシブストリーム（音声+動画）
        progressive_streams = yt.streams.filter(progressive=True, file_extension='mp4').order_by('resolution').desc()
        
        # 適応的ストリーム（音声なし動画）
        adaptive_streams = yt.streams.filter(adaptive=True, file_extension='mp4', only_video=True).order_by('resolution').desc()
        
        # 音声ストリーム
        audio_streams = yt.streams.filter(only_audio=True).order_by('abr').desc()
        
        # ストリームオプションの作成（ファイルサイズ情報付き）
        stream_options = []
        
        # プログレッシブストリーム
        for stream in progressive_streams:
            size = format_file_size(stream.filesize) if hasattr(stream, 'filesize') and stream.filesize else "不明"
            stream_options.append((f"🎬 {stream.resolution} - 動画+音声 ({size})", stream))
        
        # 適応的ストリーム（高品質）
        for stream in adaptive_streams[:3]:  # 上位3つまで
            size = format_file_size(stream.filesize) if hasattr(stream, 'filesize') and stream.filesize else "不明"
            stream_options.append((f"🎥 {stream.resolution} - 高品質動画 ({size})", stream))
        
        # 音声ストリーム
        for stream in audio_streams[:2]:  # 上位2つまで
            size = format_file_size(stream.filesize) if hasattr(stream, 'filesize') and stream.filesize else "不明"
            abr = stream.abr if hasattr(stream, 'abr') and stream.abr else "不明"
            stream_options.append((f"🎵 音声のみ - {abr} ({size})", stream))
        
        if not stream_options:
            st.error("❌ ダウンロード可能なストリームが見つかりませんでした")
            st.stop()
        
        stream_dict = {option: stream for option, stream in stream_options}
        selected_option = st.selectbox(
            "品質を選択してください", 
            list(stream_dict.keys()),
            help="高品質動画は音声と動画を別々にダウンロードしてマージします"
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
                
                if "動画+音声" in selected_option:
                    # プログレッシブストリームのダウンロード
                    with st.spinner("ダウンロード中..."):
                        progress_bar = st.progress(0)
                        file_path = download_stream(selected_stream, temp_dir, progress_bar)
                        
                        if file_path:
                            progress_bar.progress(100)
                            st.success("✅ ダウンロード完了！")
                            
                            with open(file_path, "rb") as file:
                                st.download_button(
                                    "📥 ファイルをダウンロード",
                                    data=file,
                                    file_name=f"{title_safe}.mp4",
                                    mime="video/mp4",
                                    use_container_width=True
                                )
                
                elif "高品質動画" in selected_option:
                    # 適応的ストリームのダウンロード（動画+音声）
                    with st.spinner("高品質動画をダウンロード中..."):
                        video_file = download_stream(selected_stream, temp_dir)
                        
                        if video_file:
                            st.info("🎵 音声ファイルをダウンロード中...")
                            best_audio = audio_streams.first()
                            audio_file = download_stream(best_audio, temp_dir)
                            
                            if audio_file:
                                st.info("🔄 動画と音声をマージ中...")
                                output_path = os.path.join(temp_dir, f"{title_safe}_merged.mp4")
                                merged_file = merge_audio_video(video_file, audio_file, output_path)
                                
                                if merged_file:
                                    st.success("✅ マージ完了！")
                                    
                                    with open(merged_file, "rb") as mf:
                                        st.download_button(
                                            "📥 高品質動画をダウンロード",
                                            data=mf,
                                            file_name=f"{title_safe}_HQ.mp4",
                                            mime="video/mp4",
                                            use_container_width=True
                                        )
                
                else:
                    # 音声のみのダウンロード
                    with st.spinner("音声をダウンロード中..."):
                        audio_file = download_stream(selected_stream, temp_dir)
                        
                        if audio_file:
                            st.success("✅ 音声ダウンロード完了！")
                            
                            with open(audio_file, "rb") as af:
                                # 音声ファイルはMP3として保存
                                file_extension = "mp3" if "mp3" in str(selected_stream.mime_type).lower() else "mp4"
                                st.download_button(
                                    "📥 音声ファイルをダウンロード",
                                    data=af,
                                    file_name=f"{title_safe}_audio.{file_extension}",
                                    mime=f"audio/{file_extension}",
                                    use_container_width=True
                                )
    
    except Exception as e:
        st.error(f"❌ エラーが発生しました: {str(e)}")
        st.info("💡 別のURLを試すか、しばらく時間をおいてから再試行してください")

# フッター
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #666; margin-top: 2rem;">
⚠️ このツールは教育目的で作成されています。著作権を尊重してご利用ください。
</div>
""", unsafe_allow_html=True)

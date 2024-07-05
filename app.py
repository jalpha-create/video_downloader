import streamlit as st
from pytube import YouTube
import os
import tempfile
from moviepy.editor import VideoFileClip, AudioFileClip

def download_stream(stream, output_path):
    try:
        return stream.download(output_path=output_path)
    except Exception as e:
        st.error(f"Download failed: {str(e)}")
        return None

def merge_audio_video(video_path, audio_path, output_path):
    try:
        video_clip = VideoFileClip(video_path)
        audio_clip = AudioFileClip(audio_path)
        final_clip = video_clip.set_audio(audio_clip)
        final_clip.write_videofile(output_path, codec='libx264')
        return output_path
    except Exception as e:
        st.error(f"Merging failed: {str(e)}")
        return None

st.title("YouTube Video Downloader")
url = st.text_input("Enter YouTube URL")

if url:
    try:
        yt = YouTube(url)
        st.subheader(f"Title: {yt.title}")
        st.image(yt.thumbnail_url, width=300)
        
        # プログレッシブストリーム（音声+動画）
        progressive_streams = yt.streams.filter(progressive=True, file_extension='mp4').order_by('resolution').desc()
        
        # 適応的ストリーム（音声なし動画）
        adaptive_streams = yt.streams.filter(adaptive=True, file_extension='mp4', only_video=True).order_by('resolution').desc()
        
        # 音声ストリーム
        audio_streams = yt.streams.filter(only_audio=True).order_by('abr').desc()
        
        # ストリームオプションの作成
        stream_options = [(f"{stream.resolution} - Video (Progressive)", stream) for stream in progressive_streams]
        stream_options += [(f"{stream.resolution} - Video (Adaptive)", stream) for stream in adaptive_streams]
        stream_options += [(f"Audio Only - {stream.abr}", stream) for stream in audio_streams[:2]]  # Top 2 audio options
        
        stream_dict = {option: stream for option, stream in stream_options}
        selected_option = st.selectbox("Select resolution or audio", list(stream_dict.keys()))
        selected_stream = stream_dict[selected_option]
        
        st.write("Select the resolution or audio quality for downloading the video or audio.")
        
        if st.button("Download"):
            with tempfile.TemporaryDirectory() as temp_dir:
                with st.spinner("Downloading..."):
                    title_safe = "".join([c if c.isalnum() else "_" for c in yt.title])
                    
                    if "Progressive" in selected_option:
                        # プログレッシブストリームのダウンロード
                        file_path = download_stream(selected_stream, temp_dir)
                        if file_path:
                            st.success("Download complete!")
                            with open(file_path, "rb") as file:
                                st.download_button(
                                    "Download Video",
                                    data=file,
                                    file_name=f"{title_safe}.mp4",
                                    mime="video/mp4"
                                )
                    elif "Adaptive" in selected_option:
                        # 適応的ストリームのダウンロード（動画+音声）
                        video_file = download_stream(selected_stream, temp_dir)
                        best_audio = audio_streams.first()
                        audio_file = download_stream(best_audio, temp_dir)
                        if video_file and audio_file:
                            st.success("Video and audio downloaded separately. Merging them now...")
                            output_path = os.path.join(temp_dir, f"{title_safe}_merged.mp4")
                            merged_file = merge_audio_video(video_file, audio_file, output_path)
                            if merged_file:
                                st.success("Merging complete!")
                                with open(merged_file, "rb") as mf:
                                    st.download_button(
                                        "Download Merged Video",
                                        data=mf,
                                        file_name=f"{title_safe}_merged.mp4",
                                        mime="video/mp4"
                                    )
                    else:
                        # 音声のみのダウンロード
                        audio_file = download_stream(selected_stream, temp_dir)
                        if audio_file:
                            st.success("Audio download complete!")
                            with open(audio_file, "rb") as af:
                                st.download_button(
                                    "Download Audio",
                                    data=af,
                                    file_name=f"{title_safe}.mp4",
                                    mime="audio/mp4"
                                )
    except Exception as e:
        st.error(f"An error occurred: {str(e)}")

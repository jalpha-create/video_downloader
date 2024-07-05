import streamlit as st
from pytube import YouTube
import os
from moviepy.editor import AudioFileClip
from pathlib import Path

def download_video(stream, output_path):
    return stream.download(output_path=output_path)

def convert_to_mp3(mp4_path, mp3_path):
    audio_clip = AudioFileClip(mp4_path)
    audio_clip.write_audiofile(mp3_path)
    audio_clip.close()

# ユーザーのダウンロードフォルダを取得
download_folder = str(Path.home() / "Downloads")

st.title("YouTube Video Downloader")

url = st.text_input("Enter YouTube URL")

if url:
    yt = YouTube(url)
    st.subheader(f"Title: {yt.title}")
    st.image(yt.thumbnail_url, width=300)

    video_streams = yt.streams.filter(file_extension='mp4', adaptive=True).all()
    audio_streams = yt.streams.filter(file_extension='mp4', only_audio=True).all()

    stream_options = [(stream.resolution or "Audio Only", stream) for stream in video_streams + audio_streams]
    stream_dict = {f"{res} - {stream.mime_type}": stream for res, stream in stream_options}
    
    selected_options = st.multiselect("Select resolutions or audio", list(stream_dict.keys()))

    if st.button("Download"):
        if selected_options:
            with st.spinner("Downloading..."):
                for option in selected_options:
                    selected_stream = stream_dict[option]
                    filepath = download_video(selected_stream, output_path=download_folder)
                    if filepath:
                        if "audio" in selected_stream.mime_type:
                            mp3_path = os.path.splitext(filepath)[0] + ".mp3"
                            convert_to_mp3(filepath, mp3_path)
                            os.remove(filepath)  # Remove the original mp4 file
                            filepath = mp3_path
                        st.success(f"Download complete for {option}!")
                        st.write("Downloaded file:", filepath)
                        with open(filepath, "rb") as file:
                            st.download_button("Download File", data=file, file_name=os.path.basename(filepath), mime="audio/mp3" if "audio" in selected_stream.mime_type else "video/mp4")
        else:
            st.error("No resolution or audio selected.")
else:
    st.error("Please enter a valid YouTube URL.")
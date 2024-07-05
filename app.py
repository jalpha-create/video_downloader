import streamlit as st
from pytube import YouTube
import os
from tkinter import Tk
from tkinter.filedialog import askdirectory
from moviepy.editor import AudioFileClip

def download_video(url, stream, save_path):
    return stream.download(output_path=save_path)

def convert_to_mp3(mp4_path, mp3_path):
    audio_clip = AudioFileClip(mp4_path)
    audio_clip.write_audiofile(mp3_path)
    audio_clip.close()

st.title("YouTube Video Downloader")

url = st.text_input("Enter YouTube URL")

if url:
    yt = YouTube(url)
    st.subheader(f"Title: {yt.title}")
    st.image(yt.thumbnail_url, width=300)

    video_streams = yt.streams.filter(progressive=True, file_extension='mp4').all()
    audio_streams = yt.streams.filter(only_audio=True, file_extension='mp4').all()

    stream_options = [(stream.resolution or "Audio Only", stream) for stream in video_streams + audio_streams]
    stream_dict = {f"{res} - {stream.mime_type}": stream for res, stream in stream_options}
    
    selected_option = st.selectbox("Select resolution or audio", list(stream_dict.keys()))
    selected_stream = stream_dict[selected_option]

    if st.button("Download"):
        root = Tk()
        root.withdraw()  # Hide the main window
        save_path = askdirectory()  # Open the directory chooser dialog
        root.destroy()
        
        if save_path:
            with st.spinner("Downloading..."):
                filepath = download_video(url, selected_stream, save_path)
                if filepath:
                    if "audio" in selected_stream.mime_type:
                        mp3_path = os.path.splitext(filepath)[0] + ".mp3"
                        convert_to_mp3(filepath, mp3_path)
                        os.remove(filepath)  # Remove the original mp4 file
                        filepath = mp3_path
                    st.success("Download complete!")
                    st.write("Downloaded file:", filepath)
                    with open(filepath, "rb") as file:
                        st.download_button("Download File", data=file, file_name=os.path.basename(filepath), mime="audio/mp3" if "audio" in selected_stream.mime_type else "video/mp4")
        else:
            st.error("No directory selected.")
import streamlit as st
import os
import glob

# MoviePy Imports
from moviepy.editor import (
    ImageClip,
    concatenate_videoclips,
    AudioFileClip
)

import yt_dlp

# -----------------------------
# SESSION STATE
# -----------------------------
if 'audio_path' not in st.session_state:
    st.session_state['audio_path'] = None

if 'yt_error' not in st.session_state:
    st.session_state['yt_error'] = None


# -----------------------------
# CLEANUP FUNCTION
# -----------------------------
def cleanup_temp_files():
    """Remove temporary files."""

    files = glob.glob("temp_*") + ["output_video.mp4"]

    for f in files:
        try:
            os.remove(f)
        except:
            pass

    st.session_state['audio_path'] = None
    st.session_state['yt_error'] = None


# -----------------------------
# YOUTUBE AUDIO DOWNLOAD
# -----------------------------
def download_youtube_audio(url):
    """Download audio from YouTube."""

    audio_opts = {
        'format': 'bestaudio/best',
        'outtmpl': 'temp_audio.%(ext)s',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'quiet': True
    }

    with yt_dlp.YoutubeDL(audio_opts) as ydl:
        ydl.download([url])

    return "temp_audio.mp3"


def handle_youtube_download(url):
    """Handle YouTube download."""

    try:
        st.session_state['yt_error'] = None

        result_path = download_youtube_audio(url)

        if result_path:
            st.session_state['audio_path'] = result_path

    except Exception as e:
        st.session_state['yt_error'] = str(e)


# -----------------------------
# VIDEO CREATION FUNCTION
# -----------------------------
def create_video(image_files, duplicate_count, fps, audio_path):
    """Create video from images and audio."""

    clips = []

    duration_per_image = duplicate_count / fps

    target_resolution = (1280, 720)

    for idx, img_file in enumerate(image_files):

        temp_img_path = f"temp_img_{idx}.png"

        with open(temp_img_path, "wb") as f:
            f.write(img_file.getbuffer())

        # Create image clip
        clip = ImageClip(temp_img_path)

        # Set duration
        clip = clip.set_duration(duration_per_image)

        # Resize image
        clip = clip.resize(target_resolution)

        clips.append(clip)

    # Merge all clips
    final_video = concatenate_videoclips(
        clips,
        method="compose"
    )

    # Set FPS
    final_video = final_video.set_fps(fps)

    # Add audio
    audio_clip = AudioFileClip(audio_path)

    # Trim audio if longer than video
    if audio_clip.duration > final_video.duration:
        audio_clip = audio_clip.subclip(
            0,
            final_video.duration
        )

    # Attach audio
    final_clip = final_video.set_audio(audio_clip)

    output_filename = "output_video.mp4"

    # Export video
    final_clip.write_videofile(
        output_filename,
        codec="libx264",
        audio_codec="aac"
    )

    return output_filename


# -----------------------------
# STREAMLIT PAGE CONFIG
# -----------------------------
st.set_page_config(
    page_title="PragyanAI Video Creator",
    layout="wide"
)

# -----------------------------
# LOGO
# -----------------------------
if os.path.exists("BMW.jpg"):
    st.image("BMW.jpg", width=250)

# -----------------------------
# TITLE
# -----------------------------
st.title("PragyanAI - Multimedia Merger")

st.markdown(
    """
    Upload multiple images, set timing,
    and merge them with audio from:
    
    - Uploaded audio file
    - YouTube URL
    """
)

# -----------------------------
# SIDEBAR
# -----------------------------
with st.sidebar:

    st.header("Video Settings")

    fps = st.slider(
        "Frames Per Second (FPS)",
        min_value=1,
        max_value=60,
        value=24
    )

    duplicates = st.number_input(
        "Frames per Image",
        min_value=1,
        value=48
    )

    if st.button("Clear Cache & Temp Files"):
        cleanup_temp_files()
        st.success("Temporary files cleared.")
        st.rerun()

# -----------------------------
# MAIN LAYOUT
# -----------------------------
col1, col2 = st.columns(2)

# -----------------------------
# IMAGE SECTION
# -----------------------------
with col1:

    st.subheader("1. Upload Images")

    uploaded_images = st.file_uploader(
        "Upload Image Sequence",
        type=["jpg", "jpeg", "png"],
        accept_multiple_files=True
    )

# -----------------------------
# AUDIO SECTION
# -----------------------------
with col2:

    st.subheader("2. Add Audio")

    uploaded_audio = st.file_uploader(
        "Upload Audio File",
        type=["mp3", "wav"]
    )

    st.markdown("### OR")

    youtube_url = st.text_input(
        "Paste YouTube URL"
    )

    if st.button("Download YouTube Audio"):

        if youtube_url:
            with st.spinner("Downloading audio..."):
                handle_youtube_download(youtube_url)

            if st.session_state['audio_path']:
                st.success("YouTube audio downloaded successfully!")

    if st.session_state['yt_error']:
        st.error(st.session_state['yt_error'])

# -----------------------------
# VIDEO GENERATION
# -----------------------------
st.subheader("3. Create Video")

if st.button("Generate Video"):

    if not uploaded_images:
        st.warning("Please upload images first.")

    else:

        audio_path = None

        # Uploaded audio
        if uploaded_audio:

            audio_path = "temp_uploaded_audio.mp3"

            with open(audio_path, "wb") as f:
                f.write(uploaded_audio.read())

        # YouTube audio
        elif st.session_state['audio_path']:

            audio_path = st.session_state['audio_path']

        else:
            st.warning(
                "Please upload audio or download from YouTube."
            )

        if audio_path:

            with st.spinner("Creating video... Please wait."):

                output_video = create_video(
                    uploaded_images,
                    duplicates,
                    fps,
                    audio_path
                )

            st.success("Video Created Successfully!")

            # Display video
            st.video(output_video)

            # Download button
            with open(output_video, "rb") as file:

                st.download_button(
                    label="Download Video",
                    data=file,
                    file_name="output_video.mp4",
                    mime="video/mp4"
                )

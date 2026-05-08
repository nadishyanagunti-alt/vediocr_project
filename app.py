import streamlit as st
import os
import glob
import yt_dlp

# FIXED MOVIEPY IMPORT
from moviepy.video.io.ImageSequenceClip import ImageSequenceClip
from moviepy.audio.io.AudioFileClip import AudioFileClip


# --------------------------
# SESSION STATE
# --------------------------
if 'audio_path' not in st.session_state:
    st.session_state['audio_path'] = None

if 'yt_error' not in st.session_state:
    st.session_state['yt_error'] = None


# --------------------------
# CLEANUP
# --------------------------
def cleanup_temp_files():

    files = glob.glob("temp_*") + ["output_video.mp4"]

    for f in files:
        try:
            os.remove(f)
        except:
            pass

    st.session_state['audio_path'] = None
    st.session_state['yt_error'] = None


# --------------------------
# YOUTUBE DOWNLOAD
# --------------------------
def download_youtube_audio(url):

    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': 'temp_audio.%(ext)s',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])

    return "temp_audio.mp3"


def handle_youtube_download(url):

    try:
        st.session_state['yt_error'] = None

        audio_path = download_youtube_audio(url)

        st.session_state['audio_path'] = audio_path

    except Exception as e:
        st.session_state['yt_error'] = str(e)


# --------------------------
# VIDEO CREATION
# --------------------------
def create_video(image_files, fps, audio_path):

    image_paths = []

    for idx, img in enumerate(image_files):

        img_path = f"temp_img_{idx}.png"

        with open(img_path, "wb") as f:
            f.write(img.getbuffer())

        image_paths.append(img_path)

    # CREATE VIDEO
    clip = ImageSequenceClip(image_paths, fps=fps)

    # ADD AUDIO
    audio = AudioFileClip(audio_path)

    # CUT AUDIO IF NEEDED
    if audio.duration > clip.duration:
        audio = audio.subclip(0, clip.duration)

    final_clip = clip.set_audio(audio)

    output_path = "output_video.mp4"

    final_clip.write_videofile(
        output_path,
        codec="libx264",
        audio_codec="aac"
    )

    return output_path


# --------------------------
# PAGE CONFIG
# --------------------------
st.set_page_config(
    page_title="PragyanAI Video Creator",
    layout="wide"
)

# --------------------------
# LOGO
# --------------------------
if os.path.exists("BMW.jpg"):
    st.image("BMW.jpg", width=250)

# --------------------------
# TITLE
# --------------------------
st.title("PragyanAI - Multimedia Merger")

st.write(
    "Upload images and merge them with audio "
    "from file or YouTube."
)

# --------------------------
# SIDEBAR
# --------------------------
with st.sidebar:

    st.header("Settings")

    fps = st.slider(
        "FPS",
        1,
        60,
        24
    )

    if st.button("Clear Temp Files"):
        cleanup_temp_files()
        st.success("Files Cleared")
        st.rerun()

# --------------------------
# MAIN LAYOUT
# --------------------------
col1, col2 = st.columns(2)

# --------------------------
# IMAGE UPLOAD
# --------------------------
with col1:

    st.subheader("1. Upload Images")

    uploaded_images = st.file_uploader(
        "Upload Images",
        type=["jpg", "jpeg", "png"],
        accept_multiple_files=True
    )

# --------------------------
# AUDIO
# --------------------------
with col2:

    st.subheader("2. Audio")

    uploaded_audio = st.file_uploader(
        "Upload Audio",
        type=["mp3", "wav"]
    )

    youtube_url = st.text_input(
        "Or Enter YouTube URL"
    )

    if st.button("Download YouTube Audio"):

        if youtube_url:

            with st.spinner("Downloading..."):
                handle_youtube_download(youtube_url)

            if st.session_state['audio_path']:
                st.success("Audio Downloaded")

    if st.session_state['yt_error']:
        st.error(st.session_state['yt_error'])

# --------------------------
# GENERATE VIDEO
# --------------------------
st.subheader("3. Generate Video")

if st.button("Generate Video"):

    if not uploaded_images:

        st.warning("Please upload images")

    else:

        audio_path = None

        # AUDIO FILE
        if uploaded_audio:

            audio_path = "temp_uploaded_audio.mp3"

            with open(audio_path, "wb") as f:
                f.write(uploaded_audio.read())

        # YOUTUBE AUDIO
        elif st.session_state['audio_path']:

            audio_path = st.session_state['audio_path']

        else:
            st.warning("Please add audio")

        if audio_path:

            with st.spinner("Creating Video..."):

                output_video = create_video(
                    uploaded_images,
                    fps,
                    audio_path
                )

            st.success("Video Created Successfully!")

            st.video(output_video)

            with open(output_video, "rb") as file:

                st.download_button(
                    label="Download Video",
                    data=file,
                    file_name="output_video.mp4",
                    mime="video/mp4"
                )

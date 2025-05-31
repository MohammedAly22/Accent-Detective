import streamlit as st
from accent_detector import AccentDetector
from utils import create_accents_chart, create_confidence_bar


st.set_page_config(
    page_title="Accent Detective", page_icon="🎙️", initial_sidebar_state="expanded"
)

# Set custom CSS styling
with open("style.css") as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)


# Instantiate `AccentDetector` object
detector = AccentDetector()

# Sidebar
with st.sidebar:
    st.header("💡 Tips")
    st.success(
        "📹 Video Quality - Clear audio with minimal background noise works best"
    )
    st.success("⏱️ Duration - 30 seconds to 5 minutes is optimal for analysis")
    st.success("🗣️ Speech - Natural conversation or monologue works better than reading")

# Main content
st.header("🎬 Input Source")

# Input method selection
input_method = st.radio(
    "Choose input method:", ["📎 Upload Your File", "🔗 Video URL"], horizontal=True
)

video_input = None
if input_method == "📎 Upload Your File":
    video_input = st.file_uploader(
        "Upload your file",
        type=["mp4", "mov", "avi", "mkv", "webm", "mp3", "wav", "m4a"],
        help="Supported formats: MP4, MOV, AVI, MKV, WebM, MP3, WAV, M4A",
    )
else:
    video_input = st.text_input(
        "Enter video URL",
        placeholder="https://www.loom.com/share/... or direct video link",
        help="Supports YouTube, Loom, direct video links, and more",
    )

if st.button("Analyze Accent", type="primary", use_container_width=True):
    if video_input:
        results = detector.process_video(video_input)
        if results:
            st.session_state["results"] = results
            st.success("✅ Analysis completed successfully!")
        else:
            st.error(
                "❌ Failed to process the video. Please check your input and try again."
            )
    else:
        st.warning("⚠️ Please provide a video file or URL first.")


# Display results
if "results" in st.session_state:
    results = st.session_state["results"]

    # Transcript
    st.subheader("📜 Transcript", anchor=False)
    st.info(results["transcript"])

    # Main results
    st.write("---")
    st.subheader("📊 Analysis Results", anchor=False)

    if results["language"] == "en":
        # Create accent visualizations
        fig = create_accents_chart(results["accent_scores"])
        st.plotly_chart(fig, use_container_width=True)

        st.subheader(
            f"🌍 Detected Accent: `{results['predicted_accent']}`", anchor=False
        )
        st.markdown(
            create_confidence_bar(results["confidence"]), unsafe_allow_html=True
        )

        st.write("---")

        st.subheader("📝 Summary", anchor=False)
        st.markdown(
            f"""
            **🎬 Title:** {results.get('title', 'Unknown')}
            
            **🌐 Language:** `{results.get('language', 'Unknown').upper()}`
            
            **🎯 Primary Accent:** {results.get('predicted_accent', 'Unknown')}
            
            **📊 Confidence:** {results.get('confidence', 0):.2f}%
            
            **⭐ Quality:** {'Excellent' if results.get("confidence", 0) > 80 else 'Good' if results.get("confidence", 0) > 60 else 'Fair'} 
            """
        )
    else:
        st.warning(
            f"⚠️ Detected another language **{results['language'].upper()}** instead of **English**!"
        )

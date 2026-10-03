import streamlit as st
import sys
import os

# Ensure sam_agent path is accessible
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from core.router import SamRouter

st.set_page_config(page_title="Sam", layout="centered")

# Custom CSS to match the minimal 3D design
st.markdown("""
    <style>
    /* Hide top right buttons (Deploy, GitHub, etc.) except the 3 dots */
    .stAppDeployButton {display: none !important;}
    [data-testid="stHeaderActionElements"] {display: none !important;}
    
    /* Lock text chat input to the bottom */
    .stChatInput {position: fixed; bottom: 3rem;}
    
    /* 3D Orb Styling */
    .orb-container {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        margin-top: 4rem;
        margin-bottom: 2rem;
    }
    .pulse-orb {
        width: 80px; 
        height: 80px;
        /* 3D Sphere lighting effect */
        background: radial-gradient(circle at 35% 35%, #4ade80, #166534, #062111);
        border-radius: 50%;
        box-shadow: 
            0 10px 25px rgba(22, 101, 52, 0.5), 
            inset 0 -10px 20px rgba(0, 0, 0, 0.6),
            inset 0 10px 20px rgba(255, 255, 255, 0.4);
        animation: pulse 3s infinite ease-in-out;
    }
    
    @keyframes pulse {
        0% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(74, 222, 128, 0.4); }
        50% { transform: scale(1.05); box-shadow: 0 0 0 15px rgba(74, 222, 128, 0); }
        100% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(74, 222, 128, 0); }
    }
    
    /* Hide the text/labels for the native audio input */
    [data-testid="stAudioInput"] label {
        display: none !important;
    }
    </style>
""", unsafe_allow_html=True)

# Clean title
st.title("Sam")

# Initialize Router in session state
if "router" not in st.session_state:
    try:
        st.session_state.router = SamRouter()
    except Exception as e:
        st.error(f"Initialization Error: {e}")

if "chat" not in st.session_state and "router" in st.session_state:
    st.session_state.chat = st.session_state.router.get_chat_session()

if "messages" not in st.session_state:
    st.session_state.messages = []

# --- 3D ORB ---
st.markdown('<div class="orb-container"><div class="pulse-orb"></div></div>', unsafe_allow_html=True)

# Native audio input widget (styled cleanly without labels)
audio_value = st.audio_input("", label_visibility="collapsed")

if audio_value:
    with st.spinner("Listening..."):
        try:
            audio_bytes = audio_value.getvalue()
            response = st.session_state.chat.send_message([
                {"data": audio_bytes, "mime_type": "audio/wav"},
                "Please respond to this voice message directly."
            ])
            st.session_state.messages.append({"role": "user", "content": "🎤 [Voice Message]"})
            st.session_state.messages.append({"role": "assistant", "content": response.text})
            st.rerun()
        except Exception as e:
            st.error(f"Error: {e}")

# Display chat history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Text input
if prompt := st.chat_input("Or type a message to..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        try:
            response_stream = st.session_state.chat.send_message_stream(prompt)
            full_response = ""
            for chunk in response_stream:
                if chunk.text:
                    full_response += chunk.text
                    message_placeholder.markdown(full_response + "▌")
            message_placeholder.markdown(full_response)
        except Exception as e:
            full_response = f"[Error] {str(e)}"
            message_placeholder.markdown(full_response)

    st.session_state.messages.append({"role": "assistant", "content": full_response})

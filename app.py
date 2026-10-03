import streamlit as st
import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from core.router import SamRouter

st.set_page_config(page_title="Sam", layout="centered")

st.markdown("""
    <style>
    /* Hide top right buttons except 3 dots */
    .stAppDeployButton {display: none !important;}
    [data-testid="stHeaderActionElements"] {display: none !important;}
    
    /* Center Title exactly like the image */
    h1 {
        text-align: center;
        margin-top: 1rem;
        font-family: sans-serif;
    }

    /* The Glossy 3D Sphere matching your exact image */
    .glass-orb {
        width: 170px;
        height: 170px;
        margin: 5rem auto 0 auto;
        border-radius: 50%;
        background: radial-gradient(circle at 35% 25%, #6bfb9c 0%, #1ab854 35%, #064c1f 75%, #001204 100%);
        box-shadow: 
            inset -15px -15px 30px rgba(0,0,0,0.7),
            inset 15px 15px 25px rgba(255,255,255,0.4),
            0 25px 35px rgba(0,0,0,0.5);
    }

    /* 
       THE HACK: Pull the native Streamlit audio widget exactly over the sphere 
       and make it transparent. You see the sphere, but you click the mic.
    */
    [data-testid="stAudioInput"] {
        margin-top: -170px !important;
        width: 170px !important;
        height: 170px !important;
        margin-left: auto;
        margin-right: auto;
        opacity: 0.001; /* Completely hides the ugly grey box */
        z-index: 999;
        cursor: pointer;
    }
    
    /* Lock text chat input to the bottom */
    .stChatInput {
        position: fixed; 
        bottom: 3rem;
    }
    </style>
""", unsafe_allow_html=True)

st.markdown("<h1>Sam</h1>", unsafe_allow_html=True)

# Session state initialization
if "router" not in st.session_state:
    try:
        st.session_state.router = SamRouter()
    except Exception as e:
        st.error(f"Initialization Error: {e}")

if "chat" not in st.session_state and "router" in st.session_state:
    st.session_state.chat = st.session_state.router.get_chat_session()

if "messages" not in st.session_state:
    st.session_state.messages = []

# Render the visual 3D sphere
st.markdown('<div class="glass-orb"></div>', unsafe_allow_html=True)

# Render the invisible audio input right on top of it
audio_value = st.audio_input("Sam Mic", label_visibility="collapsed")

if audio_value:
    with st.spinner("Processing voice..."):
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

# Bottom text input
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

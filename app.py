import streamlit as st
import sys
import os

# Ensure sam_agent path is accessible
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from core.router import SamRouter

st.set_page_config(page_title="Sam Agent", page_icon="🤖", layout="centered")

# Custom CSS for the Glowing Orb and modern mobile layout
st.markdown("""
    <style>
    .stChatInput {position: fixed; bottom: 3rem;}
    .orb-container {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        margin-top: 1rem;
        margin-bottom: 2rem;
    }
    .pulse-orb {
        width: 90px;
        height: 90px;
        background: radial-gradient(circle, #38ef7d 0%, #11998e 100%);
        border-radius: 50%;
        box-shadow: 0 0 25px rgba(56, 239, 125, 0.6);
        animation: pulse 2s infinite;
        display: flex;
        align-items: center;
        justify-content: center;
        cursor: pointer;
    }
    @keyframes pulse {
        0% {
            transform: scale(0.95);
            box-shadow: 0 0 0 0 rgba(56, 239, 125, 0.7);
        }
        70% {
            transform: scale(1.05);
            box-shadow: 0 0 0 20px rgba(56, 239, 125, 0);
        }
        100% {
            transform: scale(0.95);
            box-shadow: 0 0 0 0 rgba(56, 239, 125, 0);
        }
    }
    .orb-label {
        margin-top: 12px;
        font-size: 0.9rem;
        color: #888;
        font-weight: 500;
        letter-spacing: 0.5px;
    }
    </style>
""", unsafe_allow_html=True)

st.title("🤖 Sam - Modular Assistant")
st.caption("Your personal AI companion across Chromebook & mobile.")

# Initialize Router in session state
if "router" not in st.session_state:
    try:
        st.session_state.router = SamRouter()
    except Exception as e:
        st.error(f"Initialization Error: {e}")

# Initialize persistent chat session
if "chat" not in st.session_state and "router" in st.session_state:
    st.session_state.chat = st.session_state.router.get_chat_session()

# Initialize message history list
if "messages" not in st.session_state:
    st.session_state.messages = []

# --- ORB VOICE INTERACTION AREA ---
st.markdown('<div class="orb-container"><div class="pulse-orb">🎙️</div><div class="orb-label">Tap below to speak with Sam</div></div>', unsafe_allow_html=True)

# Native audio input widget styled centrally for voice interaction
audio_value = st.audio_input("Voice Input")

# Handle Voice Input processing
if audio_value:
    with st.spinner("Sam is listening and processing your voice..."):
        try:
            # Send audio bytes directly to Gemini 3.8 Flash multimodal input
            audio_bytes = audio_value.getvalue()
            response = st.session_state.chat.send_message([
                {"data": audio_bytes, "mime_type": "audio/wav"},
                "Please respond to this voice message directly."
            ])
            
            # Log exchange
            st.session_state.messages.append({"role": "user", "content": "🎤 [Voice Message]"})
            st.session_state.messages.append({"role": "assistant", "content": response.text})
            st.rerun()
        except Exception as e:
            st.error(f"Voice Processing Error: {e}")

st.divider()

# Display chat history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Text input handling fallback/alternative
if prompt := st.chat_input("Or type a message to Sam..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        message_placeholder.text("Sam is thinking...")
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

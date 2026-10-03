import streamlit as st
import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from core.router import SamRouter

st.set_page_config(page_title="Sam", layout="centered")

st.markdown("""
    <style>
    .stAppDeployButton {display: none !important;}
    [data-testid="stHeaderActionElements"] {display: none !important;}
    h1 { text-align: center; margin-top: 1rem; font-family: sans-serif; }
    
    .orb-container {
        display: flex;
        justify-content: center;
        align-items: center;
        margin-top: 2.5rem;
        margin-bottom: 2.5rem;
        perspective: 800px;
    }
    
    .spinning-orb {
        width: 160px;
        height: 160px;
        border-radius: 50%;
        background: radial-gradient(circle at 30% 30%, #7efcb0 0%, #17b952 35%, #05481d 75%, #001204 100%);
        box-shadow: 
            inset -20px -20px 40px rgba(0,0,0,0.8),
            inset 15px 15px 30px rgba(255,255,255,0.4),
            0 20px 40px rgba(0,0,0,0.4);
        position: relative;
        animation: floatOrb 4s ease-in-out infinite;
        transform-style: preserve-3d;
    }

    .spinning-orb::after {
        content: '';
        position: absolute;
        top: 0; left: 0; right: 0; bottom: 0;
        border-radius: 50%;
        background: conic-gradient(from 0deg at 50% 50%, rgba(255,255,255,0) 0%, rgba(255,255,255,0.2) 25%, rgba(255,255,255,0) 50%, rgba(10,80,30,0.3) 75%, rgba(255,255,255,0) 100%);
        animation: spinSheen 6s linear infinite;
    }

    @keyframes spinSheen {
        0% { transform: rotate(0deg); }
        100% { transform: rotate(360deg); }
    }

    @keyframes floatOrb {
        0%, 100% { transform: translateY(0px) scale(1); }
        50% { transform: translateY(-8px) scale(1.02); }
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

# Render the clean 3D Spinning Orb
st.markdown("""
    <div class="orb-container">
        <div class="spinning-orb"></div>
    </div>
""", unsafe_allow_html=True)

# Display chat history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Handle Chat Input cleanly and reliably
if prompt := st.chat_input("Message Sam..."):
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
    st.rerun()

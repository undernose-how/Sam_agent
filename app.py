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
    .stChatInput { position: fixed; bottom: 3rem; }
    
    .orb-wrapper {
        display: flex;
        justify-content: center;
        align-items: center;
        margin-top: 3rem;
        margin-bottom: 2rem;
    }
    .glass-orb {
        width: 170px;
        height: 170px;
        border-radius: 50%;
        background: radial-gradient(circle at 35% 25%, #6bfb9c 0%, #1ab854 35%, #064c1f 75%, #001204 100%);
        box-shadow: 
            inset -15px -15px 30px rgba(0,0,0,0.7),
            inset 15px 15px 25px rgba(255,255,255,0.4),
            0 25px 35px rgba(0,0,0,0.5);
        cursor: pointer;
        transition: all 0.3s ease;
    }
    .glass-orb.listening {
        box-shadow: 
            inset -15px -15px 30px rgba(0,0,0,0.7),
            inset 15px 15px 25px rgba(255,255,255,0.4),
            0 0 50px #6bfb9c,
            0 0 100px rgba(107, 251, 156, 0.6);
        transform: scale(1.05);
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

# Safely parse query parameters to guarantee a string value
raw_param = st.query_params.get("voice_input", "")
voice_text = str(raw_param) if not isinstance(raw_param, list) else str(raw_param[0])

if voice_text and voice_text != st.session_state.get("processed_voice", ""):
    st.session_state.processed_voice = voice_text
    st.session_state.messages.append({"role": "user", "content": f"🎤 {voice_text}"})
    
    with st.chat_message("user"):
        st.markdown(f"🎤 {voice_text}")
        
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        try:
            response_stream = st.session_state.chat.send_message_stream(voice_text)
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
    st.query_params.clear()
    st.rerun()

# Render the 3D Orb with direct speech-recognition JS
st.markdown("""
    <div class="orb-wrapper">
        <div class="glass-orb" id="sam-orb" title="Tap to speak"></div>
    </div>
    <script>
        const orb = document.getElementById("sam-orb");
        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        
        if (orb && SpeechRecognition) {
            const recognition = new SpeechRecognition();
            recognition.continuous = false;
            recognition.interimResults = false;

            orb.onclick = () => {
                orb.classList.add("listening");
                try {
                    recognition.start();
                } catch(e) {
                    orb.classList.remove("listening");
                }
            };

            recognition.onresult = (event) => {
                const transcript = event.results[0][0].transcript;
                orb.classList.remove("listening");
                const currentUrl = window.location.href.split('?')[0];
                window.location.href = currentUrl + "?voice_input=" + encodeURIComponent(transcript);
            };

            recognition.onspeechend = () => {
                recognition.stop();
                orb.classList.remove("listening");
            };

            recognition.onerror = () => {
                orb.classList.remove("listening");
            };
        }
    </script>
""", unsafe_allow_html=True)

# Display chat history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Handle Text Input from bottom bar
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
    st.rerun()

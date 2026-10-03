import streamlit as st
import streamlit.components.v1 as components
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

# --- SMART ORB JAVASCRIPT COMPONENT ---
# This block handles the 3D UI, Noise Suppression, and Silence Detection
orb_html = """
<!DOCTYPE html>
<html>
<head>
    <script src="https://cdn.jsdelivr.net/npm/streamlit-component-lib@1.3.0/dist/streamlit.js"></script>
    <style>
        body {
            display: flex;
            justify-content: center;
            align-items: center;
            height: 250px;
            margin: 0;
            background-color: transparent;
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
        /* Glowing effect when actively listening */
        .glass-orb.listening {
            box-shadow: 
                inset -15px -15px 30px rgba(0,0,0,0.7),
                inset 15px 15px 25px rgba(255,255,255,0.4),
                0 0 50px #6bfb9c,
                0 0 100px rgba(107, 251, 156, 0.6);
            transform: scale(1.05);
        }
    </style>
</head>
<body>
    <div class="glass-orb" id="orb"></div>

    <script>
        function init() {
            Streamlit.setComponentReady();
            Streamlit.setFrameHeight(250);
            
            const orb = document.getElementById("orb");
            // Load Chrome's native Speech Recognition (includes VAD & DSP Noise Suppression)
            const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
            
            if (!SpeechRecognition) {
                orb.innerHTML = "<p style='color:white;text-align:center;padding-top:70px'>Not Supported</p>";
                return;
            }

            const recognition = new SpeechRecognition();
            // Automatically stop when silence is detected
            recognition.continuous = false; 
            recognition.interimResults = false;

            orb.addEventListener("click", () => {
                orb.classList.add("listening");
                recognition.start();
            });

            recognition.onresult = (event) => {
                const transcript = event.results[0][0].transcript;
                orb.classList.remove("listening");
                // Send the recognized text back to Streamlit/Python
                Streamlit.setComponentValue(transcript);
            };

            recognition.onspeechend = () => {
                recognition.stop();
                orb.classList.remove("listening");
            };

            recognition.onerror = (event) => {
                orb.classList.remove("listening");
            };
        }
        
        window.addEventListener("load", init);
    </script>
</body>
</html>
"""

# Render the Smart Orb
transcript = components.html(orb_html, height=250)

# Display chat history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Handle Voice Input from the Orb
if transcript and transcript != st.session_state.get("last_voice_input", ""):
    st.session_state.last_voice_input = transcript
    st.session_state.messages.append({"role": "user", "content": f"🎤 {transcript}"})
    
    with st.chat_message("user"):
        st.markdown(f"🎤 {transcript}")
        
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        try:
            response_stream = st.session_state.chat.send_message_stream(transcript)
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

# Handle Text Input from the bottom bar
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

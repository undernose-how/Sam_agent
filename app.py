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
        flex-direction: column;
        align-items: center;
        justify-content: center;
        margin-top: 2rem;
        margin-bottom: 2rem;
    }

    .spinning-orb {
        width: 140px;
        height: 140px;
        border-radius: 50%;
        background: radial-gradient(circle at 30% 30%, #7efcb0 0%, #17b952 35%, #05481d 75%, #001204 100%);
        box-shadow: 
            inset -15px -15px 30px rgba(0,0,0,0.8),
            inset 12px 12px 25px rgba(255,255,255,0.4),
            0 15px 30px rgba(0,0,0,0.4);
        position: relative;
        animation: floatOrb 4s ease-in-out infinite;
        cursor: pointer;
        transition: transform 0.2s ease;
    }
    
    .spinning-orb:hover {
        transform: scale(1.03);
    }

    .spinning-orb.listening {
        background: radial-gradient(circle at 30% 30%, #ffffff 0%, #6bfb9c 35%, #107c3e 75%, #002b0a 100%);
        box-shadow: 0 0 35px #6bfb9c, 0 0 70px rgba(107, 251, 156, 0.6);
        animation: pulseOrb 1.2s infinite alternate;
    }

    @keyframes floatOrb {
        0%, 100% { transform: translateY(0px); }
        50% { transform: translateY(-6px); }
    }

    @keyframes pulseOrb {
        0% { transform: scale(1); }
        100% { transform: scale(1.07); }
    }
    
    .instruction-label {
        font-family: sans-serif;
        color: #9ca3af;
        font-size: 0.85rem;
        margin-top: 1rem;
        text-align: center;
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
    st.messages = []

# Display chat history first
if "messages" in st.session_state:
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

# Handle Voice Input via HTML/JS component bridge cleanly
voice_result = st.text_input("Voice transcript bridge", key="voice_bridge", label_visibility="collapsed")

# Render 3D Orb with direct HTML integration
st.markdown("""
    <div class="orb-container">
        <div class="spinning-orb" id="sam-orb" title="Click to speak"></div>
        <div class="instruction-label" id="orb-status">Tap orb to talk</div>
    </div>

    <script>
        const orb = document.getElementById("sam-orb");
        const statusLabel = document.getElementById("orb-status");
        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;

        if (orb && SpeechRecognition) {
            const recognition = new SpeechRecognition();
            recognition.continuous = false;
            recognition.interimResults = false;

            let recognizing = false;

            orb.onclick = () => {
                if (!recognizing) {
                    try {
                        recognition.start();
                    } catch(e) {
                        console.error(e);
                    }
                } else {
                    recognition.stop();
                }
            };

            recognition.onstart = () => {
                recognizing = true;
                orb.classList.add("listening");
                statusLabel.innerText = "Listening...";
                statusLabel.style.color = "#4ade80";
            };

            recognition.onresult = (event) => {
                const text = event.results[0][0].transcript;
                statusLabel.innerText = "Heard: " + text;
                
                // Find Streamlit's hidden text input for the bridge and set its value
                const doc = window.parent.document;
                const inputs = doc.querySelectorAll('input[type="text"]');
                inputs.forEach(input => {
                    if (input.value !== undefined) {
                        // Locate our specific bridge input by placeholder or proximity
                        const nativeInputValueSetter = Object.getOwnPropertyDescriptor(window.parent.HTMLInputElement.prototype, "value").set;
                        nativeInputValueSetter.call(input, text);
                        input.dispatchEvent(new Event('input', { bubbles: true }));
                    }
                });
            };

            recognition.onend = () => {
                recognizing = false;
                orb.classList.remove("listening");
                statusLabel.innerText = "Tap orb to talk";
                statusLabel.style.color = "#9ca3af";
            };

            recognition.onerror = () => {
                recognizing = false;
                orb.classList.remove("listening");
                statusLabel.innerText = "Microphone error";
                statusLabel.style.color = "#f87171";
            };
        } else {
            statusLabel.innerText = "Speech API not supported in this browser";
        }
    </script>
""", unsafe_allow_html=True)

# Process text input from standard chat box OR the voice bridge
prompt = st.chat_input("Message Sam...")

if prompt:
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

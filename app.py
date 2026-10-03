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
    
    .orb-wrapper {
        display: flex;
        justify-content: center;
        align-items: center;
        margin-top: 2.5rem;
        margin-bottom: 1.5rem;
        perspective: 800px;
    }
    
    .spinning-orb {
        width: 150px;
        height: 150px;
        border-radius: 50%;
        background: radial-gradient(circle at 30% 30%, #7efcb0 0%, #17b952 35%, #05481d 75%, #001204 100%);
        box-shadow: 
            inset -20px -20px 40px rgba(0,0,0,0.8),
            inset 15px 15px 30px rgba(255,255,255,0.4),
            0 20px 40px rgba(0,0,0,0.4);
        position: relative;
        animation: floatOrb 4s ease-in-out infinite;
        transform-style: preserve-3d;
        cursor: pointer;
        transition: all 0.3s ease;
    }

    /* Listening state: bright glowing pulse */
    .spinning-orb.listening {
        background: radial-gradient(circle at 30% 30%, #ffffff 0%, #6bfb9c 35%, #107c3e 75%, #002b0a 100%);
        box-shadow: 
            inset -15px -15px 30px rgba(0,0,0,0.5),
            inset 15px 15px 25px rgba(255,255,255,0.8),
            0 0 40px #6bfb9c,
            0 0 80px rgba(107, 251, 156, 0.7);
        animation: pulseOrb 1.5s infinite alternate;
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

    @keyframes pulseOrb {
        0% { transform: scale(1); }
        100% { transform: scale(1.06); }
    }
    
    .transcript-box {
        text-align: center;
        font-family: sans-serif;
        font-size: 1rem;
        color: #d1d5db;
        background: rgba(255, 255, 255, 0.05);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 12px;
        padding: 12px 20px;
        margin: 0 auto 2rem auto;
        max-width: 500px;
        min-height: 48px;
        display: flex;
        align-items: center;
        justify-content: center;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
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

# Safely handle voice query parameter passed back from browser recognition
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

# Render 3D Spinning Orb and Live Transcript Feedback Box
st.markdown("""
    <div class="orb-wrapper">
        <div class="spinning-orb" id="sam-orb" title="Click to speak"></div>
    </div>
    <div class="transcript-box" id="transcript-display">Click the orb and start speaking...</div>
    
    <script>
        const orb = document.getElementById("sam-orb");
        const transcriptDisplay = document.getElementById("transcript-display");
        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        
        if (orb && SpeechRecognition) {
            const recognition = new SpeechRecognition();
            recognition.continuous = false;
            recognition.interimResults = true; // Allows seeing words as you say them!

            let isListening = false;

            orb.onclick = () => {
                if (!isListening) {
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
                isListening = true;
                orb.classList.add("listening");
                transcriptDisplay.innerText = "Listening...";
                transcriptDisplay.style.color = "#7efcb0";
            };

            recognition.onresult = (event) => {
                let interimTranscript = '';
                let finalTranscript = '';

                for (let i = event.resultIndex; i < event.results.length; ++i) {
                    if (event.results[i].isFinal) {
                        finalTranscript += event.results[i][0].transcript;
                    } else {
                        interimTranscript += event.results[i][0].transcript;
                    }
                }

                // Show what Sam is hearing live inside the box
                if (interimTranscript !== '') {
                    transcriptDisplay.innerText = '"' + interimTranscript + '"';
                } else if (finalTranscript !== '') {
                    transcriptDisplay.innerText = '"' + finalTranscript + '"';
                }

                if (finalTranscript !== '') {
                    transcriptDisplay.innerText = "Processing: \"" + finalTranscript + "\"";
                    const currentUrl = window.location.href.split('?')[0];
                    window.location.href = currentUrl + "?voice_input=" + encodeURIComponent(finalTranscript);
                }
            };

            recognition.onspeechend = () => {
                recognition.stop();
            };

            recognition.onend = () => {
                isListening = false;
                orb.classList.remove("listening");
            };

            recognition.onerror = (event) => {
                isListening = false;
                orb.classList.remove("listening");
                transcriptDisplay.innerText = "Microphone error or permission blocked.";
                transcriptDisplay.style.color = "#f87171";
            };
        } else if (orb) {
            transcriptDisplay.innerText = "Speech recognition not supported in this browser.";
            transcriptDisplay.style.color = "#f87171";
        }
    </script>
""", unsafe_allow_html=True)

# Display chat history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Handle standard text input
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

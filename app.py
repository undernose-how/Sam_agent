import streamlit as st
import sys
import os

# Ensure sam_agent path is accessible
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from core.router import SamRouter

st.set_page_config(page_title="Sam Agent", page_icon="🤖", layout="centered")

st.title("🤖 Sam - Modular Assistant")
st.caption("Your personal automation assistant running locally via Streamlit.")

# Initialize Router in session state
if "router" not in st.session_state:
    st.session_state.router = SamRouter()

# Initialize persistent chat session
if "chat" not in st.session_state:
    st.session_state.chat = st.session_state.router.get_chat_session()

# Initialize message history list
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# User input handling
if prompt := st.chat_input("What would you like Sam to do?"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Generate streaming response
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

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
        margin-top: 2rem;
        margin-bottom: 2rem;
        filter: drop-shadow(0 15px 25px rgba(10, 150, 80, 0.3));
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

# Render the True 3D Rotating Sphere using Three.js
st.markdown("""
    <div class="orb-wrapper">
        <div id="three-orb-canvas" style="width: 180px; height: 180px; border-radius: 50%;"></div>
    </div>
    
    <script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
    <script>
    (function() {
        const container = document.getElementById('three-orb-canvas');
        if (!container) return;
        
        // Prevent duplicate initializations if Streamlit reruns
        container.innerHTML = '';

        const scene = new THREE.Scene();
        const camera = new THREE.PerspectiveCamera(45, 1, 0.1, 1000);
        camera.position.z = 4;

        const renderer = new THREE.WebGLRenderer({ alpha: true, antialias: true });
        renderer.setSize(180, 180);
        container.appendChild(renderer.domElement);

        // Inner solid 3D sphere with rich metallic/glossy green material
        const geometry = new THREE.SphereGeometry(1.2, 32, 32);
        const material = new THREE.MeshStandardMaterial({
            color: 0x10b981,
            emissive: 0x054f21,
            roughness: 0.25,
            metalness: 0.4
        });
        const sphere = new THREE.Mesh(geometry, material);
        scene.add(sphere);

        // Outer translucent high-tech wireframe sphere for depth
        const wireGeometry = new THREE.SphereGeometry(1.26, 16, 16);
        const wireMaterial = new THREE.MeshBasicMaterial({
            color: 0x6bfb9c,
            wireframe: true,
            transparent: true,
            opacity: 0.2
        });
        const wireSphere = new THREE.Mesh(wireGeometry, wireMaterial);
        scene.add(wireSphere);

        // Dynamic 3D Lighting
        const ambientLight = new THREE.AmbientLight(0xffffff, 0.7);
        scene.add(ambientLight);

        const pointLight = new THREE.PointLight(0x6bfb9c, 3, 50);
        pointLight.position.set(3, 3, 3);
        scene.add(pointLight);

        // Smooth multi-axis rotation loop
        function animate() {
            requestAnimationFrame(animate);
            sphere.rotation.x += 0.004;
            sphere.rotation.y += 0.007;
            wireSphere.rotation.x -= 0.003;
            wireSphere.rotation.y -= 0.005;
            renderer.render(scene, camera);
        }
        animate();
    })();
    </script>
""", unsafe_allow_html=True)

# Display chat history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Handle Chat Input cleanly
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

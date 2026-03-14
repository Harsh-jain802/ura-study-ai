import streamlit as st
import fitz  # PyMuPDF
import google.generativeai as genai
from streamlit_google_auth import Authenticate
import json
import os

# ==========================================
# 1. INITIAL CONFIG (MUST BE THE FIRST COMMAND)
# ==========================================
st.set_page_config(page_title="Aura Study AI", page_icon="✨", layout="wide")

# ==========================================
# 2. AUTHENTICATION SETUP
# ==========================================

# Create the secrets file for the Google Auth library
def create_secrets_file():
    google_secrets = {
        "web": {
            "client_id": st.secrets["GOOGLE_CLIENT_ID"],
            "client_secret": st.secrets["GOOGLE_CLIENT_SECRET"],
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
            "redirect_uris": ["https://ura-study-ai-ju8ey5voyozp46sez29dof.streamlit.app"]
        }
    }
    with open('client_secrets.json', 'w') as f:
        json.dump(google_secrets, f)

create_secrets_file()

# Initialize the Authenticator
# Note: Changed 'cookie_key' to 'key' as this is the most common cause of the TypeError
authenticator = Authenticate(
    secret_credentials_path='client_secrets.json',
    cookie_name='aura_study_cookie',
    key='aura_secret_key_123', 
    redirect_uri="https://ura-study-ai-ju8ey5voyozp46sez29dof.streamlit.app",
    cookie_expiry_days=30
)

# Check if user is already logged in
authenticator.check_authenticity()

# If NOT logged in, show login screen and STOP
if not st.session_state.get("connected"):
    st.markdown("<h1 style='text-align: center; color: #4facfe;'>✨ Aura Study AI</h1>", unsafe_allow_html=True)
    st.write("### Welcome! Please sign in with Google to access your dashboard.")
    authenticator.login()
    st.stop() 

# ==========================================
# 3. APP CONFIGURATION (Runs after login)
# ==========================================

# API CONFIG
API_KEY = st.secrets["GEMINI_API_KEY"]
genai.configure(api_key=API_KEY)

# SESSION STATE
if 'history' not in st.session_state:
    st.session_state.history = []  
if 'active_index' not in st.session_state:
    st.session_state.active_index = None

# UI STYLING
st.markdown("""
    <style>
    .stApp { background: radial-gradient(circle at top right, #1a1f2c, #0b0e14); }
    section[data-testid="stSidebar"] { background-color: #0d1117 !important; border-right: 1px solid #30363d; }
    .hero-text {
        background: linear-gradient(90deg, #4facfe, #00f2fe);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 3.2rem !important;
        font-weight: 800 !important;
    }
    .content-card {
        background: rgba(22, 27, 34, 0.7);
        border: 1px solid #30363d;
        border-radius: 20px;
        padding: 40px;
        backdrop-filter: blur(12px);
        margin-top: 20px;
    }
    .tutor-bubble {
        background: rgba(79, 172, 254, 0.1);
        padding: 20px;
        border-radius: 15px;
        border-left: 5px solid #4facfe;
        margin-top: 20px;
    }
    </style>
    """, unsafe_allow_html=True)

@st.cache_resource
def get_model():
    return genai.GenerativeModel('gemini-1.5-flash')

model = get_model()

# SIDEBAR
with st.sidebar:
    st.markdown("<h2 style='color: #4facfe;'>✨ Aura AI</h2>", unsafe_allow_html=True)
    
    # Display User Info
    user = st.session_state.get('user_info', {})
    st.write(f"Logged in: **{user.get('email', 'Student')}**")
    
    if st.button("Logout", use_container_width=True):
        authenticator.logout()
        st.rerun()
    
    st.write("---")
    
    if st.button("➕ New Session", use_container_width=True):
        st.session_state.active_index = None
        st.rerun()
    
    st.markdown("### 📂 Upload Material")
    uploaded_file = st.file_uploader("Drop PDF here", type="pdf", label_visibility="collapsed")
    
    if uploaded_file and st.button("🚀 UNLOCK KNOWLEDGE", use_container_width=True):
        with st.spinner("🧠 Aura is reading..."):
            try:
                doc = fitz.open(stream=uploaded_file.read(), filetype="pdf")
                text = "".join([doc.load_page(i).get_text() for i in range(min(5, len(doc)))])
                prompt = f"Analyze this text and provide: Big Picture, Key Pillars, Analogy, and 2 Self-test questions: {text}"
                response = model.generate_content(prompt)
                st.session_state.history.append({"title": uploaded_file.name, "result": response.text, "full_text": text})
                st.session_state.active_index = len(st.session_state.history) - 1
                st.balloons()
                st.rerun()
            except Exception as e:
                st.error(f"Error: {e}")

    st.write("---")
    st.markdown("### 🕒 Recent History")
    for i, item in enumerate(reversed(st.session_state.history)):
        real_idx = len(st.session_state.history) - 1 - i
        if st.button(f"📄 {item['title'][:18]}...", key=f"h_{real_idx}", use_container_width=True):
            st.session_state.active_index = real_idx
            st.rerun()

# MAIN CONTENT
st.markdown("<h1 class='hero-text'>Aura Study AI</h1>", unsafe_allow_html=True)

active_data = st.session_state.history[st.session_state.active_index] if st.session_state.active_index is not None else None

if active_data:
    st.markdown(f"<p style='color: #94a3b8;'>Resource: <b>{active_data['title']}</b></p>", unsafe_allow_html=True)
    tab1, tab2 = st.tabs(["📑 Study Guide", "💬 AI Doubt Solver"])
    
    with tab1:
        st.markdown('<div class="content-card">', unsafe_allow_html=True)
        st.markdown(active_data['result'])
        st.markdown('</div>', unsafe_allow_html=True)
        
    with tab2:
        st.markdown('<div class="content-card">', unsafe_allow_html=True)
        st.markdown("### 💬 Ask a Doubt")
        user_query = st.chat_input("Ask Aura anything about this document...")
        if user_query:
            with st.spinner("Thinking..."):
                tutor_prompt = f"Context: {active_data['full_text']}\n\nQuestion: {user_query}"
                ans = model.generate_content(tutor_prompt)
                st.markdown(f'<div class="tutor-bubble"><b>Aura says:</b><br><br>{ans.text}</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
else:
    st.write("---")
    st.markdown("### 👋 Welcome back! Upload a PDF in the sidebar to get started.")
    st.image("https://img.freepik.com/free-vector/digital-lifestyle-concept-illustration_114360-7327.jpg", width=600)

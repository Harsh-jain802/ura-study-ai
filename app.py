import streamlit as st
import fitz  # PyMuPDF
import google.generativeai as genai
from streamlit_google_auth import Authenticate

# ==========================================
# 1. AUTHENTICATION SETUP (The New Part)
# ==========================================
authenticator = Authenticate(
    secret_credentials_path=None,
    client_id=st.secrets["GOOGLE_CLIENT_ID"],
    client_secret=st.secrets["GOOGLE_CLIENT_SECRET"],
    # This MUST match the Redirect URI you saved in Google Console
    redirect_uri="https://ura-study-ai-ju8ey5voyozp46sez29dof.streamlit.app", 
    cookie_name="aura_auth",
    cookie_key="aura_secure_key",
    cookie_expiry_days=30,
)

# Check if the user is already logged in
authenticator.check_authenticity()

# If user is NOT logged in, show login screen and STOP
if not st.session_state.get("connected"):
    st.set_page_config(page_title="Aura AI - Login", page_icon="✨")
    st.markdown("<h1 style='text-align: center; color: #4facfe;'>✨ Aura Study AI</h1>", unsafe_allow_html=True)
    st.write("### Welcome! Please sign in with Google to continue.")
    
    # This displays the actual "Login with Google" button
    authenticator.login()
    st.stop() 

# ==========================================
# 2. YOUR ORIGINAL APP CODE (Runs after login)
# ==========================================

# API CONFIG
API_KEY = st.secrets["GEMINI_API_KEY"]
genai.configure(api_key=API_KEY)

# SESSION STATE
if 'history' not in st.session_state:
    st.session_state.history = []  
if 'active_index' not in st.session_state:
    st.session_state.active_index = None

# UI CONFIG & STYLING (Your Premium UI)
st.set_page_config(page_title="Aura Study AI", page_icon="✨", layout="wide")

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
    }
    </style>
    """, unsafe_allow_html=True)

@st.cache_resource
def get_model():
    return genai.GenerativeModel('gemini-1.5-flash')

model = get_model()

# SIDEBAR (Updated with Logout)
with st.sidebar:
    st.markdown("<h2 style='color: #4facfe;'>✨ Aura AI</h2>", unsafe_allow_html=True)
    
    # Show who is logged in
    user_email = st.session_state.get('user_info', {}).get('email', 'Student')
    st.write(f"Logged in: **{user_email}**")
    
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
        user_query = st.chat_input("Ask anything...")
        if user_query:
            ans = model.generate_content(f"Context: {active_data['full_text']}\nQuestion: {user_query}")
            st.info(f"**Aura:** {ans.text}")
        st.markdown('</div>', unsafe_allow_html=True)
else:
    st.write("---")
    st.markdown("### 👋 Welcome! Upload a PDF to start.")
    st.image("https://img.freepik.com/free-vector/digital-lifestyle-concept-illustration_114360-7327.jpg", width=500)

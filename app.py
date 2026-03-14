import streamlit as st
import fitz  # PyMuPDF
import google.generativeai as genai

# ==========================================
# 1. APP CONFIGURATION
# ==========================================
st.set_page_config(page_title="Aura Study AI", page_icon="✨", layout="wide")

# API CONFIG
if "GEMINI_API_KEY" not in st.secrets:
    st.error("Missing GEMINI_API_KEY in Secrets!")
    st.stop()

genai.configure(api_key=st.secrets["GEMINI_API_KEY"])

# SESSION STATE
if 'history' not in st.session_state:
    st.session_state.history = []  
if 'active_index' not in st.session_state:
    st.session_state.active_index = None

# UI STYLING
st.markdown("""
    <style>
    .stApp { background: #0b0e14; color: white; }
    .hero-text {
        background: linear-gradient(90deg, #4facfe, #00f2fe);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 3rem !important;
        font-weight: 800 !important;
    }
    .content-card {
        background: rgba(255, 255, 255, 0.05);
        border: 1px solid #30363d;
        border-radius: 15px;
        padding: 25px;
        margin-top: 20px;
    }
    </style>
    """, unsafe_allow_html=True)

# MODEL INITIALIZATION (Robust checking)
@st.cache_resource
def get_model():
    # We try the most stable version strings
    for m in ["gemini-1.5-flash", "gemini-1.5-flash-latest", "gemini-pro"]:
        try:
            model = genai.GenerativeModel(m)
            # Test if it actually works
            model.generate_content("test")
            return model
        except:
            continue
    return None

model = get_model()

# ==========================================
# 2. SIDEBAR
# ==========================================
with st.sidebar:
    st.markdown("<h2 style='color: #4facfe;'>✨ Aura AI</h2>", unsafe_allow_html=True)
    
    if st.button("➕ New Session", use_container_width=True):
        st.session_state.active_index = None
        st.rerun()
    
    st.markdown("### 📂 Upload Material")
    uploaded_file = st.file_uploader("Drop PDF here", type="pdf", label_visibility="collapsed")
    
    if uploaded_file and st.button("🚀 UNLOCK KNOWLEDGE", use_container_width=True):
        if model is None:
            st.error("Could not connect to Gemini. Check your API Key.")
        else:
            with st.spinner("🧠 Aura is reading..."):
                try:
                    doc = fitz.open(stream=uploaded_file.read(), filetype="pdf")
                    text = "".join([page.get_text() for page in doc][:8])
                    
                    prompt = f"Analyze this study material and provide a Big Picture, Key Pillars, and an Analogy: {text[:4000]}"
                    response = model.generate_content(prompt)
                    
                    st.session_state.history.append({
                        "title": uploaded_file.name, 
                        "result": response.text, 
                        "full_text": text
                    })
                    st.session_state.active_index = len(st.session_state.history) - 1
                    st.rerun()
                except Exception as e:
                    st.error(f"Error: {e}")

    st.write("---")
    for i, item in enumerate(reversed(st.session_state.history)):
        real_idx = len(st.session_state.history) - 1 - i
        if st.button(f"📄 {item['title'][:15]}", key=f"h_{real_idx}", use_container_width=True):
            st.session_state.active_index = real_idx
            st.rerun()

# ==========================================
# 3. MAIN CONTENT
# ==========================================
st.markdown("<h1 class='hero-text'>Aura Study AI</h1>", unsafe_allow_html=True)

active_data = st.session_state.history[st.session_state.active_index] if st.session_state.active_index is not None else None

if active_data:
    tab1, tab2 = st.tabs(["📑 Study Guide", "💬 Ask Aura"])
    with tab1:
        st.markdown('<div class="content-card">', unsafe_allow_html=True)
        st.markdown(active_data['result'])
        st.markdown('</div>', unsafe_allow_html=True)
    with tab2:
        user_query = st.chat_input("Ask a doubt...")
        if user_query:
            ans = model.generate_content(f"Context: {active_data['full_text'][:3000]}\n\nQuestion: {user_query}")
            st.info(f"**Aura:** {ans.text}")
else:
    st.info("👋 Upload a PDF to start studying!")

import streamlit as st
import fitz  # PyMuPDF
import google.generativeai as genai

# ==========================================
# 1. APP CONFIGURATION
# ==========================================
st.set_page_config(page_title="Aura Study AI", page_icon="✨", layout="wide")

# API CONFIG
if "GEMINI_API_KEY" not in st.secrets:
    st.error("❌ GEMINI_API_KEY is missing from Streamlit Secrets!")
    st.stop()

genai.configure(api_key=st.secrets["GEMINI_API_KEY"])

# SESSION STATE
if 'history' not in st.session_state:
    st.session_state.history = []  
if 'active_index' not in st.session_state:
    st.session_state.active_index = None

# UI STYLING (Restored)
st.markdown("""
    <style>
    .stApp { background: radial-gradient(circle at top right, #1a1f2c, #0b0e14); color: white; }
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
        padding: 30px;
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
    # Using 'gemini-1.5-flash' which is the newest and fastest
    return genai.GenerativeModel('gemini-1.5-flash')

model = get_model()

# ==========================================
# 2. SIDEBAR (Restored History & Upload)
# ==========================================
with st.sidebar:
    st.markdown("<h2 style='color: #4facfe;'>✨ Aura AI</h2>", unsafe_allow_html=True)
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
                text = "".join([page.get_text() for page in doc][:10])
                
                prompt = (
                    f"Analyze this study material and provide:\n"
                    f"1. **The Big Picture**\n2. **Key Pillars**\n3. **Practical Analogy**\n4. **2 Self-test questions**\n\n"
                    f"Text: {text[:4000]}"
                )
                
                response = model.generate_content(prompt)
                
                st.session_state.history.append({
                    "title": uploaded_file.name, 
                    "result": response.text, 
                    "full_text": text
                })
                st.session_state.active_index = len(st.session_state.history) - 1
                st.balloons()
                st.rerun()
            except Exception as e:
                st.error(f"Error: {e}")

    st.write("---")
    st.markdown("### 🕒 Recent History")
    # Restored full history layout
    for i, item in enumerate(reversed(st.session_state.history)):
        real_idx = len(st.session_state.history) - 1 - i
        if st.button(f"📄 {item['title']}", key=f"h_{real_idx}", use_container_width=True):
            st.session_state.active_index = real_idx
            st.rerun()

# ==========================================
# 3. MAIN CONTENT
# ==========================================
st.markdown("<h1 class='hero-text'>Aura Study AI</h1>", unsafe_allow_html=True)

active_data = st.session_state.history[st.session_state.active_index] if st.session_state.active_index is not None else None

if active_data:
    st.markdown(f"<p style='color: #94a3b8;'>Current Resource: <b>{active_data['title']}</b></p>", unsafe_allow_html=True)
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
                tutor_prompt = f"Context: {active_data['full_text'][:3000]}\n\nQuestion: {user_query}"
                ans = model.generate_content(tutor_prompt)
                st.markdown(f'<div class="tutor-bubble"><b>Aura says:</b><br><br>{ans.text}</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
else:
    # Restored Welcome Image and Message
    st.write("---")
    st.markdown("### 👋 Welcome back! Upload a PDF in the sidebar to begin your session.")
    st.image("https://img.freepik.com/free-vector/digital-lifestyle-concept-illustration_114360-7327.jpg", width=600)

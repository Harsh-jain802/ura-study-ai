import streamlit as st
import fitz  # PyMuPDF
import google.generativeai as genai

# ==========================================
# 1. API CONFIGURATION
# ==========================================
# Securely pulling from Streamlit Secrets
API_KEY = st.secrets["GEMINI_API_KEY"]
genai.configure(api_key=API_KEY)

# ==========================================
# 2. SESSION STATE
# ==========================================
if 'history' not in st.session_state:
    st.session_state.history = []  
if 'active_index' not in st.session_state:
    st.session_state.active_index = None

# ==========================================
# 3. PREMIUM UI CONFIG & STYLING
# ==========================================
st.set_page_config(page_title="Aura Study AI", page_icon="✨", layout="wide")

st.markdown("""
    <style>
    .stApp { background: radial-gradient(circle at top right, #1a1f2c, #0b0e14); }
    section[data-testid="stSidebar"] { background-color: #0d1117 !important; border-right: 1px solid #30363d; }
    .main-card {
        background: rgba(22, 27, 34, 0.8);
        border: 1px solid #3a7bd5;
        border-radius: 20px;
        padding: 25px;
        backdrop-filter: blur(12px);
        margin-bottom: 20px;
    }
    .hero-text {
        background: linear-gradient(90deg, #4facfe, #00f2fe);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 2.8rem !important;
        font-weight: 800 !important;
    }
    .tutor-box {
        background: rgba(79, 172, 254, 0.1);
        border-radius: 15px;
        padding: 15px;
        border: 1px dashed #4facfe;
    }
    </style>
    """, unsafe_allow_html=True)

# ==========================================
# 4. BULLETPROOF MODEL PICKER (Fixed the NotFound error)
# ==========================================
@st.cache_resource
def get_model():
    try:
        # Ask Google for the list of models YOU are allowed to use
        available = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        
        # Priority list
        if 'models/gemini-1.5-flash' in available: return genai.GenerativeModel('models/gemini-1.5-flash')
        if 'models/gemini-1.5-flash-latest' in available: return genai.GenerativeModel('models/gemini-1.5-flash-latest')
        
        # Fallback to the first working model it finds
        return genai.GenerativeModel(available[0])
    except Exception:
        # Last resort fallback string
        return genai.GenerativeModel('gemini-1.5-flash')

model = get_model()

# ==========================================
# 5. SIDEBAR (History)
# ==========================================
with st.sidebar:
    st.markdown("<h2 style='color: #4facfe;'>✨ Aura AI</h2>", unsafe_allow_html=True)
    if st.button("➕ New Session", use_container_width=True):
        st.session_state.active_index = None
        st.rerun()
    st.write("---")
    st.markdown("### 🕒 History")
    for i, item in enumerate(reversed(st.session_state.history)):
        real_idx = len(st.session_state.history) - 1 - i
        if st.button(f"📄 {item['title'][:15]}...", key=f"h_{real_idx}", use_container_width=True):
            st.session_state.active_index = real_idx
            st.rerun()

# ==========================================
# 6. MAIN CONTENT
# ==========================================
st.markdown("<h1 class='hero-text'>Aura Study AI</h1>", unsafe_allow_html=True)

col1, col2, col3 = st.columns([1, 1.5, 1], gap="medium")

with col1:
    st.markdown('<div class="main-card">', unsafe_allow_html=True)
    st.markdown("### 📂 Upload")
    uploaded_file = st.file_uploader("", type="pdf")
    
    if uploaded_file and st.button("🚀 ANALYZE"):
        with st.spinner("Analyzing..."):
            try:
                doc = fitz.open(stream=uploaded_file.read(), filetype="pdf")
                text = "".join([doc.load_page(i).get_text() for i in range(min(5, len(doc)))])
                
                prompt = f"Summarize this text with a Master Concept, 4 Pillars, an Analogy, and a 2-question quiz: {text}"
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
    st.markdown('</div>', unsafe_allow_html=True)

active_data = st.session_state.history[st.session_state.active_index] if st.session_state.active_index is not None else None

with col2:
    if active_data:
        st.markdown('<div class="main-card">', unsafe_allow_html=True)
        st.markdown(f"#### 📖 {active_data['title']}")
        st.write(active_data['result'])
        st.markdown('</div>', unsafe_allow_html=True)
    else:
        st.info("Upload a PDF to get started.")

with col3:
    st.markdown('<div class="main-card">', unsafe_allow_html=True)
    st.markdown("### 💬 Doubt Solver")
    if active_data:
        user_query = st.text_input("Ask a question about this topic...")
        if user_query:
            with st.spinner("Thinking..."):
                tutor_prompt = f"Context: {active_data['full_text']}\n\nQuestion: {user_query}"
                ans = model.generate_content(tutor_prompt)
                st.markdown('<div class="tutor-box">', unsafe_allow_html=True)
                st.markdown(ans.text)
                st.markdown('</div>', unsafe_allow_html=True)
    else:
        st.caption("Summarize a file first to chat with AI Tutor.")
    st.markdown('</div>', unsafe_allow_html=True)

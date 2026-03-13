import streamlit as st
import fitz  # PyMuPDF
import google.generativeai as genai

# ==========================================
# 1. API CONFIGURATION
# ==========================================
# We pull the key from the Streamlit Secrets vault
API_KEY = st.secrets["GEMINI_API_KEY"]
genai.configure(api_key=API_KEY)

# ==========================================
# 2. SESSION STATE (App Memory)
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
        background: rgba(255, 255, 255, 0.05);
        border-radius: 15px;
        padding: 15px;
        border: 1px dashed #4facfe;
    }
    </style>
    """, unsafe_allow_html=True)

# ==========================================
# 4. MODEL PICKER
# ==========================================
@st.cache_resource
def get_model():
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

# --- COLUMN 1: UPLOAD ---
with col1:
    st.markdown('<div class="main-card">', unsafe_allow_html=True)
    st.markdown("### 📂 Upload")
    uploaded_file = st.file_uploader("", type="pdf")
    
    if uploaded_file and st.button("🚀 ANALYZE"):
        with st.spinner("Processing..."):
            doc = fitz.open(stream=uploaded_file.read(), filetype="pdf")
            text = "".join([doc.load_page(i).get_text() for i in range(min(5, len(doc)))])
            
            prompt = f"Create a Master Concept, 4 Pillars, an Analogy, and a 2-question quiz for this text: {text}"
            response = model.generate_content(prompt)
            
            st.session_state.history.append({
                "title": uploaded_file.name, 
                "result": response.text,
                "full_text": text # Keep text for the Tutor
            })
            st.session_state.active_index = len(st.session_state.history) - 1
            st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

# --- COLUMN 2: RESULTS ---
active_data = st.session_state.history[st.session_state.active_index] if st.session_state.active_index is not None else None

with col2:
    if active_data:
        st.markdown('<div class="main-card">', unsafe_allow_html=True)
        st.markdown(f"#### 📖 {active_data['title']}")
        st.write(active_data['result'])
        st.markdown('</div>', unsafe_allow_html=True)
    else:
        st.info("Upload a PDF to see the study guide here.")

# --- COLUMN 3: DOUBT SOLVER (New!) ---
with col3:
    st.markdown('<div class="main-card">', unsafe_allow_html=True)
    st.markdown("### 💬 Doubt Solver")
    if active_data:
        user_query = st.text_input("Ask a question about this topic...")
        if user_query:
            with st.spinner("Tutor is thinking..."):
                tutor_prompt = f"Based on this text: {active_data['full_text']}\n\nAnswer the student's question simply: {user_query}"
                ans = model.generate_content(tutor_prompt)
                st.markdown('<div class="tutor-box">', unsafe_allow_html=True)
                st.markdown(f"**Aura says:** {ans.text}")
                st.markdown('</div>', unsafe_allow_html=True)
    else:
        st.caption("Summarize a file first to enable the AI Tutor.")
    st.markdown('</div>', unsafe_allow_html=True)

import streamlit as st
import fitz  # PyMuPDF
import google.generativeai as genai

# ==========================================
# 1. API CONFIGURATION
# ==========================================
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
    
    /* Only applied when content exists */
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
        font-size: 3rem !important;
        font-weight: 800 !important;
        margin-bottom: 20px;
    }
    
    .tutor-box {
        background: rgba(79, 172, 254, 0.1);
        border-radius: 15px;
        padding: 15px;
        border: 1px dashed #4facfe;
    }
    
    /* Hiding Streamlit's default empty padding */
    .block-container { padding-top: 3rem; }
    </style>
    """, unsafe_allow_html=True)

# ==========================================
# 4. BULLETPROOF MODEL PICKER
# ==========================================
@st.cache_resource
def get_model():
    try:
        available = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        if 'models/gemini-1.5-flash' in available: return genai.GenerativeModel('models/gemini-1.5-flash')
        return genai.GenerativeModel(available[0])
    except:
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

# Define columns
col1, col2, col3 = st.columns([1, 1.5, 1], gap="large")

# 📂 COLUMN 1: UPLOAD (Always visible but styled cleanly)
with col1:
    st.markdown("### 📂 Learning Material")
    uploaded_file = st.file_uploader("Upload a PDF to begin", type="pdf", label_visibility="collapsed")
    
    if uploaded_file and st.button("🚀 UNLOCK KNOWLEDGE", use_container_width=True):
        with st.spinner("🧠 Aura is processing..."):
            try:
                doc = fitz.open(stream=uploaded_file.read(), filetype="pdf")
                text = "".join([doc.load_page(i).get_text() for i in range(min(5, len(doc)))])
                
                prompt = f"Analyze this text and provide: A Master Concept (2 sentences), 4 Key Pillars, a simple Analogy, and a 2-question quiz: {text}"
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

# Check if there is data to display
active_data = st.session_state.history[st.session_state.active_index] if st.session_state.active_index is not None else None

# 📖 COLUMN 2: RESULTS (Only shows if file is processed)
with col2:
    if active_data:
        st.markdown(f"#### 📖 {active_data['title']}")
        st.markdown('<div class="main-card">', unsafe_allow_html=True)
        st.markdown(active_data['result'])
        st.markdown('</div>', unsafe_allow_html=True)
    elif not uploaded_file:
        st.info("👋 Welcome! Upload an academic PDF on the left to generate your interactive study guide.")

# 💬 COLUMN 3: DOUBT SOLVER (Only shows if file is processed)
with col3:
    if active_data:
        st.markdown("### 💬 Doubt Solver")
        st.markdown('<div class="main-card">', unsafe_allow_html=True)
        user_query = st.text_input("Ask a follow-up question...", placeholder="e.g., Explain the third pillar more deeply")
        if user_query:
            with st.spinner("Thinking..."):
                tutor_prompt = f"Using this context: {active_data['full_text']}\n\nAnswer this student question: {user_query}"
                ans = model.generate_content(tutor_prompt)
                st.markdown('<div class="tutor-box">', unsafe_allow_html=True)
                st.markdown(ans.text)
                st.markdown('</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

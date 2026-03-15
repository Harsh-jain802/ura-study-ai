import streamlit as st
import fitz  # PyMuPDF
import google.generativeai as genai

# ==========================================
# 1. API CONFIGURATION
# ==========================================
try:
    API_KEY = st.secrets["GEMINI_API_KEY"]
    genai.configure(api_key=API_KEY)
except Exception as e:
    st.error("API Key not found. Please set GEMINI_API_KEY in Streamlit secrets.")

# ==========================================
# 2. SESSION STATE
# ==========================================
if 'history' not in st.session_state:
    st.session_state.history = []  
if 'active_index' not in st.session_state:
    st.session_state.active_index = None

# ==========================================
# 3. PREMIUM UI CONFIG & STYLING (MOBILE OPTIMIZED)
# ==========================================
st.set_page_config(page_title="Aura Study AI", page_icon="✨", layout="wide")

st.markdown("""
    <style>
    /* Base Background */
    .stApp { background: radial-gradient(circle at top right, #1a1f2c, #0b0e14); }
    
    /* Sidebar */
    section[data-testid="stSidebar"] { 
        background-color: #0d1117 !important; 
        border-right: 1px solid #30363d; 
    }

    /* RESPONSIVE CONTAINER PADDING */
    .block-container {
        padding: 2rem 1rem !important; /* Mobile default */
    }
    @media (min-width: 768px) {
        .block-container {
            padding: 3rem 5rem !important; /* Desktop view */
        }
    }

    /* Content Cards */
    .content-card {
        background: rgba(22, 27, 34, 0.7);
        border: 1px solid #30363d;
        border-radius: 20px;
        padding: 20px; /* Reduced for mobile */
        backdrop-filter: blur(12px);
        margin-top: 20px;
        color: #e6edf3;
        line-height: 1.6;
    }
    @media (min-width: 768px) {
        .content-card { padding: 40px; }
    }
    
    /* RESPONSIVE HERO TEXT */
    .hero-text {
        background: linear-gradient(90deg, #4facfe, #00f2fe);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 800 !important;
        margin-bottom: 0px;
        font-size: 2.2rem !important; /* Smaller for mobile */
        line-height: 1.2;
    }
    @media (min-width: 768px) {
        .hero-text { font-size: 3.2rem !important; }
    }

    /* Modern Tab Styling */
    .stTabs [data-baseweb="tab-list"] { gap: 10px; }
    @media (min-width: 768px) {
        .stTabs [data-baseweb="tab-list"] { gap: 30px; }
    }
    .stTabs [data-baseweb="tab"] {
        font-size: 0.9rem;
        font-weight: 600;
        color: #94a3b8 !important;
    }
    @media (min-width: 768px) {
        .stTabs [data-baseweb="tab"] { font-size: 1.1rem; }
    }
    .stTabs [aria-selected="true"] { color: #4facfe !important; }

    .tutor-bubble {
        background: rgba(79, 172, 254, 0.1);
        padding: 15px;
        border-radius: 15px;
        border-left: 5px solid #4facfe;
        margin-top: 20px;
    }
    
    /* Image scaling for mobile */
    .welcome-img {
        width: 100%;
        max-width: 600px;
        height: auto;
    }
    </style>
    """, unsafe_allow_html=True)

# ==========================================
# 4. BULLETPROOF MODEL PICKER
# ==========================================
@st.cache_resource
def get_model():
    try:
        available = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        name = 'models/gemini-1.5-flash' if 'models/gemini-1.5-flash' in available else available[0]
        return genai.GenerativeModel(name)
    except:
        return genai.GenerativeModel('gemini-1.5-flash')

model = get_model()

# ==========================================
# 5. SIDEBAR
# ==========================================
with st.sidebar:
    st.markdown("<h2 style='color: #4facfe;'>✨ Aura AI</h2>", unsafe_allow_html=True)
    
    if st.button("➕ New Session", use_container_width=True):
        st.session_state.active_index = None
        st.rerun()
    
    st.write("---")
    st.markdown("### 📂 Upload Material")
    uploaded_file = st.file_uploader("Drop PDF here", type="pdf", label_visibility="collapsed")
    
    if uploaded_file and st.button("🚀 UNLOCK KNOWLEDGE", use_container_width=True):
        with st.spinner("🧠 Aura scanning..."):
            try:
                doc = fitz.open(stream=uploaded_file.read(), filetype="pdf")
                num_pages = min(30, len(doc))
                text = "".join([doc.load_page(i).get_text() for i in range(num_pages)])
                
                prompt = f"""
                Act as an expert academic professor. Provide a COMPREHENSIVE STUDY GUIDE for: {uploaded_file.name}
                Structure:
                # 📖 DETAILED ANALYSIS
                ## 🎯 THE BIG PICTURE (2-paragraph summary)
                ## 🔍 KEY THEMES & PILLARS (Detailed sections)
                ## 💡 ANALOGIES (For hard concepts)
                ## 📑 GLOSSARY (5-8 terms)
                ## 🎓 CRITICAL TAKEAWAYS
                ## ❓ CHALLENGE QUESTIONS
                
                TEXT: {text}
                """
                
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

active_data = st.session_state.history[st.session_state.active_index] if st.session_state.active_index is not None else None

if active_data:
    st.markdown(f"<p style='color: #94a3b8; font-size: 0.9rem;'>Resource: <b>{active_data['title']}</b></p>", unsafe_allow_html=True)
    
    tab1, tab2 = st.tabs(["📑 Guide", "💬 Tutor"])
    
    with tab1:
        st.markdown('<div class="content-card">', unsafe_allow_html=True)
        st.markdown(active_data['result'])
        st.markdown('</div>', unsafe_allow_html=True)
        
    with tab2:
        st.markdown('<div class="content-card">', unsafe_allow_html=True)
        st.markdown("### 💬 Ask a Doubt")
        user_query = st.chat_input("Ask Aura anything...")
        
        if user_query:
            with st.spinner("Thinking..."):
                tutor_prompt = f"Context: {active_data['full_text']}\nQuestion: {user_query}"
                ans = model.generate_content(tutor_prompt)
                st.markdown(f'<div class="tutor-bubble"><b>Aura:</b><br>{ans.text}</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

else:
    st.write("---")
    st.markdown("""
    ### 👋 Welcome to Aura.
    
    **To get started:**
    1. Open the **Sidebar** (arrow on top left).
    2. Upload a **PDF**.
    3. Click **Unlock Knowledge**.
    """)
    st.markdown('<img src="https://img.freepik.com/free-vector/digital-lifestyle-concept-illustration_114360-7327.jpg" class="welcome-img">', unsafe_allow_html=True)

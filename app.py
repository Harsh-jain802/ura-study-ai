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
    st.error("API Key not found.")

# ==========================================
# 2. SESSION STATE
# ==========================================
if 'history' not in st.session_state:
    st.session_state.history = []  
if 'active_index' not in st.session_state:
    st.session_state.active_index = None

# ==========================================
# 3. PREMIUM UI CONFIG & STYLING (THE MOBILE FIX)
# ==========================================
st.set_page_config(page_title="Aura Study AI", page_icon="✨", layout="wide")

st.markdown("""
    <style>
    /* 1. FORCED VISIBILITY: This makes sure text is ALWAYS readable on dark background */
    html, body, [data-testid="stWidgetLabel"], .stMarkdown, p, li {
        color: #e6edf3 !important; 
    }

    .stApp { 
        background: radial-gradient(circle at top right, #1a1f2c, #0b0e14); 
    }
    
    /* 2. MOBILE PADDING FIX */
    .block-container {
        padding: 1.5rem 1rem !important;
    }
    @media (min-width: 768px) {
        .block-container { padding: 3rem 5rem !important; }
    }

    /* 3. HERO TEXT (Responsive) */
    .hero-text {
        background: linear-gradient(90deg, #4facfe, #00f2fe);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 800 !important;
        font-size: 2.5rem !important;
        margin-bottom: 10px;
    }
    @media (min-width: 768px) {
        .hero-text { font-size: 3.5rem !important; }
    }

    /* 4. CONTENT CARDS */
    .content-card {
        background: rgba(22, 27, 34, 0.8);
        border: 1px solid #30363d;
        border-radius: 15px;
        padding: 20px;
        margin-top: 15px;
        color: #e6edf3 !important;
    }

    /* 5. SIDEBAR */
    section[data-testid="stSidebar"] { 
        background-color: #0d1117 !important; 
    }

    /* 6. TUTOR BUBBLE */
    .tutor-bubble {
        background: rgba(79, 172, 254, 0.15);
        padding: 15px;
        border-radius: 12px;
        border-left: 4px solid #4facfe;
        margin-top: 15px;
        color: white !important;
    }

    /* Image responsive */
    .welcome-img {
        width: 100%;
        max-width: 500px;
        height: auto;
        margin-top: 20px;
        border-radius: 10px;
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
# 5. SIDEBAR
# ==========================================
with st.sidebar:
    st.markdown("<h2 style='color: #4facfe;'>✨ Aura AI</h2>", unsafe_allow_html=True)
    
    if st.button("➕ New Session", use_container_width=True):
        st.session_state.active_index = None
        st.rerun()
    
    st.write("---")
    st.markdown("### 📂 Upload PDF")
    uploaded_file = st.file_uploader("Drop PDF here", type="pdf", label_visibility="collapsed")
    
    if uploaded_file and st.button("🚀 UNLOCK KNOWLEDGE", use_container_width=True):
        with st.spinner("Aura reading..."):
            try:
                doc = fitz.open(stream=uploaded_file.read(), filetype="pdf")
                text = "".join([doc.load_page(i).get_text() for i in range(min(30, len(doc)))])
                
                prompt = f"Act as an expert professor. Provide a detailed, deep analysis of this document. Break it down into Overview, Key Pillars, Analogies, Glossary, and Challenge Questions. TEXT: {text}"
                
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
    st.markdown("### 🕒 Recent")
    for i, item in enumerate(reversed(st.session_state.history)):
        real_idx = len(st.session_state.history) - 1 - i
        if st.button(f"📄 {item['title'][:15]}", key=f"h_{real_idx}", use_container_width=True):
            st.session_state.active_index = real_idx
            st.rerun()

# ==========================================
# 6. MAIN CONTENT
# ==========================================
st.markdown("<h1 class='hero-text'>Aura Study AI</h1>", unsafe_allow_html=True)

if st.session_state.active_index is not None:
    data = st.session_state.history[st.session_state.active_index]
    
    tab1, tab2 = st.tabs(["📑 Study Guide", "💬 AI Tutor"])
    
    with tab1:
        st.markdown('<div class="content-card">', unsafe_allow_html=True)
        st.markdown(data['result'])
        st.markdown('</div>', unsafe_allow_html=True)
        
    with tab2:
        st.markdown('<div class="content-card">', unsafe_allow_html=True)
        query = st.chat_input("Ask a doubt...")
        if query:
            with st.spinner("Aura thinking..."):
                ans = model.generate_content(f"Context: {data['full_text']}\nQuestion: {query}")
                st.markdown(f'<div class="tutor-bubble"><b>Aura:</b><br>{ans.text}</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

else:
    # UPDATED: Brighter welcome text for mobile
    st.markdown("### 👋 Welcome to Aura.")
    st.markdown("<p style='color: #cbd5e1;'>Aura is your advanced AI study companion. Please follow these steps:</p>", unsafe_allow_html=True)
    st.markdown("""
    <div style='color: #cbd5e1;'>
    1. Open the <b>Sidebar</b> (top-left arrow).<br>
    2. Upload your <b>Study PDF</b>.<br>
    3. Click <b>Unlock Knowledge</b>.
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown('<img src="https://img.freepik.com/free-vector/digital-lifestyle-concept-illustration_114360-7327.jpg" class="welcome-img">', unsafe_allow_html=True)

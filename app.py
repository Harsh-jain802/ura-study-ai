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
# 3. THE ULTIMATE MOBILE SIDEBAR & TEXT FIX
# ==========================================
st.set_page_config(page_title="Aura Study AI", page_icon="✨", layout="wide")

st.markdown("""
    <style>
    /* Global Force: White Text */
    html, body, [data-testid="stWidgetLabel"], .stMarkdown, p, li, span, label {
        color: #e6edf3 !important; 
    }

    .stApp { 
        background: radial-gradient(circle at top right, #1a1f2c, #0b0e14); 
    }
    
    /* SIDEBAR CONTAINER */
    section[data-testid="stSidebar"] {
        background-color: #0d1117 !important;
        border-right: 1px solid #30363d;
    }

    /* SIDEBAR BUTTONS (New Session / Unlock) */
    section[data-testid="stSidebar"] .stButton > button {
        background-color: #1f2937 !important;
        color: #4facfe !important;
        border: 1px solid #4facfe !important;
        border-radius: 8px !important;
        font-weight: bold !important;
        height: 45px !important;
    }

    /* FILE UPLOADER VISIBILITY FIX (Crucial for Mobile) */
    [data-testid="stFileUploader"] {
        background-color: #161b22 !important;
        border: 1px dashed #4facfe !important;
        padding: 10px !important;
        border-radius: 10px !important;
    }

    /* Target the invisible filename and size text */
    [data-testid="stFileUploaderFileName"], 
    [data-testid="stFileUploaderFileData"],
    [data-testid="stFileUploadDropzone"] div {
        color: #ffffff !important;
    }

    /* Target the Delete (X) button on uploaded files */
    [data-testid="stFileUploaderDeleteBtn"] {
        color: #ff4b4b !important;
        background-color: rgba(255,255,255,0.1) !important;
        border-radius: 50% !important;
    }

    /* MAIN SCREEN TEXT FIXES */
    .hero-text {
        background: linear-gradient(90deg, #4facfe, #00f2fe);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 800 !important;
        font-size: 2.2rem !important;
    }
    @media (min-width: 768px) {
        .hero-text { font-size: 3.5rem !important; }
    }

    .content-card {
        background: rgba(22, 27, 34, 0.95);
        border: 1px solid #30363d;
        border-radius: 15px;
        padding: 20px;
        margin-top: 15px;
        color: #e6edf3 !important;
    }

    /* Tab Label Colors */
    .stTabs [data-baseweb="tab"] p {
        color: #94a3b8 !important;
    }
    .stTabs [aria-selected="true"] p {
        color: #4facfe !important;
    }

    .tutor-bubble {
        background: rgba(79, 172, 254, 0.15);
        padding: 15px;
        border-radius: 12px;
        border-left: 4px solid #4facfe;
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
    st.markdown("<b style='color:#4facfe'>📂 Upload Study Material</b>", unsafe_allow_html=True)
    uploaded_file = st.file_uploader("Drop PDF", type="pdf", label_visibility="collapsed")
    
    if uploaded_file and st.button("🚀 UNLOCK KNOWLEDGE", use_container_width=True):
        with st.spinner("Analyzing..."):
            try:
                doc = fitz.open(stream=uploaded_file.read(), filetype="pdf")
                # Read up to 30 pages for deep analysis
                text = "".join([doc.load_page(i).get_text() for i in range(min(30, len(doc)))])
                
                prompt = f"""
                Act as a world-class academic professor. Create an EXHAUSTIVE and DEEP Study Guide.
                # 📖 DETAILED ANALYSIS: {uploaded_file.name}
                ## 🎯 THE BIG PICTURE (2 detailed paragraphs)
                ## 🔍 KEY THEMES & PILLARS (In-depth bullet points)
                ## 💡 COMPLEX ANALOGIES (For hard parts)
                ## 📑 GLOSSARY (Definitions of technical terms)
                ## 🎓 CRITICAL TAKEAWAYS (For exams)
                ## ❓ CHALLENGE QUESTIONS (Deep thinking)
                TEXT: {text}
                """
                
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
    st.markdown("<b style='color:#4facfe'>🕒 Recent History</b>", unsafe_allow_html=True)
    for i, item in enumerate(reversed(st.session_state.history)):
        real_idx = len(st.session_state.history) - 1 - i
        if st.button(f"📄 {item['title'][:18]}", key=f"h_{real_idx}", use_container_width=True):
            st.session_state.active_index = real_idx
            st.rerun()

# ==========================================
# 6. MAIN CONTENT
# ==========================================
st.markdown("<h1 class='hero-text'>Aura Study AI</h1>", unsafe_allow_html=True)

if st.session_state.active_index is not None:
    data = st.session_state.history[st.session_state.active_index]
    
    tab1, tab2 = st.tabs(["📑 Detailed Guide", "💬 AI Tutor"])
    
    with tab1:
        st.markdown('<div class="content-card">', unsafe_allow_html=True)
        st.markdown(data['result'])
        st.markdown('</div>', unsafe_allow_html=True)
        
    with tab2:
        st.markdown('<div class="content-card">', unsafe_allow_html=True)
        st.markdown("### 💬 Ask a Doubt")
        query = st.chat_input("Ask Aura...")
        if query:
            with st.spinner("Aura thinking..."):
                ans = model.generate_content(f"Context: {data['full_text']}\nQuestion: {query}")
                st.markdown(f'<div class="tutor-bubble"><b>Aura:</b><br><br>{ans.text}</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

else:
    st.markdown("### 👋 Welcome to Aura.")
    st.markdown("<p style='color: #cbd5e1;'>Follow these steps to start studying:</p>", unsafe_allow_html=True)
    st.markdown("""
    <div style='color: #ffffff; background: rgba(255,255,255,0.05); padding: 15px; border-radius: 10px; border: 1px solid #30363d;'>
    1. Open the <b>Sidebar</b> (top-left arrow).<br>
    2. Upload your <b>Study PDF</b>.<br>
    3. Click <b>Unlock Knowledge</b>.
    </div>
    """, unsafe_allow_html=True)
    st.image("https://img.freepik.com/free-vector/digital-lifestyle-concept-illustration_114360-7327.jpg")

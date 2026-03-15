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
# 3. PREMIUM UI CONFIG & STYLING (THE MOBILE SIDEBAR FIX)
# ==========================================
st.set_page_config(page_title="Aura Study AI", page_icon="✨", layout="wide")

st.markdown("""
    <style>
    /* Global Text Color Fix */
    html, body, [data-testid="stWidgetLabel"], .stMarkdown, p, li {
        color: #e6edf3 !important; 
    }

    .stApp { 
        background: radial-gradient(circle at top right, #1a1f2c, #0b0e14); 
    }
    
    /* ---------------- SIDEBAR MOBILE FIXES ---------------- */
    section[data-testid="stSidebar"] {
        background-color: #0d1117 !important;
        border-right: 1px solid #30363d;
    }

    /* Fix the "New Session" Button Visibility */
    section[data-testid="stSidebar"] .stButton > button {
        background-color: #1f2937 !important;
        color: #4facfe !important;
        border: 1px solid #30363d !important;
        border-radius: 10px !important;
        font-weight: 700 !important;
        width: 100% !important;
    }
    
    section[data-testid="stSidebar"] .stButton > button:hover {
        background-color: #4facfe !important;
        color: white !important;
    }

    /* Fix File Uploader (Browse files button and box) */
    [data-testid="stFileUploader"] {
        background-color: #161b22 !important;
        border: 1px dashed #30363d !important;
        border-radius: 10px !important;
        padding: 10px !important;
    }
    
    [data-testid="stFileUploader"] label {
        color: #4facfe !important;
        font-weight: 600 !important;
    }

    /* ---------------- MAIN STAGE FIXES ---------------- */
    .block-container {
        padding: 1.5rem 1rem !important;
    }
    @media (min-width: 768px) {
        .block-container { padding: 3rem 5rem !important; }
    }

    .hero-text {
        background: linear-gradient(90deg, #4facfe, #00f2fe);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 800 !important;
        font-size: 2.2rem !important;
        margin-bottom: 5px;
    }
    @media (min-width: 768px) {
        .hero-text { font-size: 3.5rem !important; }
    }

    .content-card {
        background: rgba(22, 27, 34, 0.9);
        border: 1px solid #30363d;
        border-radius: 15px;
        padding: 18px;
        margin-top: 15px;
        color: #e6edf3 !important;
    }

    .tutor-bubble {
        background: rgba(79, 172, 254, 0.15);
        padding: 15px;
        border-radius: 12px;
        border-left: 4px solid #4facfe;
        margin-top: 15px;
    }

    /* Recent History buttons in sidebar */
    .history-btn {
        text-align: left !important;
        font-size: 0.85rem !important;
        color: #8b949e !important;
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
    st.markdown("<h2 style='color: #4facfe; margin-bottom: 20px;'>✨ Aura AI</h2>", unsafe_allow_html=True)
    
    if st.button("➕ New Session"):
        st.session_state.active_index = None
        st.rerun()
    
    st.write("---")
    st.markdown("### 📂 Upload PDF")
    uploaded_file = st.file_uploader("Drop PDF here", type="pdf", label_visibility="collapsed")
    
    if uploaded_file and st.button("🚀 UNLOCK"):
        with st.spinner("Analyzing..."):
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
        if st.button(f"📄 {item['title'][:15]}", key=f"h_{real_idx}"):
            st.session_state.active_index = real_idx
            st.rerun()

# ==========================================
# 6. MAIN CONTENT
# ==========================================
st.markdown("<h1 class='hero-text'>Aura Study AI</h1>", unsafe_allow_html=True)

if st.session_state.active_index is not None:
    data = st.session_state.history[st.session_state.active_index]
    st.markdown(f"<p style='color: #8b949e; font-size:0.9rem'>Reading: {data['title']}</p>", unsafe_allow_html=True)
    
    tab1, tab2 = st.tabs(["📑 Guide", "💬 Tutor"])
    
    with tab1:
        st.markdown('<div class="content-card">', unsafe_allow_html=True)
        st.markdown(data['result'])
        st.markdown('</div>', unsafe_allow_html=True)
        
    with tab2:
        st.markdown('<div class="content-card">', unsafe_allow_html=True)
        query = st.chat_input("Ask Aura...")
        if query:
            with st.spinner("Aura thinking..."):
                ans = model.generate_content(f"Context: {data['full_text']}\nQuestion: {query}")
                st.markdown(f'<div class="tutor-bubble"><b>Aura:</b><br>{ans.text}</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

else:
    st.markdown("### 👋 Welcome.")
    st.markdown("<p style='color: #cbd5e1;'>Aura is your advanced AI study companion.</p>", unsafe_allow_html=True)
    st.markdown("""
    <div style='color: #cbd5e1; background: rgba(255,255,255,0.05); padding: 15px; border-radius: 10px;'>
    1. Click the <b>Top-Left Arrow</b> to open the Sidebar.<br>
    2. Upload your <b>PDF</b>.<br>
    3. Click <b>Unlock</b> to start.
    </div>
    """, unsafe_allow_html=True)
    st.image("https://img.freepik.com/free-vector/digital-lifestyle-concept-illustration_114360-7327.jpg")

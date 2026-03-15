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
# 3. ULTIMATE MOBILE CSS FIX
# ==========================================
st.set_page_config(page_title="Aura Study AI", page_icon="✨", layout="wide")

st.markdown("""
    <style>
    /* 1. Overall Dark Theme */
    .stApp { background: radial-gradient(circle at top right, #1a1f2c, #0b0e14); }
    
    /* 2. Sidebar Color */
    section[data-testid="stSidebar"] {
        background-color: #0d1117 !important;
        border-right: 1px solid #30363d;
    }

    /* 3. FIX: Sidebar Buttons (New Session / Unlock) */
    /* This forces the text inside buttons to be white and readable */
    section[data-testid="stSidebar"] .stButton button p {
        color: white !important;
        font-weight: bold !important;
    }
    section[data-testid="stSidebar"] .stButton button {
        background-color: #1f2937 !important;
        border: 1px solid #4facfe !important;
    }

    /* 4. FIX: File Uploader Box */
    /* We make the box DARK so white text shows up */
    [data-testid="stFileUploader"] {
        background-color: #0d1117 !important;
    }
    
    /* The 'Drag and drop' area */
    [data-testid="stFileUploadDropzone"] {
        background-color: #161b22 !important;
        border: 1px dashed #4facfe !important;
    }

    /* Force all text inside uploader to be white */
    [data-testid="stFileUploadDropzone"] p, 
    [data-testid="stFileUploadDropzone"] span,
    [data-testid="stFileUploaderFileName"],
    [data-testid="stFileUploaderFileData"] {
        color: white !important;
    }

    /* 5. FIX: 'Browse Files' Button */
    [data-testid="stFileUploadDropzone"] button {
        background-color: #1f2937 !important;
        color: white !important;
        border: 1px solid #4facfe !important;
    }

    /* 6. Main Content Text */
    .hero-text {
        background: linear-gradient(90deg, #4facfe, #00f2fe);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 800 !important;
        font-size: 2rem !important;
    }
    @media (min-width: 768px) {
        .hero-text { font-size: 3.5rem !important; }
    }

    .content-card {
        background: rgba(22, 27, 34, 0.9);
        border: 1px solid #30363d;
        border-radius: 15px;
        padding: 20px;
        color: white !important;
    }
    
    /* Force main markdown text white */
    .stMarkdown p, .stMarkdown li, .stMarkdown h1, .stMarkdown h2, .stMarkdown h3 {
        color: white !important;
    }

    /* Tabs visibility */
    .stTabs [data-baseweb="tab"] p { color: #94a3b8 !important; }
    .stTabs [aria-selected="true"] p { color: #4facfe !important; }
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
    st.markdown("<b style='color:#4facfe'>📂 Upload PDF</b>", unsafe_allow_html=True)
    uploaded_file = st.file_uploader("Upload", type="pdf", label_visibility="collapsed")
    
    if uploaded_file and st.button("🚀 UNLOCK NOW", use_container_width=True):
        with st.spinner("Analyzing..."):
            try:
                doc = fitz.open(stream=uploaded_file.read(), filetype="pdf")
                text = "".join([doc.load_page(i).get_text() for i in range(min(30, len(doc)))])
                
                prompt = f"Act as an expert professor. Create a highly detailed study guide with Overview, Key Themes, Analogies, Glossary, and Questions. PDF Name: {uploaded_file.name}. TEXT: {text}"
                
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
    st.markdown("<b style='color:#4facfe'>🕒 Recent</b>", unsafe_allow_html=True)
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
        query = st.chat_input("Ask anything...")
        if query:
            with st.spinner("Aura thinking..."):
                ans = model.generate_content(f"Context: {data['full_text']}\nQuestion: {query}")
                st.markdown(f"<div style='background: rgba(79,172,254,0.1); padding: 15px; border-radius: 10px; border-left: 4px solid #4facfe; color: white;'><b>Aura:</b><br>{ans.text}</div>", unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

else:
    st.markdown("<h3 style='color: white;'>👋 Welcome to Aura.</h3>", unsafe_allow_html=True)
    st.markdown("""
    <div style='color: #cbd5e1; background: rgba(255,255,255,0.05); padding: 15px; border-radius: 10px; border: 1px solid #30363d;'>
    1. Open the <b>Sidebar</b>.<br>
    2. Upload your <b>PDF</b>.<br>
    3. Click <b>Unlock Now</b>.
    </div>
    """, unsafe_allow_html=True)
    st.image("https://img.freepik.com/free-vector/digital-lifestyle-concept-illustration_114360-7327.jpg")

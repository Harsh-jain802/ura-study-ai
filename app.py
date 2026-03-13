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
    
    /* Sidebar Styling */
    section[data-testid="stSidebar"] { 
        background-color: #0d1117 !important; 
        border-right: 1px solid #30363d; 
    }

    /* Main Container Padding */
    .block-container { padding: 3rem 5rem !important; }

    /* Content Cards */
    .content-card {
        background: rgba(22, 27, 34, 0.7);
        border: 1px solid #30363d;
        border-radius: 20px;
        padding: 40px;
        backdrop-filter: blur(12px);
        margin-top: 20px;
    }
    
    .hero-text {
        background: linear-gradient(90deg, #4facfe, #00f2fe);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 3.2rem !important;
        font-weight: 800 !important;
        margin-bottom: 0px;
    }

    /* Modern Tab Styling */
    .stTabs [data-baseweb="tab-list"] { gap: 30px; }
    .stTabs [data-baseweb="tab"] {
        font-size: 1.1rem;
        font-weight: 600;
        color: #94a3b8 !important;
    }
    .stTabs [aria-selected="true"] { color: #4facfe !important; }

    .tutor-bubble {
        background: rgba(79, 172, 254, 0.1);
        padding: 20px;
        border-radius: 15px;
        border-left: 5px solid #4facfe;
        margin-top: 20px;
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
# 5. SIDEBAR (The Control Center)
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
        with st.spinner("🧠 Aura is reading..."):
            try:
                doc = fitz.open(stream=uploaded_file.read(), filetype="pdf")
                text = "".join([doc.load_page(i).get_text() for i in range(min(5, len(doc)))])
                
                prompt = f"""
                Analyze this text and provide:
                1. 🎯 THE BIG PICTURE: 2 simple sentences.
                2. 📑 KEY PILLARS: 4 bullet points.
                3. 💡 ANALOGY: A simple comparison.
                4. ❓ SELF-TEST: 2 questions.

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
    st.markdown("### 🕒 Recent History")
    for i, item in enumerate(reversed(st.session_state.history)):
        real_idx = len(st.session_state.history) - 1 - i
        if st.button(f"📄 {item['title'][:18]}...", key=f"h_{real_idx}", use_container_width=True):
            st.session_state.active_index = real_idx
            st.rerun()

# ==========================================
# 6. MAIN CONTENT (The Stage)
# ==========================================
st.markdown("<h1 class='hero-text'>Aura Study AI</h1>", unsafe_allow_html=True)

active_data = st.session_state.history[st.session_state.active_index] if st.session_state.active_index is not None else None

if active_data:
    st.markdown(f"<p style='color: #94a3b8;'>Current Resource: <b>{active_data['title']}</b></p>", unsafe_allow_html=True)
    
    # Using Tabs to save space and organize features
    tab1, tab2 = st.tabs(["📑 Study Guide", "💬 AI Doubt Solver"])
    
    with tab1:
        st.markdown('<div class="content-card">', unsafe_allow_html=True)
        st.markdown(active_data['result'])
        st.markdown('</div>', unsafe_allow_html=True)
        
    with tab2:
        st.markdown('<div class="content-card">', unsafe_allow_html=True)
        st.markdown("### 💬 Ask a Doubt")
        st.write("Ask anything about this document and Aura will explain it simply.")
        
        user_query = st.chat_input("Explain the concept of...")
        
        if user_query:
            with st.spinner("Tutor is thinking..."):
                tutor_prompt = f"Context: {active_data['full_text']}\n\nQuestion: {user_query}"
                ans = model.generate_content(tutor_prompt)
                st.markdown(f'<div class="tutor-bubble"><b>Aura says:</b><br><br>{ans.text}</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

else:
    # Empty State
    st.write("---")
    st.markdown("""
    ### 👋 Welcome to Aura.
    Your study material is currently empty. 
    
    **To get started:**
    1. Look at the **Sidebar** on the left.
    2. Upload a **PDF** (Textbook, Research Paper, or Notes).
    3. Click **Unlock Knowledge**.
    """)
    st.image("https://img.freepik.com/free-vector/digital-lifestyle-concept-illustration_114360-7327.jpg", width=600)

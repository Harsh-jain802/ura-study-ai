import streamlit as st
import fitz  # PyMuPDF
import google.generativeai as genai

# ==========================================
# 1. API CONFIGURATION
# ==========================================
# Instead of hardcoding the key, we pull it from the cloud "Secrets"
API_KEY = st.secrets["GEMINI_API_KEY"] # 🚨 PASTE YOUR KEY HERE
genai.configure(api_key=API_KEY)

# ==========================================
# 2. SESSION STATE (The "Memory" of the app)
# ==========================================
if 'history' not in st.session_state:
    st.session_state.history = []  # Stores list of {title, result}
if 'active_index' not in st.session_state:
    st.session_state.active_index = None # Which history item is currently viewed

# ==========================================
# 3. PREMIUM UI CONFIG & STYLING
# ==========================================
st.set_page_config(page_title="Aura Study AI", page_icon="✨", layout="wide")

st.markdown("""
    <style>
    .stApp { background: radial-gradient(circle at top right, #1a1f2c, #0b0e14); }
    section[data-testid="stSidebar"] { 
        background-color: #0d1117 !important; 
        border-right: 1px solid #30363d; 
    }
    
    /* Sidebar History Button Styling */
    .stSidebar [data-testid="stVerticalBlock"] button {
        background-color: transparent !important;
        border: 1px solid #30363d !important;
        color: #94a3b8 !important;
        text-align: left !important;
        padding: 10px !important;
        font-size: 0.85rem !important;
    }
    .stSidebar [data-testid="stVerticalBlock"] button:hover {
        border-color: #4facfe !important;
        color: #4facfe !important;
    }

    .main-card {
        background: rgba(22, 27, 34, 0.8);
        border: 1px solid #3a7bd5;
        border-radius: 20px;
        padding: 30px;
        backdrop-filter: blur(12px);
    }
    
    .hero-text {
        background: linear-gradient(90deg, #4facfe, #00f2fe);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 3rem !important;
        font-weight: 800 !important;
    }

    .quiz-box {
        background: rgba(79, 172, 254, 0.1);
        padding: 15px;
        border-left: 5px solid #4facfe;
        border-radius: 10px;
        margin: 10px 0;
    }
    </style>
    """, unsafe_allow_html=True)

# ==========================================
# 4. MODEL PICKER
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
# 5. SIDEBAR (History Management)
# ==========================================
with st.sidebar:
    st.markdown("<h2 style='color: #4facfe;'>✨ Aura Study</h2>", unsafe_allow_html=True)
    
    # NEW SESSION BUTTON
    if st.button("➕ New Study Session", use_container_width=True):
        st.session_state.active_index = None
        st.rerun()
    
    st.write("---")
    st.markdown("### 🕒 Recent History")
    
    if not st.session_state.history:
        st.caption("No history yet. Upload a file to start!")
    else:
        # Loop through history and create buttons for each item
        for i, item in enumerate(reversed(st.session_state.history)):
            # Real index is total length - 1 - reversed index
            real_idx = len(st.session_state.history) - 1 - i
            if st.button(f"📄 {item['title'][:20]}...", key=f"hist_{real_idx}", use_container_width=True):
                st.session_state.active_index = real_idx
                st.rerun()

# ==========================================
# 6. MAIN CONTENT
# ==========================================
st.markdown("<h1 class='hero-text'>Aura Study AI</h1>", unsafe_allow_html=True)

# Determine what to show in the main window
active_data = None
if st.session_state.active_index is not None:
    active_data = st.session_state.history[st.session_state.active_index]

col1, col2 = st.columns([1, 1.8], gap="large")

with col1:
    st.markdown('<div class="main-card">', unsafe_allow_html=True)
    st.markdown("### 📂 Upload Material")
    uploaded_file = st.file_uploader("Drop PDF here", type="pdf")
    
    if uploaded_file and st.button("🚀 UNLOCK KNOWLEDGE"):
        with st.spinner("🧠 Aura is reading..."):
            try:
                doc = fitz.open(stream=uploaded_file.read(), filetype="pdf")
                text = "".join([doc.load_page(i).get_text() for i in range(min(5, len(doc)))])
                
                prompt = f"""
                Analyze this text and create:
                1. 🎯 THE BIG PICTURE: 2 simple sentences.
                2. 💡 ANALOGY: A real-world comparison.
                3. 📑 KEY TAKEAWAYS: 4 bullet points.
                4. ❓ QUIZ: Create 2 Multiple Choice Questions (Q1, Q2) with options A,B,C. 
                   Format: Q1: [Question] [Options] ANSWER: [Option]

                TEXT: {text}
                """
                
                response = model.generate_content(prompt)
                
                # Add to history
                new_entry = {"title": uploaded_file.name, "result": response.text}
                st.session_state.history.append(new_entry)
                st.session_state.active_index = len(st.session_state.history) - 1
                st.balloons()
                st.rerun()
                
            except Exception as e:
                st.error(f"Error: {e}")
    st.markdown('</div>', unsafe_allow_html=True)

with col2:
    if active_data:
        st.markdown(f"### 📖 Viewing: **{active_data['title']}**")
        st.markdown('<div class="main-card">', unsafe_allow_html=True)
        tab1, tab2 = st.tabs(["📑 Master Guide", "❓ Quiz & Knowledge"])
        
        # Split result for better display
        parts = active_data['result'].split("Q1:")
        guide = parts[0]
        quiz = "Q1:" + parts[1] if len(parts) > 1 else "No quiz found."

        with tab1:
            st.markdown(guide)
        with tab2:
            st.markdown("### 🧠 Self-Test")
            st.markdown(f'<div class="quiz-box">{quiz.split("ANSWER:")[0]}</div>', unsafe_allow_html=True)
            with st.expander("👁️ Reveal Answer"):
                if "ANSWER:" in quiz:
                    st.success(f"Correct Answer: {quiz.split('ANSWER:')[1].strip()}")
        st.markdown('</div>', unsafe_allow_html=True)
    else:
        st.image("https://img.freepik.com/free-vector/digital-lifestyle-concept-illustration_114360-7327.jpg", width=450)
        st.info("Select a previous session from the sidebar or upload a new file to begin.")

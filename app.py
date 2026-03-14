import streamlit as st
import fitz  # PyMuPDF
import google.generativeai as genai
import time

# ==========================================
# 1. API CONFIGURATION & ROBUST MODEL LOADING
# ==========================================
try:
    API_KEY = st.secrets["GEMINI_API_KEY"]
    genai.configure(api_key=API_KEY)
except Exception:
    st.error("⚠️ API Key not found! Add GEMINI_API_KEY to Streamlit Secrets.")

@st.cache_resource
def get_working_model():
    """
    Tries multiple model names to bypass the 404 error 
    caused by library version mismatches.
    """
    # Order of preference
    models_to_try = ['gemini-1.5-flash', 'models/gemini-1.5-flash', 'gemini-pro']
    
    for m_name in models_to_try:
        try:
            model = genai.GenerativeModel(m_name)
            # Quick validation call
            model.generate_content("Hi", generation_config={"max_output_tokens": 1})
            return model
        except Exception:
            continue
    return genai.GenerativeModel('gemini-pro') # Last resort

model = get_working_model()

# ==========================================
# 2. SESSION STATE INITIALIZATION
# ==========================================
if 'history' not in st.session_state:
    st.session_state.history = []
if 'active_index' not in st.session_state:
    st.session_state.active_index = None
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = {} # Keyed by document index

# ==========================================
# 3. PREMIUM UI & STYLING
# ==========================================
st.set_page_config(page_title="Aura Study AI", page_icon="✨", layout="wide")

st.markdown("""
<style>
    .stApp { background: #0b0e14; color: #e6edf3; }
    section[data-testid="stSidebar"] { background-color: #0d1117 !important; border-right: 1px solid #30363d; }
    .content-card {
        background: rgba(22, 27, 34, 0.9);
        border: 1px solid #30363d;
        border-radius: 15px;
        padding: 25px;
        margin-bottom: 20px;
        color: #adbac7;
    }
    .hero-text {
        background: linear-gradient(90deg, #4facfe, #00f2fe);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 3rem;
        font-weight: 800;
        margin-bottom: 5px;
    }
    .stTabs [data-baseweb="tab-list"] { gap: 20px; }
    .stTabs [data-baseweb="tab"] { font-weight: 600; color: #94a3b8 !important; }
    .stTabs [aria-selected="true"] { color: #4facfe !important; border-bottom-color: #4facfe !important; }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 4. SIDEBAR LOGIC (Upload & Preferences)
# ==========================================
with st.sidebar:
    st.markdown("<h2 style='color: #4facfe;'>✨ Aura AI</h2>", unsafe_allow_html=True)
    
    if st.button("➕ New Session", use_container_width=True):
        st.session_state.active_index = None
        st.rerun()

    st.write("---")
    st.markdown("### 📂 Learning Material")
    uploaded_file = st.file_uploader("Upload PDF", type="pdf", label_visibility="collapsed")
    
    # PROBLEM STATEMENT FEATURE: Learning Style Selection
    learn_style = st.selectbox("🎯 Adaptation Style", 
                               ["Simplified (Default)", "Visual Learner", "Step-by-Step", "Summarized"])

    if uploaded_file:
        file_already_processed = any(h['title'] == uploaded_file.name for h in st.session_state.history)
        
        if not file_already_processed:
            if st.button("🚀 UNLOCK KNOWLEDGE", use_container_width=True):
                with st.spinner("🧠 Aura is simplifying content..."):
                    try:
                        # Extract PDF Text
                        doc = fitz.open(stream=uploaded_file.read(), filetype="pdf")
                        text = "".join([page.get_text() for page in doc][:10]) 
                        
                        prompt = f"""
                        You are a world-class tutor. Transform this material for a {learn_style}.
                        
                        1. 🎯 THE BIG PICTURE: Explain the core concept in 1 simple sentence.
                        2. 📑 KEY PILLARS: 4 essential points.
                        3. 💡 ANALOGY: A relatable real-world comparison.
                        4. 🎨 VISUAL DESCRIPTION: Describe exactly how a diagram of this should look to help a visual learner.

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
                        st.error(f"Analysis Error: {e}")
        else:
            st.info("File already processed. See History below.")

    st.write("---")
    st.markdown("### 🕒 Recent History")
    for i, item in enumerate(reversed(st.session_state.history)):
        real_idx = len(st.session_state.history) - 1 - i
        if st.button(f"📄 {item['title'][:20]}...", key=f"h_{real_idx}", use_container_width=True):
            st.session_state.active_index = real_idx
            st.rerun()

# ==========================================
# 5. MAIN CONTENT AREA
# ==========================================
st.markdown("<h1 class='hero-text'>Aura Study AI</h1>", unsafe_allow_html=True)

if st.session_state.active_index is not None:
    active_data = st.session_state.history[st.session_state.active_index]
    st.caption(f"Current Session: {active_data['title']}")

    tab1, tab2 = st.tabs(["📑 Simplified Guide", "💬 Interactive Tutor"])

    with tab1:
        st.markdown('<div class="content-card">', unsafe_allow_html=True)
        st.markdown(active_data['result'])
        st.markdown('</div>', unsafe_allow_html=True)
        
    with tab2:
        st.markdown("### 💬 Ask a Doubt")
        
        idx = st.session_state.active_index
        if idx not in st.session_state.chat_history:
            st.session_state.chat_history[idx] = []

        # Display Chat History
        for chat in st.session_state.chat_history[idx]:
            with st.chat_message(chat["role"]):
                st.markdown(chat["content"])

        # Chat Input
        if user_query := st.chat_input("Explain the part about..."):
            with st.chat_message("user"):
                st.markdown(user_query)
            st.session_state.chat_history[idx].append({"role": "user", "content": user_query})
            
            try:
                with st.chat_message("assistant"):
                    with st.spinner("Thinking..."):
                        tutor_prompt = f"Context: {active_data['full_text'][:4000]}\n\nQuestion: {user_query}\n\nExplain simply as a tutor."
                        ans = model.generate_content(tutor_prompt)
                        st.markdown(ans.text)
                        st.session_state.chat_history[idx].append({"role": "assistant", "content": ans.text})
            except Exception:
                st.error("AI is currently overloaded. Please wait 10 seconds.")

else:
    # Landing View
    st.write("---")
    col1, col2 = st.columns([1, 1])
    with col1:
        st.markdown("""
        ### Transform complex learning into simple insights.
        Aura helps you overcome text-heavy materials by:
        - 🧩 Breaking down complex jargon.
        - 🖼️ Describing visual diagrams for visual learners.
        - 🤖 Providing a 24/7 Interactive AI Tutor.
        
        **Get Started:**
        Upload a PDF (Textbook or Notes) in the sidebar.
        """)
    with col2:
        st.image("https://img.freepik.com/free-vector/ai-technology-concept-illustration_114360-7052.jpg")

st.markdown("<br><br><center style='color: #4b5563; font-size: 0.8rem;'>Built for Accessible Education | Powered by Aura AI</center>", unsafe_allow_html=True)

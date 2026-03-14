import streamlit as st
import fitz  # PyMuPDF
import google.generativeai as genai
import time

# ==========================================
# 1. API CONFIGURATION
# ==========================================
st.cache_resource.clear()

if "GEMINI_API_KEY" not in st.secrets:
    st.error("❌ Add GEMINI_API_KEY to Secrets!")
    st.stop()

genai.configure(api_key=st.secrets["GEMINI_API_KEY"])

@st.cache_resource
def get_model():
    # 'gemini-1.5-flash' is the fastest and has the most free quota
    return genai.GenerativeModel('gemini-1.5-flash')

model = get_model()

# ==========================================
# 2. SESSION STATE (Saves data so you don't re-call the API)
# ==========================================
if 'history' not in st.session_state:
    st.session_state.history = []
if 'active_index' not in st.session_state:
    st.session_state.active_index = None

# ==========================================
# 3. UI & STYLING
# ==========================================
st.set_page_config(page_title="Aura Study AI", page_icon="✨", layout="wide")

st.markdown("""
<style>
    .stApp { background: #0b0e14; color: white; }
    .hero-text { background: linear-gradient(90deg, #4facfe, #00f2fe); -webkit-background-clip: text; -webkit-text-fill-color: transparent; font-size: 3rem; font-weight: 800; }
    .content-card { background: rgba(255, 255, 255, 0.05); border: 1px solid #30363d; border-radius: 15px; padding: 25px; margin-top: 20px; }
    .wait-box { background: #1e1e1e; border: 1px solid #ffaa00; padding: 15px; border-radius: 10px; color: #ffaa00; text-align: center; }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 4. SIDEBAR
# ==========================================
with st.sidebar:
    st.markdown("<h2 style='color: #4facfe;'>✨ Aura AI</h2>", unsafe_allow_html=True)
    
    if st.button("➕ New Session", use_container_width=True):
        st.session_state.active_index = None
        st.rerun()

    st.write("---")
    uploaded_file = st.file_uploader("Upload PDF", type="pdf")
    
    # Problem Statement: Adapt for different learners
    learner_style = st.selectbox("Adapt for:", ["Visual Learner", "Simplified Basics", "Exam Summary"])

    if uploaded_file:
        # Check if we already processed this file in this session
        already_processed = any(h['title'] == uploaded_file.name for h in st.session_state.history)
        
        if not already_processed:
            if st.button("🚀 UNLOCK KNOWLEDGE", use_container_width=True):
                with st.spinner("Aura is processing..."):
                    try:
                        doc = fitz.open(stream=uploaded_file.read(), filetype="pdf")
                        # Read ONLY first 3 pages to save quota tokens
                        text = "".join([page.get_text() for page in doc[:3]])
                        
                        prompt = f"""
                        Target Learner: {learner_style}. 
                        Material: {text[:3000]}
                        Task: 1. Core concept (1 sentence) 2. 3 Main points 3. A real-world analogy.
                        """
                        
                        response = model.generate_content(prompt)
                        
                        st.session_state.history.append({
                            "title": uploaded_file.name,
                            "content": response.text,
                            "raw": text[:2000] # Keep a small context for the tutor
                        })
                        st.session_state.active_index = len(st.session_state.history) - 1
                        st.balloons()
                        st.rerun()
                        
                    except Exception as e:
                        if "429" in str(e):
                            st.markdown('<div class="wait-box">🚦 GOOGLE SPEED LIMIT REACHED<br>Please wait 60 seconds. The Free Tier needs a break.</div>', unsafe_allow_html=True)
                        else:
                            st.error(f"Error: {e}")
        else:
            st.info("File already simplified! See History below.")

    st.write("---")
    for i, item in enumerate(reversed(st.session_state.history)):
        real_idx = len(st.session_state.history) - 1 - i
        if st.button(f"📄 {item['title'][:15]}", key=f"h_{real_idx}"):
            st.session_state.active_index = real_idx
            st.rerun()

# ==========================================
# 5. MAIN AREA
# ==========================================
st.markdown("<h1 class='hero-text'>Aura Study AI</h1>", unsafe_allow_html=True)

if st.session_state.active_index is not None:
    data = st.session_state.history[st.session_state.active_index]
    
    tab1, tab2 = st.tabs(["📑 Study Guide", "💬 Doubt Solver"])
    
    with tab1:
        st.markdown('<div class="content-card">', unsafe_allow_html=True)
        st.markdown(data['content'])
        st.markdown('</div>', unsafe_allow_html=True)
        
    with tab2:
        st.subheader("💬 Ask a Question")
        user_q = st.chat_input("What is...")
        if user_q:
            st.chat_message("user").write(user_q)
            try:
                # We send very little text to the AI to avoid the quota limit
                ans = model.generate_content(f"Use this info: {data['raw']}\nQuestion: {user_q}")
                st.chat_message("assistant").write(ans.text)
            except Exception as e:
                if "429" in str(e):
                    st.warning("🚦 Speed limit! Please wait 30 seconds before asking another question.")
                else:
                    st.error("AI is temporarily unavailable.")
else:
    st.info("👈 Upload a PDF in the sidebar to begin.")

import streamlit as st
import fitz  # PyMuPDF
import google.generativeai as genai

# ==========================================
# 1. API CONFIGURATION
# ==========================================
try:
    API_KEY = st.secrets["GEMINI_API_KEY"]
    genai.configure(api_key=API_KEY)
except:
    st.error("API Key not found in Streamlit Secrets!")

# THE FIX: Using the most stable string name
# We don't use "models/..." prefix here because the 
# newer library handles that automatically.
@st.cache_resource
def get_model():
    try:
        # 'gemini-1.5-flash' is the standard stable model
        return genai.GenerativeModel('gemini-1.5-flash')
    except:
        # Fallback to the older stable version
        return genai.GenerativeModel('gemini-pro')

model = get_model()

# ==========================================
# 2. SESSION STATE
# ==========================================
if 'history' not in st.session_state:
    st.session_state.history = []
if 'active_index' not in st.session_state:
    st.session_state.active_index = None

# ==========================================
# 3. UI & STYLING (Aura Theme)
# ==========================================
st.set_page_config(page_title="Aura Study AI", page_icon="✨", layout="wide")

st.markdown("""
<style>
    .stApp { background: #0b0e14; color: white; }
    .hero-text { background: linear-gradient(90deg, #4facfe, #00f2fe); -webkit-background-clip: text; -webkit-text-fill-color: transparent; font-size: 3rem; font-weight: 800; }
    .content-card { background: rgba(255, 255, 255, 0.05); border: 1px solid #30363d; border-radius: 15px; padding: 20px; }
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
    uploaded_file = st.file_uploader("Upload PDF Study Material", type="pdf")
    
    # Addressing Problem Statement: Learning Styles
    style = st.radio("Adapt for:", ["Simplified (General)", "Visual Learner (Diagram focus)", "Auditory (Text-to-Speech Ready)"])

    if uploaded_file and st.button("🚀 UNLOCK KNOWLEDGE"):
        with st.spinner("Aura is simplifying..."):
            try:
                # Extracting text
                doc = fitz.open(stream=uploaded_file.read(), filetype="pdf")
                text = ""
                for page in doc[:5]: # Limit to 5 pages for speed/safety
                    text += page.get_text()
                
                # The Prompt
                prompt = f"""
                You are a world-class educational tutor. Analyze the following text:
                1. BIG PICTURE: 1 sentence summary.
                2. KEY PILLARS: 3 simplified points.
                3. ANALOGY: A simple real-world comparison.
                4. VISUAL: Describe a diagram that explains this.
                
                Style: {style}
                Text: {text}
                """
                
                response = model.generate_content(prompt)
                
                st.session_state.history.append({
                    "title": uploaded_file.name,
                    "content": response.text,
                    "raw": text
                })
                st.session_state.active_index = len(st.session_state.history) - 1
                st.rerun()
            except Exception as e:
                st.error(f"Error: {e}")

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
    
    tab1, tab2 = st.tabs(["📑 Simplified Guide", "💬 Doubt Solver"])
    
    with tab1:
        st.markdown('<div class="content-card">', unsafe_allow_html=True)
        st.markdown(data['content'])
        st.markdown('</div>', unsafe_allow_html=True)
        
    with tab2:
        st.markdown("### 💬 Ask anything about this material")
        user_q = st.chat_input("What is this part about?")
        if user_q:
            st.chat_message("user").write(user_q)
            ans = model.generate_content(f"Context: {data['raw'][:3000]}\nQuestion: {user_q}")
            st.chat_message("assistant").write(ans.text)
else:
    st.info("👈 Upload a PDF in the sidebar to get started!")

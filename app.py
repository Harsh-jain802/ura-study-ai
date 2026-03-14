import streamlit as st
import fitz  # PyMuPDF
import google.generativeai as genai

# ==========================================
# 1. API CONFIG & AUTOMATIC MODEL DISCOVERY
# ==========================================
try:
    API_KEY = st.secrets["GEMINI_API_KEY"]
    genai.configure(api_key=API_KEY)
except Exception:
    st.error("⚠️ API Key not found in Secrets!")

@st.cache_resource
def get_best_available_model():
    """
    This function checks your API key to see which models are actually 
    available to you, preventing the 404 error.
    """
    try:
        # Get list of models available to your specific API Key
        available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        
        # Priority list: We want 1.5 Flash, then 1.5 Pro, then 1.0 Pro
        target_models = [
            'models/gemini-1.5-flash', 
            'models/gemini-1.5-pro', 
            'models/gemini-pro'
        ]
        
        for target in target_models:
            if target in available_models:
                return genai.GenerativeModel(target)
        
        # If no target found, just pick the first available one
        return genai.GenerativeModel(available_models[0])
    except Exception as e:
        # Absolute fallback if listing fails
        return genai.GenerativeModel('gemini-pro')

model = get_best_available_model()

# ==========================================
# 2. SESSION STATE
# ==========================================
if 'history' not in st.session_state:
    st.session_state.history = []
if 'active_index' not in st.session_state:
    st.session_state.active_index = None
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = {}

# ==========================================
# 3. UI STYLING
# ==========================================
st.set_page_config(page_title="Aura Study AI", page_icon="✨", layout="wide")

st.markdown("""
<style>
    .stApp { background: #0b0e14; color: #e6edf3; }
    section[data-testid="stSidebar"] { background-color: #0d1117 !important; border-right: 1px solid #30363d; }
    .content-card { background: rgba(22, 27, 34, 0.9); border: 1px solid #30363d; border-radius: 15px; padding: 25px; margin-bottom: 20px; }
    .hero-text { background: linear-gradient(90deg, #4facfe, #00f2fe); -webkit-background-clip: text; -webkit-text-fill-color: transparent; font-size: 3rem; font-weight: 800; }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 4. SIDEBAR
# ==========================================
with st.sidebar:
    st.markdown("<h2 style='color: #4facfe;'>✨ Aura AI</h2>", unsafe_allow_html=True)
    st.caption(f"Connected to: {model.model_name}") # Shows you which model is working
    
    if st.button("➕ New Session", use_container_width=True):
        st.session_state.active_index = None
        st.rerun()

    st.write("---")
    st.markdown("### 📂 Learning Material")
    uploaded_file = st.file_uploader("Upload PDF", type="pdf", label_visibility="collapsed")
    
    learn_style = st.selectbox("🎯 Adaptation Style", 
                               ["Simplified", "Visual Learner", "Quick Summary"])

    if uploaded_file:
        if st.button("🚀 UNLOCK KNOWLEDGE", use_container_width=True):
            with st.spinner("🧠 Aura is analyzing..."):
                try:
                    doc = fitz.open(stream=uploaded_file.read(), filetype="pdf")
                    text = "".join([page.get_text() for page in doc][:8])
                    
                    prompt = f"""
                    Simplify this material for a student preferring a {learn_style} style:
                    1. BIG PICTURE: Core concept in 1 sentence.
                    2. KEY PILLARS: 4 bullet points.
                    3. ANALOGY: A simple real-world example.
                    4. VISUAL: Describe a diagram that explains this.
                    
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
    for i, item in enumerate(reversed(st.session_state.history)):
        real_idx = len(st.session_state.history) - 1 - i
        if st.button(f"📄 {item['title'][:15]}...", key=f"h_{real_idx}"):
            st.session_state.active_index = real_idx
            st.rerun()

# ==========================================
# 5. MAIN CONTENT
# ==========================================
st.markdown("<h1 class='hero-text'>Aura Study AI</h1>", unsafe_allow_html=True)

if st.session_state.active_index is not None:
    active_data = st.session_state.history[st.session_state.active_index]
    
    t1, t2 = st.tabs(["📑 Guide", "💬 Tutor"])
    
    with t1:
        st.markdown('<div class="content-card">', unsafe_allow_html=True)
        st.markdown(active_data['result'])
        st.markdown('</div>', unsafe_allow_html=True)
        
    with t2:
        idx = st.session_state.active_index
        if idx not in st.session_state.chat_history: st.session_state.chat_history[idx] = []
        
        for chat in st.session_state.chat_history[idx]:
            with st.chat_message(chat["role"]): st.markdown(chat["content"])

        if query := st.chat_input("Ask a doubt..."):
            st.chat_message("user").markdown(query)
            st.session_state.chat_history[idx].append({"role": "user", "content": query})
            
            # Generate response
            response = model.generate_content(f"Context: {active_data['full_text'][:3000]}\nQuestion: {query}")
            st.chat_message("assistant").markdown(response.text)
            st.session_state.chat_history[idx].append({"role": "assistant", "content": response.text})
else:
    st.info("👈 Upload a textbook or research paper in the sidebar to begin!")

import streamlit as st
import fitz  # PyMuPDF
import google.generativeai as genai

# ==========================================
# 1. API CONFIGURATION
# ==========================================
try:
    API_KEY = st.secrets["GEMINI_API_KEY"]
    genai.configure(api_key=API_KEY)
except Exception:
    st.error("⚠️ API Key missing! Please add GEMINI_API_KEY to Streamlit Secrets.")

@st.cache_resource
def get_model():
    return genai.GenerativeModel('gemini-1.5-flash')

model = get_model()

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
# 3. UI & STYLING
# ==========================================
st.set_page_config(page_title="Aura Study AI", page_icon="✨", layout="wide")

st.markdown("""
<style>
    .stApp { background: #0b0e14; color: white; }
    section[data-testid="stSidebar"] { background-color: #0d1117 !important; border-right: 1px solid #30363d; }
    .content-card { background: rgba(22, 27, 34, 0.8); border: 1px solid #30363d; border-radius: 15px; padding: 25px; }
    .hero-text { background: linear-gradient(90deg, #4facfe, #00f2fe); -webkit-background-clip: text; -webkit-text-fill-color: transparent; font-size: 3rem; font-weight: 800; }
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
    st.markdown("### 📂 Upload Material")
    uploaded_file = st.file_uploader("Upload PDF", type="pdf", label_visibility="collapsed")
    
    # PROBLEM STATEMENT ADDITION: Learning Style
    learning_style = st.selectbox("🎯 Your Learning Style", 
                                ["Simplified (General)", "Visual Learner (Descriptions)", "Quick Summary", "Deep Dive"])

    if uploaded_file:
        file_id = uploaded_file.name
        if st.button("🚀 UNLOCK KNOWLEDGE", use_container_width=True):
            with st.spinner("🧠 Aura is analyzing..."):
                try:
                    doc = fitz.open(stream=uploaded_file.read(), filetype="pdf")
                    text = "".join([page.get_text() for page in doc][:10]) # First 10 pages
                    
                    prompt = f"""
                    You are an expert AI Tutor. Analyze this text and adapt to a {learning_style} style.
                    
                    Format your response with:
                    1. 🎯 BIG PICTURE: One simple sentence.
                    2. 📑 KEY CONCEPTS: 3-5 bullet points.
                    3. 💡 ANALOGY: A real-world comparison.
                    4. 🎨 VISUALIZATION: Describe what a helpful diagram for this would look like.
                    
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
    st.markdown("### 🕒 History")
    for i, item in enumerate(reversed(st.session_state.history)):
        real_idx = len(st.session_state.history) - 1 - i
        if st.button(f"📄 {item['title'][:20]}", key=f"h_{real_idx}"):
            st.session_state.active_index = real_idx
            st.rerun()

# ==========================================
# 5. MAIN CONTENT
# ==========================================
st.markdown("<h1 class='hero-text'>Aura Study AI</h1>", unsafe_allow_html=True)

if st.session_state.active_index is not None:
    active_data = st.session_state.history[st.session_state.active_index]
    
    tab1, tab2 = st.tabs(["📑 Simplified Guide", "💬 Interactive Tutor"])

    with tab1:
        st.markdown(f"### Study Guide: {active_data['title']}")
        st.markdown('<div class="content-card">', unsafe_allow_html=True)
        st.markdown(active_data['result'])
        st.markdown('</div>', unsafe_allow_html=True)
    
    with tab2:
        st.markdown("### 💬 Ask a Doubt")
        idx = st.session_state.active_index
        if idx not in st.session_state.chat_history:
            st.session_state.chat_history[idx] = []

        for chat in st.session_state.chat_history[idx]:
            with st.chat_message(chat["role"]):
                st.markdown(chat["content"])

        if user_query := st.chat_input("Ask anything about this document..."):
            st.chat_message("user").markdown(user_query)
            st.session_state.chat_history[idx].append({"role": "user", "content": user_query})
            
            tutor_prompt = f"Context: {active_data['full_text'][:4000]}\nQuestion: {user_query}\nAnswer simply."
            ans = model.generate_content(tutor_prompt)
            
            st.chat_message("assistant").markdown(ans.text)
            st.session_state.chat_history[idx].append({"role": "assistant", "content": ans.text})

else:
    st.info("👈 Upload a PDF in the sidebar to begin your learning journey!")
    st.image("https://img.freepik.com/free-vector/ai-technology-concept-illustration_114360-7052.jpg", width=500)

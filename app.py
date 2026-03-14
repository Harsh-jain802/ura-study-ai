import streamlit as st
import fitz  # PyMuPDF
import google.generativeai as genai
import time

# ==========================================
# 1. API CONFIGURATION & MODEL SETUP
# ==========================================
# Accessing the key from secrets
try:
    API_KEY = st.secrets["GEMINI_API_KEY"]
    genai.configure(api_key=API_KEY)
except:
    st.error("API Key not found in Streamlit Secrets!")

@st.cache_resource
def get_model():
    # Using 'gemini-1.5-flash-8b' which is more efficient for free-tier limits
    return genai.GenerativeModel('gemini-1.5-flash-8b')

model = get_model()

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
    .stApp { background: #0b0e14; }
    section[data-testid="stSidebar"] { background-color: #0d1117 !important; border-right: 1px solid #30363d; }
    .block-container { padding: 2rem 4rem !important; }
    
    .content-card {
        background: rgba(22, 27, 34, 0.8);
        border: 1px solid #30363d;
        border-radius: 15px;
        padding: 25px;
        margin-bottom: 20px;
    }
    
    .hero-text {
        background: linear-gradient(90deg, #4facfe, #00f2fe);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 3rem;
        font-weight: 800;
        margin-bottom: 10px;
    }

    .stTabs [data-baseweb="tab-list"] { gap: 20px; }
    .stTabs [data-baseweb="tab"] { font-weight: 600; color: #94a3b8 !important; }
    .stTabs [aria-selected="true"] { color: #4facfe !important; border-bottom-color: #4facfe !important; }
    </style>
    """, unsafe_allow_html=True)

# ==========================================
# 4. SIDEBAR LOGIC
# ==========================================
with st.sidebar:
    st.markdown("<h2 style='color: #4facfe;'>✨ Aura AI</h2>", unsafe_allow_html=True)
    
    if st.button("➕ New Session", use_container_width=True):
        st.session_state.active_index = None
        st.rerun()
    
    st.write("---")
    st.markdown("### 📂 Upload Material")
    uploaded_file = st.file_uploader("Upload PDF (Textbook/Notes)", type="pdf", label_visibility="collapsed")
    
    if uploaded_file:
        # Prevent re-processing the same file if it's already in history
        file_already_processed = any(h['title'] == uploaded_file.name for h in st.session_state.history)
        
        if not file_already_processed:
            if st.button("🚀 UNLOCK KNOWLEDGE", use_container_width=True):
                with st.spinner("🧠 Aura is analyzing content..."):
                    try:
                        doc = fitz.open(stream=uploaded_file.read(), filetype="pdf")
                        # Limit text to first 8 pages to avoid token/quota limits
                        text = "".join([page.get_text() for page in doc][:8])
                        
                        prompt = f"""
                        You are a world-class educational tutor. Simplify this complex material:
                        1. 🎯 THE BIG PICTURE: Explain the core concept in 2 simple sentences for a 10-year-old.
                        2. 📑 KEY PILLARS: 4 main points simplified.
                        3. 💡 ANALOGY: A relatable real-world comparison.
                        4. 🎨 VISUAL DESCRIPTION: Describe how a diagram of this would look to help a visual learner.

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
                        if "429" in str(e):
                            st.error("🚦 Quota Busy! Google's free AI tier is cooling down. Please wait 60 seconds and try again.")
                        else:
                            st.error(f"Error: {e}")
        else:
            st.info("File already in history below 👇")

    st.write("---")
    st.markdown("### 🕒 Recent History")
    for i, item in enumerate(reversed(st.session_state.history)):
        real_idx = len(st.session_state.history) - 1 - i
        if st.button(f"📄 {item['title'][:20]}", key=f"h_{real_idx}", use_container_width=True):
            st.session_state.active_index = real_idx
            st.rerun()

# ==========================================
# 5. MAIN CONTENT AREA
# ==========================================
st.markdown("<h1 class='hero-text'>Aura Study AI</h1>", unsafe_allow_html=True)

if st.session_state.active_index is not None:
    active_data = st.session_state.history[st.session_state.active_index]
    st.markdown(f"**Currently Studying:** `{active_data['title']}`")
    
    tab1, tab2 = st.tabs(["📑 Simplified Guide", "💬 Interactive Tutor"])
    
    with tab1:
        st.markdown('<div class="content-card">', unsafe_allow_html=True)
        st.markdown(active_data['result'])
        st.markdown('</div>', unsafe_allow_html=True)
        
    with tab2:
        st.markdown("### 💬 Ask a Doubt")
        
        # Unique Chat History for this specific document
        if st.session_state.active_index not in st.session_state.chat_history:
            st.session_state.chat_history[st.session_state.active_index] = []

        # Display Chat History
        for chat in st.session_state.chat_history[st.session_state.active_index]:
            with st.chat_message(chat["role"]):
                st.markdown(chat["content"])

        # Chat Input
        if user_query := st.chat_input("Explain the part about..."):
            # Display user message
            with st.chat_message("user"):
                st.markdown(user_query)
            st.session_state.chat_history[st.session_state.active_index].append({"role": "user", "content": user_query})
            
            # Generate Response
            try:
                with st.chat_message("assistant"):
                    with st.spinner("Tutor is thinking..."):
                        tutor_prompt = f"Context from document: {active_data['full_text'][:4000]}\n\nUser Question: {user_query}\n\nAnswer simply and clearly."
                        ans = model.generate_content(tutor_prompt)
                        st.markdown(ans.text)
                        st.session_state.chat_history[st.session_state.active_index].append({"role": "assistant", "content": ans.text})
            except Exception as e:
                st.error("AI is busy. Please wait a moment.")

else:
    # Landing State
    st.write("---")
    col1, col2 = st.columns([1, 1])
    with col1:
        st.markdown("""
        ### Transform complex learning today.
        Aura helps you break down:
        - 📚 **Textbooks** into simple analogies.
        - 📄 **Research Papers** into key pillars.
        - ✍️ **Lecture Notes** into self-test questions.
        
        **To start:**
        Upload a PDF in the sidebar.
        """)
    with col2:
        st.image("https://img.freepik.com/free-vector/ai-technology-concept-illustration_114360-7052.jpg")

# ==========================================
# 6. FOOTER
# ==========================================
st.markdown("<br><br><center style='color: #4b5563; font-size: 0.8rem;'>Built for Accessible Education | Powered by Aura AI</center>", unsafe_allow_html=True)

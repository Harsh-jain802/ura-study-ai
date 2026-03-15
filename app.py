import streamlit as st
import fitz  # PyMuPDF
import google.generativeai as genai

# ==========================================
# 1. API CONFIGURATION
# ==========================================
# Ensure you have GEMINI_API_KEY in your .streamlit/secrets.toml
try:
    API_KEY = st.secrets["GEMINI_API_KEY"]
    genai.configure(api_key=API_KEY)
except Exception as e:
    st.error("API Key not found. Please set GEMINI_API_KEY in Streamlit secrets.")

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
        color: #e6edf3;
        line-height: 1.6;
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
        with st.spinner("🧠 Aura is performing a deep scan of your document..."):
            try:
                # Open PDF
                doc = fitz.open(stream=uploaded_file.read(), filetype="pdf")
                
                # EXTRACT TEXT: We increased the limit to 30 pages for a more detailed analysis
                num_pages = min(30, len(doc))
                text = ""
                for i in range(num_pages):
                    text += doc.load_page(i).get_text()
                
                # THE DETAILED PROMPT
                prompt = f"""
                Act as an expert academic professor. I will provide you with text from a document. 
                Your goal is to create a COMPREHENSIVE, HIGH-LEVEL STUDY GUIDE. 
                
                Please structure your output exactly like this:

                # 📖 DETAILED ANALYSIS: {uploaded_file.name}

                ## 🎯 THE BIG PICTURE
                Provide a detailed 2-paragraph executive summary of the core message and purpose of this document.

                ## 🔍 KEY THEMES & PILLARS
                Break down the main topics into detailed sections. For every main theme:
                - Explain the core concept in depth.
                - List secondary details or supporting evidence.
                - Mention any specific examples found in the text.

                ## 💡 COMPLEX CONCEPTS & ANALOGIES
                Identify the 3 most difficult concepts in this text and explain them using simple, real-world analogies.

                ## 📑 GLOSSARY OF TERMS
                List and define at least 5-8 key technical terms or vocabulary words used in this text.

                ## 🎓 CRITICAL TAKEAWAYS
                What are the top 5 most important things a student should remember from this material for an exam?

                ## ❓ CHALLENGE QUESTIONS
                Provide 4 deep-thinking questions (with hidden answers if possible) to test mastery of the subject.

                ---
                DOCUMENT TEXT:
                {text}
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
                st.error(f"Error processing PDF: {e}")

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
    tab1, tab2 = st.tabs(["📑 Detailed Study Guide", "💬 Interactive Tutor"])
    
    with tab1:
        st.markdown('<div class="content-card">', unsafe_allow_html=True)
        # Displaying the AI result with Markdown
        st.markdown(active_data['result'])
        st.markdown('</div>', unsafe_allow_html=True)
        
    with tab2:
        st.markdown('<div class="content-card">', unsafe_allow_html=True)
        st.markdown("### 💬 Ask a Doubt")
        st.write("Aura has read your document. Ask anything for a simplified explanation.")
        
        user_query = st.chat_input("Explain the part about...")
        
        if user_query:
            with st.spinner("Aura is typing..."):
                tutor_prompt = f"""
                You are Aura, an AI Tutor. Use the context below to answer the student's question.
                If the answer isn't in the text, use your general knowledge but mention it's not in the document.
                
                CONTEXT: {active_data['full_text']}
                QUESTION: {user_query}
                """
                ans = model.generate_content(tutor_prompt)
                st.markdown(f'<div class="tutor-bubble"><b>Aura says:</b><br><br>{ans.text}</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

else:
    # Empty State
    st.write("---")
    st.markdown("""
    ### 👋 Welcome to Aura.
    Your intelligent study companion.
    
    **How to use:**
    1. Upload a **PDF** (Research paper, textbook chapter, or notes) in the sidebar.
    2. Click **Unlock Knowledge**.
    3. Aura will generate a **Deep Study Guide** and you can chat with it to clear doubts.
    """)
    st.image("https://img.freepik.com/free-vector/digital-lifestyle-concept-illustration_114360-7327.jpg", width=600)

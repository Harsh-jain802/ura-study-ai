import streamlit as st
import fitz  # PyMuPDF
import google.generativeai as genai
import streamlit.components.v1 as components

# ==========================================
# 1. API CONFIGURATION
# ==========================================
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
    section[data-testid="stSidebar"] { background-color: #0d1117 !important; border-right: 1px solid #30363d; }
    .block-container { padding: 3rem 5rem !important; }
    .content-card {
        background: rgba(22, 27, 34, 0.7);
        border: 1px solid #30363d;
        border-radius: 20px;
        padding: 40px;
        backdrop-filter: blur(12px);
        margin-top: 20px;
        color: #e6edf3;
    }
    .hero-text {
        background: linear-gradient(90deg, #4facfe, #00f2fe);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 3.2rem !important;
        font-weight: 800 !important;
    }
    .tutor-bubble {
        background: rgba(79, 172, 254, 0.1);
        padding: 20px;
        border-radius: 15px;
        border-left: 5px solid #4facfe;
        margin-top: 20px;
    }
    </style>
    """, unsafe_allow_html=True)

# Function to render Mermaid Diagrams
def render_mermaid(code):
    components.html(
        f"""
        <pre class="mermaid" style="background: transparent;">
            {code}
        </pre>
        <script type="module">
            import mermaid from 'https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.esm.min.mjs';
            mermaid.initialize({{ startOnLoad: true, theme: 'dark' }});
        </script>
        """,
        height=400,
    )

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
    st.markdown("### 📂 Upload Material")
    uploaded_file = st.file_uploader("Drop PDF here", type="pdf", label_visibility="collapsed")
    
    if uploaded_file and st.button("🚀 UNLOCK KNOWLEDGE", use_container_width=True):
        with st.spinner("🧠 Aura is performing a deep scan..."):
            try:
                doc = fitz.open(stream=uploaded_file.read(), filetype="pdf")
                text = "".join([doc.load_page(i).get_text() for i in range(min(20, len(doc)))])
                
                # UPDATED PROMPT: Now includes requests for Diagrams
                prompt = f"""
                Act as a Senior Biology & Science Professor. 
                Analyze the provided text and create a DETAILED study guide.

                IF the text describes a process (like blood flow, cell division, or chemical reactions), 
                you MUST include a Mermaid.js flowchart code block.

                Structure:
                1. 📑 EXECUTIVE SUMMARY (Detailed)
                2. 🔍 DEEP DIVE (Comprehensive explanation of parts)
                3. 🧬 DIAGRAM SECTION: Write a Mermaid.js code block starting with ```mermaid 
                   to visually represent the most important system in the text (e.g., The Heart's chambers or Blood Flow).
                4. 💡 ANALOGIES (For hard parts)
                5. ❓ MASTERY QUESTIONS

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

# ==========================================
# 6. MAIN CONTENT
# ==========================================
st.markdown("<h1 class='hero-text'>Aura Study AI</h1>", unsafe_allow_html=True)

if st.session_state.active_index is not None:
    active_data = st.session_state.history[st.session_state.active_index]
    
    tab1, tab2 = st.tabs(["📑 Detailed Study Guide", "💬 Ask Aura"])
    
    with tab1:
        st.markdown('<div class="content-card">', unsafe_allow_html=True)
        
        # We split the text to find the mermaid code and render it beautifully
        raw_text = active_data['result']
        if "```mermaid" in raw_text:
            parts = raw_text.split("```mermaid")
            st.markdown(parts[0]) # Text before diagram
            
            mermaid_code = parts[1].split("```")[0]
            st.info("📊 Aura-Generated Visual Diagram:")
            render_mermaid(mermaid_code) # Render the diagram
            
            st.markdown(parts[1].split("```")[1]) # Text after diagram
        else:
            st.markdown(raw_text)
            
        st.markdown('</div>', unsafe_allow_html=True)
        
    with tab2:
        st.markdown('<div class="content-card">')
        user_query = st.chat_input("Ask a question...")
        if user_query:
            tutor_prompt = f"Context: {active_data['full_text']}\nQuestion: {user_query}. If a diagram helps explain this, provide mermaid code."
            ans = model.generate_content(tutor_prompt)
            
            # Check for mermaid in chat as well
            if "```mermaid" in ans.text:
                chat_parts = ans.text.split("```mermaid")
                st.markdown(chat_parts[0])
                render_mermaid(chat_parts[1].split("```")[0])
                st.markdown(chat_parts[1].split("```")[1])
            else:
                st.markdown(f'<div class="tutor-bubble">{ans.text}</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
else:
    st.info("Please upload a PDF to begin.")

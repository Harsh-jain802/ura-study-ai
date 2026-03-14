import streamlit as st
import fitz
import google.generativeai as genai

# ==========================================
# 1. API CONFIGURATION
# ==========================================
API_KEY = st.secrets["GEMINI_API_KEY"]
genai.configure(api_key=API_KEY)

# Force stable model
model = genai.GenerativeModel("gemini-1.5-flash")

# ==========================================
# 2. SESSION STATE
# ==========================================
if 'history' not in st.session_state:
    st.session_state.history = []

if 'active_index' not in st.session_state:
    st.session_state.active_index = None

# ==========================================
# 3. PAGE CONFIG
# ==========================================
st.set_page_config(
    page_title="Aura Study AI",
    page_icon="✨",
    layout="wide"
)

# ==========================================
# 4. UI STYLING
# ==========================================
st.markdown("""
<style>

.stApp {
background: radial-gradient(circle at top right, #1a1f2c, #0b0e14);
}

section[data-testid="stSidebar"]{
background-color:#0d1117 !important;
border-right:1px solid #30363d;
}

.block-container{
padding:3rem 5rem !important;
}

.content-card{
background:rgba(22,27,34,0.7);
border:1px solid #30363d;
border-radius:20px;
padding:40px;
backdrop-filter:blur(12px);
margin-top:20px;
}

.hero-text{
background:linear-gradient(90deg,#4facfe,#00f2fe);
-webkit-background-clip:text;
-webkit-text-fill-color:transparent;
font-size:3.2rem !important;
font-weight:800 !important;
margin-bottom:0px;
}

.stTabs [data-baseweb="tab-list"]{
gap:30px;
}

.stTabs [data-baseweb="tab"]{
font-size:1.1rem;
font-weight:600;
color:#94a3b8 !important;
}

.stTabs [aria-selected="true"]{
color:#4facfe !important;
}

.tutor-bubble{
background:rgba(79,172,254,0.1);
padding:20px;
border-radius:15px;
border-left:5px solid #4facfe;
margin-top:20px;
}

</style>
""", unsafe_allow_html=True)

# ==========================================
# 5. SUMMARY GENERATOR
# ==========================================
@st.cache_data(show_spinner=False)
def generate_summary(text):

    prompt = f"""
You are an expert study assistant.

Analyze the following text and provide:

1. THE BIG PICTURE  
Explain the main idea in 2 simple sentences.

2. KEY PILLARS  
Give 4 bullet points.

3. ANALOGY  
Explain with a simple real-world comparison.

4. SELF TEST  
Generate 2 quiz questions.

TEXT:
{text[:3000]}
"""

    try:
        response = model.generate_content(prompt)
        return response.text

    except Exception as e:
        return f"AI Error: {e}"

# ==========================================
# 6. SIDEBAR
# ==========================================
with st.sidebar:

    st.markdown("<h2 style='color:#4facfe;'>✨ Aura AI</h2>", unsafe_allow_html=True)

    if st.button("➕ New Session", use_container_width=True):
        st.session_state.active_index = None
        st.rerun()

    st.write("---")

    st.markdown("### 📂 Upload Material")

    uploaded_file = st.file_uploader(
        "Drop PDF here",
        type="pdf",
        label_visibility="collapsed"
    )

    if uploaded_file and st.button("🚀 UNLOCK KNOWLEDGE", use_container_width=True):

        with st.spinner("🧠 Aura is reading..."):

            try:

                doc = fitz.open(stream=uploaded_file.read(), filetype="pdf")

                text = ""

                for i in range(min(3, len(doc))):
                    page = doc.load_page(i)
                    text += page.get_text()

                summary = generate_summary(text)

                st.session_state.history.append({
                    "title": uploaded_file.name,
                    "result": summary,
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

        if st.button(
            f"📄 {item['title'][:18]}...",
            key=f"h_{real_idx}",
            use_container_width=True
        ):

            st.session_state.active_index = real_idx
            st.rerun()

# ==========================================
# 7. MAIN CONTENT
# ==========================================
st.markdown(
    "<h1 class='hero-text'>Aura Study AI</h1>",
    unsafe_allow_html=True
)

active_data = None

if st.session_state.active_index is not None:
    active_data = st.session_state.history[st.session_state.active_index]

# ==========================================
# SHOW CONTENT
# ==========================================
if active_data:

    st.markdown(
        f"<p style='color:#94a3b8;'>Current Resource: <b>{active_data['title']}</b></p>",
        unsafe_allow_html=True
    )

    tab1, tab2 = st.tabs([
        "📑 Study Guide",
        "💬 AI Doubt Solver"
    ])

    # Study Guide
    with tab1:

        st.markdown('<div class="content-card">', unsafe_allow_html=True)

        st.markdown(active_data["result"])

        st.markdown('</div>', unsafe_allow_html=True)

    # AI Doubt Solver
    with tab2:

        st.markdown('<div class="content-card">', unsafe_allow_html=True)

        st.markdown("### 💬 Ask a Doubt")

        user_query = st.chat_input("Explain the concept of...")

        if user_query:

            with st.spinner("Tutor is thinking..."):

                context = active_data["full_text"][:3000]

                tutor_prompt = f"""
You are a helpful tutor.

Context:
{context}

Student Question:
{user_query}

Explain clearly and simply.
"""

                try:

                    ans = model.generate_content(tutor_prompt)

                    st.markdown(
                        f'<div class="tutor-bubble"><b>Aura says:</b><br><br>{ans.text}</div>',
                        unsafe_allow_html=True
                    )

                except Exception as e:
                    st.error(f"AI Error: {e}")

        st.markdown('</div>', unsafe_allow_html=True)

# ==========================================
# EMPTY STATE
# ==========================================
else:

    st.write("---")

    st.markdown("""
### 👋 Welcome to Aura

Your study material is currently empty.

To get started:

1 Upload a PDF from the sidebar  
2 Click Unlock Knowledge  
3 Aura will generate summaries and quiz questions  
""")

    st.image(
        "https://img.freepik.com/free-vector/digital-lifestyle-concept-illustration_114360-7327.jpg",
        width=600
    )

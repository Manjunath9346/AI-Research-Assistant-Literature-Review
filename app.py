import streamlit as st
import pandas as pd
from arxiv_client import ArxivFetcher
from summarizer import PaperSummarizer
from embedding_manager import EmbeddingManager
from qa_chain import QASystem
from analysis import ThemeGapAnalyzer
import database as db
from datetime import datetime

# --------------------- PAGE CONFIG ---------------------
st.set_page_config(
    page_title="AI Research Assistant",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"  # Sidebar open by default
)

st.markdown("""
<style>
.sticky-toolbar {
    position: sticky;
    top: 0;
    background: white;
    z-index: 999;
    padding: 10px 0;
}
</style>
""", unsafe_allow_html=True)
# --------------------- CUSTOM CSS ---------------------
# st.markdown("""
# <style>
#     #MainMenu {visibility: hidden;}
#     footer {visibility: hidden;}
#     header {visibility: hidden;}
    
#     .stApp { background-color: #0b0e11; }
    
#     /* Sidebar styling */
#     .css-1d391kg, .css-1lcbmhc, [data-testid="stSidebar"] {
#         background-color: #151a21 !important;
#         border-right: 1px solid #2a3038 !important;
#     }
    
#     .sidebar-header {
#         color: #e8edf5 !important;
#         font-size: 1.1rem !important;
#         font-weight: 700 !important;
#         padding: 0 0.5rem 0.8rem 0.5rem !important;
#         border-bottom: 1px solid #2a3038 !important;
#         margin-bottom: 0.8rem !important;
#         display: flex !important;
#         align-items: center !important;
#         gap: 0.5rem !important;
#     }
#     .sidebar-header span {
#         background: linear-gradient(135deg, #6C63FF, #4CAF50);
#         -webkit-background-clip: text;
#         -webkit-text-fill-color: transparent;
#     }
    
#     .stSidebar .stButton button {
#         background-color: #6C63FF !important;
#         color: white !important;
#         border: none !important;
#         border-radius: 8px !important;
#         padding: 0.5rem 1rem !important;
#         font-weight: 600 !important;
#         width: 100% !important;
#         transition: 0.2s !important;
#     }
#     .stSidebar .stButton button:hover {
#         background-color: #5a52d5 !important;
#         box-shadow: 0 0 20px rgba(108, 99, 255, 0.3) !important;
#     }
    
#     /* Main content text color fixes */
#     .stMarkdown, .stMarkdown p, .stMarkdown li, 
#     .stMarkdown h1, .stMarkdown h2, .stMarkdown h3, 
#     .stMarkdown strong, .stMarkdown em {
#         color: #e8edf5 !important;
#     }
    
#     /* Toolbar Layout */
#     .toolbar-container {
#         display: flex !important;
#         gap: 0.5rem !important;
#         flex-wrap: wrap !important;
#         padding: 0.5rem 0 !important;
#         margin-bottom: 0.5rem !important;
#         border-bottom: 1px solid #1e2530 !important;
#     }
    
#     .stChatInput { padding-bottom: 1rem !important; padding-top: 0.5rem !important; }
#     .stChatInput input {
#         background-color: #1e2530 !important;
#         border: 1px solid #353d4a !important;
#         border-radius: 12px !important;
#         color: #e8edf5 !important;
#         padding: 12px 16px !important;
#     }
#     .stChatInput input:focus {
#         border-color: #6C63FF !important;
#         box-shadow: 0 0 0 2px rgba(108, 99, 255, 0.2) !important;
#     }
    
#     .stChatMessage[data-testid="chat-message-user"] {
#         background-color: #2a313c !important;
#         border-radius: 18px 18px 4px 18px !important;
#         padding: 12px 18px !important;
#         margin: 8px 0 !important;
#         color: #f0f2f6 !important;
#         border: 1px solid #3a424f !important;
#     }
#     .stChatMessage[data-testid="chat-message-user"] p { color: #f0f2f6 !important; }
    
#     .stChatMessage[data-testid="chat-message-assistant"] {
#         background-color: transparent !important;
#         padding: 12px 0 !important;
#         margin: 8px 0 !important;
#         color: #e8edf5 !important;
#         border-bottom: 1px solid #1e2530 !important;
#     }
    
#     .streamlit-expanderHeader {
#         color: #e8edf5 !important;
#         background-color: #151a21 !important;
#         border-radius: 8px !important;
#         border: 1px solid #2a3038 !important;
#     }
    
#     /* Login container */
#     .login-container {
#         max-width: 400px !important;
#         margin: 3rem auto !important;
#         padding: 2rem !important;
#         background-color: #151a21 !important;
#         border-radius: 16px !important;
#         border: 1px solid #2a3038 !important;
#         text-align: center !important;
#     }
#     .login-container h1 { color: #e8edf5 !important; margin-bottom: 0.5rem !important; }
#     .login-container p { color: #9aa3b3 !important; margin-bottom: 1.5rem !important; }
# </style>
# """, unsafe_allow_html=True)

# --------------------- CACHE RESOURCES ---------------------
@st.cache_resource
def load_embedding_manager():
    return EmbeddingManager()

# --------------------- INITIALIZE SESSION STATE ---------------------
if 'papers' not in st.session_state:
    st.session_state.papers = []
if 'embedding_manager' not in st.session_state:
    st.session_state.embedding_manager = load_embedding_manager()
if 'qa_system' not in st.session_state:
    st.session_state.qa_system = None
if 'papers_loaded' not in st.session_state:
    st.session_state.papers_loaded = False
if 'current_chat_id' not in st.session_state:
    st.session_state.current_chat_id = None
if 'user_id' not in st.session_state:
    st.session_state.user_id = None
if 'user' not in st.session_state:
    st.session_state.user = None
if 'messages' not in st.session_state:
    st.session_state.messages = []
if 'auth_mode' not in st.session_state:
    st.session_state.auth_mode = "login"
if 'num_papers' not in st.session_state:
    st.session_state.num_papers = 10
if 'search_category' not in st.session_state:
    st.session_state.search_category = "all"

# --------------------- AUTH FUNCTIONS ---------------------
def login_user(username: str, password: str):
    user = db.authenticate_user(username, password)
    if user:
        st.session_state.user = user
        st.session_state.user_id = user['id']
        st.session_state.messages = []
        st.session_state.current_chat_id = None
        st.session_state.papers = []
        st.session_state.papers_loaded = False
        return True
    return False

def register_user(username: str, password: str, display_name: str):
    if db.create_user(username, password, display_name):
        return login_user(username, password)
    return False

def logout_user():
    st.session_state.user = None
    st.session_state.user_id = None
    st.session_state.messages = []
    st.session_state.current_chat_id = None
    st.session_state.papers = []
    st.session_state.papers_loaded = False

def load_chat(chat_id: int):
    chat = db.get_chat(chat_id, st.session_state.user_id)
    if chat:
        st.session_state.current_chat_id = chat_id
        st.session_state.messages = chat['messages']
        st.session_state.papers = []
        st.session_state.papers_loaded = False

def save_current_chat():
    if st.session_state.user_id and st.session_state.messages:
        title = "New Chat"
        for msg in st.session_state.messages:
            if msg['role'] == 'user':
                title = msg['content'][:50]
                break
        
        if st.session_state.current_chat_id:
            db.update_chat(st.session_state.current_chat_id, st.session_state.messages)
        else:
            chat_id = db.save_chat(st.session_state.user_id, title, st.session_state.messages)
            st.session_state.current_chat_id = chat_id

def create_new_chat():
    if st.session_state.messages:
        save_current_chat()
    st.session_state.messages = []
    st.session_state.current_chat_id = None
    st.session_state.papers = []
    st.session_state.papers_loaded = False

# --------------------- PROCESS COMMAND ---------------------
def process_command(user_input: str) -> str:
    lower_input = user_input.lower().strip()
    
    if not st.session_state.papers_loaded or not st.session_state.papers:
        return "⚠️ No papers loaded. Please enter a research topic (e.g., 'quantum machine learning') to fetch papers first."
    
    if "summarize" in lower_input:
        with st.spinner("Generating summaries..."):
            summarizer = PaperSummarizer()
            summaries = []
            for i, paper in enumerate(st.session_state.papers):
                if 'summary' not in paper:
                    paper['summary'] = summarizer.summarize(paper['abstract'])
                summaries.append(f"**{i+1}. {paper['title']}**\n\n> {paper['summary']}")
            return "### 📝 Paper Summaries\n\n" + "\n\n---\n\n".join(summaries)
    
    elif "theme" in lower_input or "topic" in lower_input:
        with st.spinner("Analyzing themes..."):
            analyzer = ThemeGapAnalyzer(st.session_state.papers)
            keywords = analyzer.extract_keywords()
            themes = analyzer.find_common_themes()
            return f"""
### 📊 Common Themes

**🔑 Top Keywords:** {', '.join(keywords[:8])}

**📌 Identified Themes:** {', '.join(themes) if themes else 'No clear themes detected.'}
"""
    
    elif "gap" in lower_input:
        with st.spinner("Identifying gaps..."):
            analyzer = ThemeGapAnalyzer(st.session_state.papers)
            gaps = analyzer.identify_gaps()
            keywords = analyzer.extract_keywords()
            return f"""


            
### 🕳️ Research Gaps

**Underexplored terms** (appear in few papers):
{', '.join(gaps) if gaps else 'No clear gaps identified.'}

**Well‑covered areas** (dominant keywords):
{', '.join(keywords[:5])}
"""


    # ===== ADD THIS NEW BLOCK HERE =====
    elif "synthesize" in lower_input or "detailed" in lower_input:
        with st.spinner("Generating detailed synthesis..."):
            if st.session_state.qa_system:
                # Extract the actual question after the command
                question_text = user_input.replace("synthesize", "").replace("detailed", "").strip()
                if not question_text:
                    question_text = "What are the main insights from these papers?"
                answer = st.session_state.qa_system.ask(question_text, top_k=10)
                return f"### 📝 Detailed Synthesis\n\n{answer}"
            else:
                return "⚠️ QA system not ready. Please try fetching papers again."
    # ===== END OF NEW BLOCK =====

    
    else:
        if st.session_state.qa_system:
            with st.spinner("Searching papers..."):
                answer = st.session_state.qa_system.ask(user_input, top_k=7)
                return f"**Answer:** {answer}"
        else:
            return "⚠️ QA system not ready. Please try fetching papers again."

def fetch_papers(topic: str, max_results: int = 10, category: str = "all"):
    with st.spinner(f"Searching for '{topic}' in {category}..."):
        fetcher = ArxivFetcher(max_results=max_results)
        papers = fetcher.fetch_papers(topic, category)
        st.session_state.papers = papers
        st.session_state.papers_loaded = False
        
        if papers:
            with st.spinner("Building index..."):
                st.session_state.embedding_manager.add_papers(papers)
                st.session_state.qa_system = QASystem(st.session_state.embedding_manager)
                st.session_state.papers_loaded = True
            
            paper_titles = "\n".join([f"• {p['title']}" for p in papers[:10]])
            return f"✅ Found **{len(papers)}** papers on *'{topic}'* in *{category}*:\n\n{paper_titles}\n\nAsk me anything about them!"
        else:
            return f"❌ No papers found for '{topic}' in *{category}*. Please try a different topic or category."

# ==================== MAIN APP RUN ====================

# ---- AUTH SCREEN ----
if not st.session_state.user:
    st.markdown("""
    <div class="login-container">
        <h1>🧠 AI Research Assistant</h1>
        <p>Login or register to start your research</p>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.session_state.auth_mode == "login":
            username = st.text_input("Username", key="login_username")
            password = st.text_input("Password", type="password", key="login_password")
            if st.button("Login", use_container_width=True):
                if login_user(username, password):
                    st.rerun()
                else:
                    st.error("Invalid username or password")
            if st.button("Don't have an account? Register", use_container_width=True):
                st.session_state.auth_mode = "register"
                st.rerun()
        else:
            username = st.text_input("Username", key="reg_username")
            password = st.text_input("Password", type="password", key="reg_password")
            display_name = st.text_input("Display Name", key="reg_display", placeholder="Your full name")
            if st.button("Register", use_container_width=True):
                if not username or not password or not display_name:
                    st.error("All fields are required")
                elif register_user(username, password, display_name):
                    st.success("Registration successful!")
                    st.rerun()
                else:
                    st.error("Username already exists. Please choose another.")
            if st.button("Already have an account? Login", use_container_width=True):
                st.session_state.auth_mode = "login"
                st.rerun()
    st.stop()  # Script stops executing here if not logged in

# ---- SIDEBAR (Only renders post successful login) ----
with st.sidebar:
    st.markdown("## 🧠 Research Assistant")

    if st.button("➕ New Chat", use_container_width=True):
        create_new_chat()
        st.rerun()

    # ===== NEW: Topic Search & Fetch =====
    st.markdown("### 🔍 Search Topic")
    fetch_topic = st.text_input(
        "Enter research topic",
        placeholder="e.g., quantum machine learning",
        key="fetch_topic_input",
        label_visibility="collapsed"
    )
    if st.button("📥 Fetch Papers", use_container_width=True):
        if fetch_topic.strip():
            response = fetch_papers(fetch_topic, st.session_state.num_papers, st.session_state.search_category)
            st.session_state.messages.append({"role": "user", "content": f"🔍 Searching for: {fetch_topic}"})
            st.session_state.messages.append({"role": "assistant", "content": response})
            # ✅ DELETED: st.session_state.fetch_topic_input = ""
            save_current_chat()
            st.rerun()
        else:
            st.warning("Please enter a topic first.")
    st.markdown("---")
    # ===== END =====
        
    # ========== PAPERS TO FETCH ==========
    st.markdown("### 🔢 Papers to Fetch")
    st.session_state.num_papers = st.selectbox(
        "Select number of papers",
        options=[5, 10, 15, 20, 25, 30],
        index=1,
        key="num_papers_selector",
        label_visibility="collapsed"
    )
    st.markdown("---")
    # ========== END ==========


     # ========== EXPANDED CATEGORY SELECTOR ==========
    st.markdown("### 📂 Category")
    st.session_state.search_category = st.selectbox(
        "Select category",
        options=[
            "all",
            "cs", "cs.AI", "cs.LG", "cs.CV", "cs.CL", "cs.NE", "cs.RO", "cs.SE",
            "math", "math.OC",
            "physics",
            "astro-ph", "cond-mat", "gr-qc", "hep-ex", "hep-lat", "hep-ph", "hep-th",
            "math-ph", "nlin", "nucl-ex", "nucl-th", "quant-ph",
            "q-bio", "q-fin", "stat", "stat.ML",
            "econ", "eess"
        ],
        format_func=lambda x: {
            "all": "🌐 All Sciences (Default)",
            "cs": "💻 Computer Science (All)",
            "cs.AI": "🤖 AI / Artificial Intelligence",
            "cs.LG": "📊 Machine Learning",
            "cs.CV": "👁️ Computer Vision",
            "cs.CL": "📝 Computation & Language (NLP)",
            "cs.NE": "🧠 Neural & Evolutionary Computing",
            "cs.RO": "🤖 Robotics",
            "cs.SE": "🛠️ Software Engineering",
            "math": "📐 Mathematics (All)",
            "math.OC": "📈 Optimization & Control",
            "physics": "⚛️ Physics (All)",
            "astro-ph": "🔭 Astrophysics",
            "cond-mat": "🧊 Condensed Matter",
            "gr-qc": "🌌 General Relativity & Cosmology",
            "hep-ex": "🔬 High Energy Physics - Experiment",
            "hep-lat": "🖥️ High Energy Physics - Lattice",
            "hep-ph": "⚛️ High Energy Physics - Phenomenology",
            "hep-th": "🧵 High Energy Physics - Theory",
            "math-ph": "📐 Mathematical Physics",
            "nlin": "🌀 Nonlinear Sciences",
            "nucl-ex": "🔬 Nuclear Experiment",
            "nucl-th": "🧠 Nuclear Theory",
            "quant-ph": "💡 Quantum Physics",
            "q-bio": "🧬 Quantitative Biology",
            "q-fin": "💰 Quantitative Finance",
            "stat": "📊 Statistics (All)",
            "stat.ML": "📈 Machine Learning (Statistics)",
            "econ": "📉 Economics",
            "eess": "⚡ Electrical Engineering & Systems Science"
        }.get(x, x),
        key="search_category_selector",
        label_visibility="collapsed"
    )
    st.markdown("---")
    # ========== END ==========


    if st.session_state.papers_loaded and st.session_state.papers:

        st.markdown("### 🛠️ Tools")

        if st.button("📝 Summarize", use_container_width=True):
            response = process_command("summarize")
            st.session_state.messages.append({"role": "user", "content": "📝 Summarize"})
            st.session_state.messages.append({"role": "assistant", "content": response})
            save_current_chat()
            st.rerun()

        if st.button("📊 Themes", use_container_width=True):
            response = process_command("themes")
            st.session_state.messages.append({"role": "user", "content": "📊 Themes"})
            st.session_state.messages.append({"role": "assistant", "content": response})
            save_current_chat()
            st.rerun()

        if st.button("🕳️ Gaps", use_container_width=True):
            response = process_command("gaps")
            st.session_state.messages.append({"role": "user", "content": "🕳️ Gaps"})
            st.session_state.messages.append({"role": "assistant", "content": response})
            save_current_chat()
            st.rerun()

        if st.button("🗑️ Clear Chat", use_container_width=True):
            st.session_state.messages = []
            st.session_state.papers = []
            st.session_state.papers_loaded = False
            st.rerun()

    st.markdown("---")
    
    # Render Chat History
    chats = db.get_user_chats(st.session_state.user_id) if st.session_state.user_id else []
    if chats:
        st.markdown("### 📋 History")
        for chat in chats:
            created = chat['created_at']
            try:
                date_str = datetime.strptime(created, "%Y-%m-%d %H:%M:%S").strftime("%b %d, %I:%M %p")
            except:
                date_str = created[:10]
            
            # Using clean unique keys per chat instance
            if st.button(
                f"{chat['title']}\n({date_str})",
                key=f"sidebar_chat_{chat['id']}",
                use_container_width=True
            ):
                load_chat(chat['id'])
                st.rerun()
    else:
        st.caption("No chats yet. Start a new research session!")
    
    # User Profile Actions Area
    if st.session_state.user:
        st.markdown("---")
        col_prof, col_log = st.columns([2, 1])
        with col_prof:
            st.markdown(f'👤 **{st.session_state.user["display_name"]}**')
        with col_log:
            if st.button("🚪 Logout", use_container_width=True):
                logout_user()
                st.rerun()

# ---- MAIN CHAT AREA ----
st.markdown('<div style="font-size:1.3rem; font-weight:700; padding:0.5rem 0;">🧠 <span style="background:linear-gradient(135deg,#6C63FF,#4CAF50); -webkit-background-clip:text; -webkit-text-fill-color:transparent;">AI Research Assistant</span></div>', unsafe_allow_html=True)

# # Main Dashboard Action Toolbar
# if st.session_state.papers_loaded and st.session_state.papers:
#     st.markdown('<div class="sticky-toolbar">', unsafe_allow_html=True)
#     st.markdown('<div class="toolbar-container">', unsafe_allow_html=True)
#     col1, col2, col3, col4 = st.columns([1, 1, 1, 3])
#     with col1:
#         if st.button("📝 Summarize", use_container_width=True):
#             response = process_command("summarize")
#             st.session_state.messages.append({"role": "user", "content": "📝 Summarize"})
#             st.session_state.messages.append({"role": "assistant", "content": response})
#             save_current_chat()
#             st.rerun()
#     with col2:
#         if st.button("📊 Themes", use_container_width=True):
#             response = process_command("themes")
#             st.session_state.messages.append({"role": "user", "content": "📊 Themes"})
#             st.session_state.messages.append({"role": "assistant", "content": response})
#             save_current_chat()
#             st.rerun()
#     with col3:
#         if st.button("🕳️ Gaps", use_container_width=True):
#             response = process_command("gaps")
#             st.session_state.messages.append({"role": "user", "content": "🕳️ Gaps"})
#             st.session_state.messages.append({"role": "assistant", "content": response})
#             save_current_chat()
#             st.rerun()
#     with col4:
#         if st.button("🗑️ Clear Chat", use_container_width=True):
#             st.session_state.messages = []
#             st.session_state.papers = []
#             st.session_state.papers_loaded = False
#             st.rerun()
#     st.markdown('</div></div>', unsafe_allow_html=True)

# Render initial greeting message if empty
if not st.session_state.messages:
    st.session_state.messages.append({
        "role": "assistant",
        "content": "👋 **Hello! I'm your AI Research Assistant.**\n\n1️⃣ Enter a research topic in the sidebar and click **📥 Fetch Papers**.\n2️⃣ Once papers are loaded, ask me questions or use commands like **summarize**, **themes**, or **gaps**.\n\nGet started by entering a topic in the sidebar!"
    })

# Render logs/messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Multi-paper Document Viewer Table
if st.session_state.papers_loaded and st.session_state.papers:
    with st.expander(f"📚 {len(st.session_state.papers)} Papers Loaded (click to view)", expanded=False):
        df = pd.DataFrame(st.session_state.papers)
        df_display = df[['title', 'authors', 'published']]
        st.dataframe(df_display, use_container_width=True, hide_index=True)

# Processing Dynamic Conversation Input
if prompt := st.chat_input("Ask a question about the loaded papers..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    
    # Now we NEVER fetch papers here – only questions/commands
    if not st.session_state.papers_loaded or not st.session_state.papers:
        response = "⚠️ No papers are loaded. Please use the **📥 Fetch Papers** button in the sidebar to load a research topic first."
    else:
        response = process_command(prompt)
    
    st.session_state.messages.append({"role": "assistant", "content": response})
    with st.chat_message("assistant"):
        st.markdown(response)
    
    save_current_chat()
    st.rerun()
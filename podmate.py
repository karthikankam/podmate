import streamlit as st
import os
import tempfile
import sqlite3
from datetime import datetime
import bcrypt
from dotenv import load_dotenv
from gtts import gTTS
from groq import Groq
from langgraph.prebuilt import create_react_agent
from langchain_groq import ChatGroq
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain.chains.summarize import load_summarize_chain
from langchain_community.document_loaders import PyPDFLoader
from langchain_community.tools import ArxivQueryRun, WikipediaQueryRun, DuckDuckGoSearchRun
from langchain_community.utilities import ArxivAPIWrapper, WikipediaAPIWrapper
import magic

# -------------------------------
# Config
# -------------------------------
DB_FILE = "podmate.db"

# -------------------------------
# Database Setup
# -------------------------------
def init_database():
    """Initialize SQLite database with required tables"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    # Users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Podcasts table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS podcasts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            summary TEXT NOT NULL,
            audio_path TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    conn.commit()
    conn.close()

# -------------------------------
# User Management Functions
# -------------------------------
def hash_password(password):
    """Hash a password using bcrypt"""
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')

def verify_password(password, hashed_password):
    """Verify a password against its hash"""
    return bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8'))

def register_user(username, password):
    """Register a new user in the database"""
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        
        hashed_pw = hash_password(password)
        cursor.execute(
            "INSERT INTO users (username, password) VALUES (?, ?)",
            (username, hashed_pw)
        )
        
        conn.commit()
        conn.close()
        return True, "Registration successful"
    except sqlite3.IntegrityError:
        return False, "Username already exists"
    except Exception as e:
        return False, f"Error: {str(e)}"

def authenticate_user(username, password):
    """Authenticate a user"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    cursor.execute("SELECT id, password FROM users WHERE username = ?", (username,))
    result = cursor.fetchone()
    conn.close()
    
    if result and verify_password(password, result[1]):
        return True, result[0]  # Return user_id
    return False, None

# -------------------------------
# Podcast Management Functions
# -------------------------------
def save_podcast(user_id, title, summary, audio_path):
    """Save podcast to database"""
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        
        cursor.execute(
            "INSERT INTO podcasts (user_id, title, summary, audio_path) VALUES (?, ?, ?, ?)",
            (user_id, title, summary, audio_path)
        )
        
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        st.error(f"Error saving podcast: {str(e)}")
        return False

def get_user_podcasts(user_id):
    """Retrieve all podcasts for a user"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    cursor.execute(
        "SELECT title, summary, audio_path, created_at FROM podcasts WHERE user_id = ? ORDER BY created_at DESC",
        (user_id,)
    )
    
    results = cursor.fetchall()
    conn.close()
    
    return [
        {
            "title": row[0],
            "summary": row[1],
            "audio": row[2],
            "created_at": row[3]
        }
        for row in results
    ]

# -------------------------------
# API Key Validation
# -------------------------------
def validate_api_key_callback():
    """Callback function to validate API key automatically"""
    api_key = st.session_state.api_key_input
    
    if not api_key or len(api_key) < 10:
        st.session_state.api_key_validated = False
        st.session_state.validation_message = "⚠️ API key too short"
        return
    
    try:
        # Test the API key by initializing clients
        test_client = Groq(api_key=api_key)
        test_llm = ChatGroq(
            model="meta-llama/llama-4-scout-17b-16e-instruct",
            groq_api_key=api_key,
            streaming=True
        )
        
        # If successful, update session state
        st.session_state.groq_api_key = api_key
        st.session_state.api_key_validated = True
        st.session_state.validation_message = "✅ API Key validated successfully!"
        
    except Exception as e:
        st.session_state.api_key_validated = False
        st.session_state.groq_api_key = ""
        st.session_state.validation_message = "❌ Invalid API Key"

# -------------------------------
# Session state init
# -------------------------------
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "username" not in st.session_state:
    st.session_state.username = ""
if "user_id" not in st.session_state:
    st.session_state.user_id = None
if "mes" not in st.session_state:
    st.session_state.mes = []
if "session_podcasts" not in st.session_state:
    st.session_state.session_podcasts = []
if "groq_api_key" not in st.session_state:
    st.session_state.groq_api_key = ""
if "api_key_validated" not in st.session_state:
    st.session_state.api_key_validated = False
if "validation_message" not in st.session_state:
    st.session_state.validation_message = ""

# Initialize database
init_database()

# -------------------------------
# Environment setup
# -------------------------------
load_dotenv()
DEFAULT_GROQ_KEY = os.getenv('GROQ_API_KEY', '')

# -------------------------------
# Login/Registration Page
# -------------------------------
def show_auth_page():
    st.title("🔐 PodMate Authentication")
    
    tab1, tab2 = st.tabs(["Login", "Sign Up"])
    
    with tab1:
        st.subheader("Login to your account")
        with st.form("login_form"):
            username_input = st.text_input("Username")
            password_input = st.text_input("Password", type="password")
            submitted = st.form_submit_button("Login")

            if submitted:
                success, user_id = authenticate_user(username_input, password_input)
                
                if success:
                    st.session_state.logged_in = True
                    st.session_state.username = username_input
                    st.session_state.user_id = user_id
                    st.session_state.session_podcasts = []
                    st.session_state.mes = [{"role": "ai", "content": "Hello! I'm your AI research assistant 🤖."}]
                    
                    # Check if default API key is available and auto-validate
                    

                    st.success(f"Welcome back, {username_input}!")
                    st.rerun()
                else:
                    st.error("❌ Invalid username or password")
    
    with tab2:
        st.subheader("Create a new account")
        with st.form("register_form"):
            new_username = st.text_input("Choose a username")
            new_password = st.text_input("Choose a password", type="password")
            confirm_password = st.text_input("Confirm password", type="password")
            register_submitted = st.form_submit_button("Sign Up")

            if register_submitted:
                if not new_username or not new_password:
                    st.error("❌ Please fill in all fields")
                elif len(new_username) < 3:
                    st.error("❌ Username must be at least 3 characters")
                elif len(new_password) < 6:
                    st.error("❌ Password must be at least 6 characters")
                elif new_password != confirm_password:
                    st.error("❌ Passwords do not match")
                else:
                    success, message = register_user(new_username, new_password)
                    if success:
                        st.success("✅ " + message + " Please login now!")
                    else:
                        st.error("❌ " + message)

# -------------------------------
# Main App
# -------------------------------
def show_main_app():
    username = st.session_state.username
    user_id = st.session_state.user_id
    
    # Sidebar for user info and API key
    st.sidebar.success(f"👤 Logged in as **{username}**")
    st.sidebar.markdown("---")
    
    # API Key Configuration Section
    st.sidebar.subheader("🔑 API Configuration")
    
    # Text input with auto-validation callback
    api_key_input = st.sidebar.text_input(
    "Enter your Groq API Key",
    value="",  # Always start empty
    type="password",
    placeholder="gsk_...",
    help="Your API key will be automatically validated as you type",
    key="api_key_input",
    on_change=validate_api_key_callback
    )

    
    # Display validation status
    if st.session_state.validation_message:
        if "✅" in st.session_state.validation_message:
            st.sidebar.success(st.session_state.validation_message)
        elif "❌" in st.session_state.validation_message:
            st.sidebar.error(st.session_state.validation_message)
        else:
            st.sidebar.warning(st.session_state.validation_message)
    
    st.sidebar.markdown("---")
    
    # Logout button
    if st.sidebar.button("🚪 Logout"):
        st.session_state.logged_in = False
        st.session_state.username = ""
        st.session_state.user_id = None
        st.session_state.session_podcasts = []
        st.session_state.mes = []
        st.session_state.groq_api_key = ""
        st.session_state.api_key_validated = False
        st.session_state.validation_message = ""
        st.rerun()
    
    # Main content area
    st.title("🎧 AI-Powered Podcast Generator & Research Assistant")
    
    # Check if API key is validated
    if not st.session_state.api_key_validated:
        st.warning("⚠️ Please enter a valid Groq API Key in the sidebar to access the features.")
        st.info("💡 **Get your free API key from:** https://console.groq.com/keys")
        
        # Display instructions
        st.markdown("""
        ### How to get started:
        1. Sign up for a free Groq account at [console.groq.com](https://console.groq.com)
        2. Generate an API key from your dashboard
        3. Enter the API key in the sidebar (it will be validated automatically)
        4. Start using the Podcast Generator and Research Assistant!
        """)
        return
    
    # Initialize LLM and tools with validated API key
    GROQ_KEY = st.session_state.groq_api_key
    
    try:
        llm = ChatGroq(
            model="meta-llama/llama-4-scout-17b-16e-instruct",
            groq_api_key=GROQ_KEY,
            streaming=True
        )
        client = Groq(api_key=GROQ_KEY)
        
        api_wiki = WikipediaAPIWrapper(top_k_results=1, doc_content_chars_max=250)
        wiki = WikipediaQueryRun(api_wrapper=api_wiki)
        api_arxiv = ArxivAPIWrapper(top_k_results=1, doc_content_chars_max=250)
        arxiv = ArxivQueryRun(api_wrapper=api_arxiv)
        search = DuckDuckGoSearchRun(name="search")
        tools = [wiki, arxiv, search]
    except Exception as e:
        st.error(f"❌ Error initializing services: {str(e)}")
        st.session_state.api_key_validated = False
        st.rerun()
        return

    # Show tabs only when API key is validated
    tab1, tab2, tab3 = st.tabs(["🎙️ Podcast Generator", "🤖 Research Assistant", "🗂️ Podcast History"])

    # ---------------- TAB 1: Podcast Generator ----------------
    with tab1:
        st.header("Generate Podcasts from Notes or Textbooks")

        uploaded_file = st.file_uploader("📄 Upload a PDF or TXT file", type=["pdf", "txt"])

        if uploaded_file:
            mime = magic.from_buffer(uploaded_file.read(2048), mime=True)
            uploaded_file.seek(0)
            if not (mime in ["application/pdf", "text/plain"]):
                st.error("❌ Invalid file type. Please upload a valid PDF or TXT file.")
                st.stop()

        if uploaded_file:
            with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(uploaded_file.name)[1]) as tmp:
                tmp.write(uploaded_file.read())
                file_path = tmp.name
            st.success("✅ File uploaded successfully!")

            file_size_mb = os.path.getsize(file_path) / (1024 * 1024)
            if file_size_mb > 10:
                st.error("❌ File too large! Please upload a file smaller than 10 MB.")
                os.unlink(file_path)
                st.stop()

            if st.button("🚀 Generate Podcast"):
                with st.spinner("🧠 Summarizing and generating your podcast..."):
                    try:
                        # Load text
                        if uploaded_file.name.endswith(".pdf"):
                            loader = PyPDFLoader(file_path)
                            docs = loader.load()
                            text_content = " ".join([d.page_content for d in docs])
                        else:
                            with open(file_path, "r", encoding="utf-8") as f:
                                text_content = f.read()
                            docs = [{"page_content": text_content}]

                        # Split text into chunks
                        splitter = RecursiveCharacterTextSplitter(chunk_size=1500, chunk_overlap=200)
                        
                        if uploaded_file.name.endswith(".pdf"):
                            chunks = splitter.create_documents([d.page_content for d in docs])
                        else:
                            chunks = splitter.create_documents([text_content])

                        word_count = len(text_content.split())

                        if word_count < 5000:
                            summarize_chain = load_summarize_chain(llm, chain_type="stuff", verbose=True)
                        else:
                            summarize_chain = load_summarize_chain(llm, chain_type="map_reduce", verbose=True)

                        summary = summarize_chain.run(chunks)

                        st.subheader("🧾 Summary:")
                        st.write(summary)

                        # Generate unique filename
                        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                        audio_filename = f"{username}_{timestamp}.wav"
                        
                        # Create audio directory if it doesn't exist
                        os.makedirs("audio_files", exist_ok=True)
                        audio_path = os.path.join("audio_files", audio_filename)

                        def generate_podcast_audio(text, output_path, voice="Celeste-PlayAI"):
                            model = "playai-tts"
                            response = client.audio.speech.create(
                                model=model,
                                voice=voice,
                                input=text,
                                response_format="wav"
                            )
                            response.write_to_file(output_path)
                            return output_path

                        try:
                            audio_path = generate_podcast_audio(summary, audio_path, voice="Celeste-PlayAI")
                        except Exception:
                            st.warning("⚠️ Groq TTS limit reached — using gTTS fallback.")
                            tts = gTTS(summary)
                            audio_path = audio_path.replace(".wav", ".mp3")
                            tts.save(audio_path)

                        st.audio(audio_path)
                        st.success("🎧 Podcast generated successfully!")

                        # Save to database
                        save_podcast(user_id, uploaded_file.name, summary, audio_path)
                        
                        # Add to session
                        new_entry = {"title": uploaded_file.name, "summary": summary, "audio": audio_path}
                        st.session_state.session_podcasts.append(new_entry)

                    except Exception as e:
                        st.error(f"❌ Error generating podcast: {str(e)}")
                    finally:
                        # Clean up temp file
                        if os.path.exists(file_path):
                            os.unlink(file_path)

        # Display current session podcasts
        if st.session_state.session_podcasts:
            st.subheader("📚 Podcasts Generated This Session")
            for i, pod in enumerate(st.session_state.session_podcasts):
                with st.expander(f"🎧 {i+1}. {pod['title']}"):
                    st.write(pod["summary"])
                    if os.path.exists(pod["audio"]):
                        st.audio(pod["audio"])

    # ---------------- TAB 2: Research Assistant ----------------
    with tab2:
        st.header("🤖 Research Assistant")
        st.markdown("**🧩 Active Tools:** Wikipedia, ArXiv, Web Search")

        for msg in st.session_state.mes:
            st.chat_message(msg["role"]).write(msg["content"])

        st.markdown("<div style='height: 100px;'></div>", unsafe_allow_html=True)
        prompt = st.chat_input("Ask me anything about your topic...")

        if prompt:
            st.session_state.mes.append({"role": "user", "content": prompt})
            st.chat_message("user").write(prompt)

            agent = create_react_agent(
            model=llm,
            tools=tools
            )

            with st.spinner("🔍 Researching across tools... please wait"):
                try:
                    response = agent.invoke({"messages": [("user", prompt)]})
                    output_text = response["messages"][-1].content
                except Exception as e:
                    output_text = f"Sorry, I encountered an error: {str(e)}"

            st.chat_message("ai").write(output_text)
            st.session_state.mes.append({"role": "ai", "content": output_text})

    # ---------------- TAB 3: Podcast History ----------------
    with tab3:
        st.header("🗂️ Podcast History")

        user_history = get_user_podcasts(user_id)

        if user_history:
            for i, pod in enumerate(user_history):
                with st.expander(f"🎧 {i+1}. {pod['title']} - {pod['created_at'][:10]}"):
                    st.write("**Summary:**")
                    st.write(pod["summary"])
                    if os.path.exists(pod["audio"]):
                        st.audio(pod["audio"])
                    else:
                        st.warning("⚠️ Audio file not found")
        else:
            st.info("ℹ️ No podcast history yet. Generate one from the 'Podcast Generator' tab!")

# -------------------------------
# Conditional Rendering
# -------------------------------
if st.session_state.logged_in:
    show_main_app()
else:
    show_auth_page()




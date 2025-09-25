import os
import requests
import streamlit as st
from dotenv import load_dotenv
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_google_genai import ChatGoogleGenerativeAI
import mimetypes
import tempfile

# ====================
# Load environment keys
# ====================
load_dotenv()
DEEPGRAM_API_KEY = os.getenv("DEEPGRAM_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# ====================
# Streamlit App Configuration
# ====================
st.set_page_config(page_title="AI Audio Chatbot", page_icon="🎙️", layout="wide")

st.title("🎙️ AI Audio Chatbot")
st.write("Upload an audio file → Transcribed with Deepgram → Chat with Gemini AI (with memory)")

# ====================
# API Key Validation
# ====================
if not DEEPGRAM_API_KEY:
    st.error("❌ Missing Deepgram API Key in .env file. Please add DEEPGRAM_API_KEY to your .env file.")
    st.stop()
if not GEMINI_API_KEY:
    st.error("❌ Missing Gemini API Key in .env file. Please add GEMINI_API_KEY to your .env file.")
    st.stop()

# ====================
# Session State Initialization
# ====================
if 'history' not in st.session_state:
    st.session_state.history = [
        SystemMessage(content="You are a helpful AI assistant. Answer user questions based on the provided transcription. Keep the conversation flowing naturally.")
    ]

# ====================
# Transcription Functions
# ====================
def transcribe_audio_primary(audio_file):
    """Primary method for transcribing audio using Deepgram API"""
    try:
        url = "https://api.deepgram.com/v1/listen"
        headers = {
            "Authorization": f"Token {DEEPGRAM_API_KEY}"
        }
        
        # Fixed parameters - use lowercase string values
        params = {
            "detect_language": "true", 
            "punctuate": "true",
            "model": "nova-2",
            "smart_format": "true",
            "diarize": "false"
        }

        # Prepare file for upload
        files = {
            'audio': (
                audio_file.name, 
                audio_file.getvalue(), 
                audio_file.type or 'audio/mpeg'
            )
        }
        
        response = requests.post(url, headers=headers, params=params, files=files, timeout=120)
        
        # Handle errors more gracefully
        if response.status_code != 200:
            # Don't show error for primary method - just return None to try alternative
            return None
            
        result = response.json()
        
        # Validate response structure
        if not result.get("results", {}).get("channels"):
            return None
            
        alternatives = result["results"]["channels"][0].get("alternatives", [])
        if not alternatives:
            return None
            
        transcript = alternatives[0].get("transcript", "")
        
        if not transcript.strip():
            return None
            
        return transcript.strip()

    except Exception:
        # Silently fail for primary method to try alternative
        return None

def transcribe_audio_alternative(audio_file):
    """Alternative method using raw binary data"""
    try:
        url = "https://api.deepgram.com/v1/listen"
        headers = {
            "Authorization": f"Token {DEEPGRAM_API_KEY}",
            "Content-Type": audio_file.type or "audio/mpeg"
        }
        
        params = {
            "detect_language": "true",
            "punctuate": "true",
            "model": "nova-2",
            "smart_format": "true"
        }

        # Send raw audio data
        response = requests.post(
            url, 
            headers=headers, 
            params=params, 
            data=audio_file.getvalue(),
            timeout=120
        )
        
        if response.status_code != 200:
            st.error(f"❌ Transcription failed - API Error {response.status_code}: {response.text}")
            return None
            
        result = response.json()
        transcript = result["results"]["channels"][0]["alternatives"][0]["transcript"]
        
        if not transcript.strip():
            st.warning("⚠️ Transcription is empty. Audio might be too quiet or unclear.")
            return None
            
        return transcript.strip()

    except Exception as e:
        st.error(f"❌ Transcription error: {str(e)}")
        return None

def validate_audio_file(audio_file):
    """Validate uploaded audio file"""
    if not audio_file:
        return False, "No file uploaded"
    
    # Check file size (25MB limit)
    file_size_mb = len(audio_file.getvalue()) / (1024 * 1024)
    if file_size_mb > 25:
        return False, f"File too large ({file_size_mb:.1f} MB). Maximum size is 25MB."
    
    # Check file type
    allowed_types = ["audio/wav", "audio/mpeg", "audio/mp3", "audio/m4a", "audio/flac", "audio/ogg"]
    file_extension = os.path.splitext(audio_file.name)[1].lower()
    allowed_extensions = [".wav", ".mp3", ".m4a", ".flac", ".ogg"]
    
    if audio_file.type not in allowed_types and file_extension not in allowed_extensions:
        return False, f"Unsupported file type. Supported formats: {', '.join(allowed_extensions)}"
    
    return True, f"Valid file: {audio_file.name} ({file_size_mb:.1f} MB)"

# ====================
# File Upload Section
# ====================
st.subheader("📁 Upload Audio File")

uploaded_file = st.file_uploader(
    "Choose an audio file", 
    type=["wav", "mp3", "m4a", "flac", "ogg"], 
    key="file_uploader",
    help="Supported formats: WAV, MP3, M4A, FLAC, OGG. Maximum file size: 25MB"
)

if uploaded_file:
    # Validate file
    is_valid, validation_message = validate_audio_file(uploaded_file)
    
    if not is_valid:
        st.error(f"❌ {validation_message}")
        st.stop()
    else:
        st.success(f"✅ {validation_message}")
    
    # Check if we need to transcribe (new file or not transcribed yet)
    file_changed = st.session_state.get("last_uploaded_file") != uploaded_file.name
    needs_transcription = "transcript" not in st.session_state or file_changed
    
    if needs_transcription:
        st.info("🎧 Starting transcription process...")
        
        # Progress tracking
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        with st.spinner('Transcribing audio... This may take up to 2 minutes for longer files.'):
            # Update progress
            progress_bar.progress(25)
            status_text.text("Sending file to Deepgram...")
            
            # Try primary transcription method
            transcript = transcribe_audio_primary(uploaded_file)
            progress_bar.progress(50)
            
            # If primary fails, try alternative method
            if transcript is None:
                status_text.text("Primary method failed, trying alternative method...")
                transcript = transcribe_audio_alternative(uploaded_file)
                progress_bar.progress(75)
            else:
                status_text.text("Primary method succeeded!")
                progress_bar.progress(75)
            
            progress_bar.progress(100)
            
            if transcript:
                st.session_state.transcript = transcript
                st.session_state.last_uploaded_file = uploaded_file.name
                status_text.text("✅ Transcription completed successfully!")
                
                # Update system message with transcript context
                context_msg = SystemMessage(content=f"""You are a helpful AI assistant. Answer user questions based on the provided audio transcription. Keep the conversation flowing naturally and refer to the transcription content when relevant.

AUDIO TRANSCRIPTION:
{transcript}

Instructions:
- Use this transcription to answer questions about the audio content
- You can discuss topics beyond the transcription if the user asks
- Maintain a conversational and helpful tone
- Reference specific parts of the transcription when relevant""")
                
                st.session_state.history = [context_msg]
            else:
                status_text.text("❌ Transcription failed with both methods.")
                st.error("Unable to transcribe the audio file. Please check:")
                st.write("- File contains clear speech")
                st.write("- Audio quality is good")
                st.write("- File is not corrupted")
                st.write("- Your Deepgram API key is valid and has credits")
        
        # Clean up progress indicators
        progress_bar.empty()
        status_text.empty()

    # ====================
    # Display Transcription
    # ====================
    if st.session_state.get("transcript"):
        st.subheader("📜 Transcription Results")
        
        with st.expander("View Full Transcript", expanded=True):
            transcript_text = st.session_state.transcript
            st.write(transcript_text)
            
            # Transcript statistics
            word_count = len(transcript_text.split())
            char_count = len(transcript_text)
            st.caption(f"📊 Statistics: {word_count} words, {char_count} characters")
            
            # Download button for transcript
            st.download_button(
                label="📥 Download Transcript",
                data=transcript_text,
                file_name=f"transcript_{uploaded_file.name}.txt",
                mime="text/plain"
            )

        # ====================
        # Chat Interface
        # ====================
        st.subheader("🤖 Chat with AI Assistant")
        st.caption("Ask questions about the transcribed audio or chat about anything!")
        
        # Display chat history (skip system message)
        chat_container = st.container()
        with chat_container:
            for i, msg in enumerate(st.session_state.history[1:], 1):
                with st.chat_message(msg.type):
                    st.markdown(msg.content)

        # Chat input
        if prompt := st.chat_input("Ask me about the audio content or anything else..."):
            # Add user message to history and display
            user_message = HumanMessage(content=prompt)
            st.session_state.history.append(user_message)
            
            with st.chat_message("user"):
                st.markdown(prompt)

            # Generate AI response
            with st.chat_message("assistant"):
                message_placeholder = st.empty()
                
                try:
                    # Initialize Gemini AI with free tier friendly settings
                    llm = ChatGoogleGenerativeAI(
                        model="gemini-1.5-flash",  # Use flash model for free tier
                        google_api_key=GEMINI_API_KEY,
                        convert_system_message_to_human=True,
                        temperature=0.7,
                        max_tokens=512  # Reduced for free tier
                    )
                    
                    # Limit conversation history to avoid token limits
                    limited_history = st.session_state.history[:1]  # Keep system message
                    if len(st.session_state.history) > 5:
                        # Keep only recent messages for context
                        limited_history.extend(st.session_state.history[-4:])
                    else:
                        limited_history = st.session_state.history
                    
                    # Generate response with rate limiting protection
                    with st.spinner("🤔 AI is thinking..."):
                        import time
                        time.sleep(1)  # Small delay to help with rate limits
                        response = llm.invoke(limited_history)
                        
                    # Add AI response to history and display
                    ai_message = AIMessage(content=response.content)
                    st.session_state.history.append(ai_message)
                    message_placeholder.markdown(response.content)
                    
                except Exception as e:
                    error_str = str(e)
                    if "429" in error_str or "quota" in error_str.lower():
                        st.error("❌ **Gemini API Rate Limit Exceeded**")
                        st.warning("""
                        **Solutions:**
                        1. **Wait a few minutes** - Free tier has strict rate limits
                        2. **Use shorter messages** - Reduce token usage
                        3. **Upgrade to paid plan** - Get higher quotas
                        4. **Try again later** - Limits reset over time
                        
                        The free tier allows:
                        - 15 requests per minute
                        - 1 million tokens per day
                        - 1,500 requests per day
                        """)
                        st.info("💡 **Tip**: Try asking shorter, more focused questions to stay within limits.")
                    else:
                        st.error(f"❌ Error generating response: {error_str}")
                    
                    # Remove the user message if AI response failed
                    if st.session_state.history and isinstance(st.session_state.history[-1], HumanMessage):
                        st.session_state.history.pop()

# ====================
# Sidebar Controls
# ====================
with st.sidebar:
    st.header("🎛️ Controls")
    
    # File info
    if uploaded_file:
        st.subheader("📁 Current File")
        file_size_mb = len(uploaded_file.getvalue()) / (1024 * 1024)
        st.info(f"**{uploaded_file.name}**\n{file_size_mb:.1f} MB")
    
    st.subheader("⚠️ API Limits")
    st.warning("""
    **Gemini Free Tier Limits:**
    - 15 requests/minute
    - 1M tokens/day  
    - 1,500 requests/day
    
    💡 Keep questions short!
    """)
    
    st.subheader("🗂️ Session Management")
    
    # Clear chat history only
    if st.button("🧹 Clear Chat History", type="secondary", use_container_width=True):
        if "transcript" in st.session_state:
            # Keep transcript but reset chat
            transcript = st.session_state.transcript
            context_msg = SystemMessage(content=f"""You are a helpful AI assistant. Answer user questions based on the provided audio transcription.

AUDIO TRANSCRIPTION:
{transcript}""")
            st.session_state.history = [context_msg]
            st.success("Chat history cleared! Transcript preserved.")
        st.rerun()
    
    # Start completely new session
    if st.button("🔄 New Session", type="primary", use_container_width=True):
        st.session_state.clear()
        st.success("New session started!")
        st.rerun()
    
    # Export chat history
    if len(st.session_state.get("history", [])) > 1:
        st.subheader("📤 Export")
        chat_export = ""
        for msg in st.session_state.history[1:]:  # Skip system message
            role = "User" if isinstance(msg, HumanMessage) else "Assistant"
            chat_export += f"{role}: {msg.content}\n\n"
        
        st.download_button(
            label="💾 Export Chat",
            data=chat_export,
            file_name="chat_history.txt",
            mime="text/plain",
            use_container_width=True
        )
    
    # Debug information
    with st.expander("🔧 Debug Info"):
        st.json({
            "session_keys": list(st.session_state.keys()),
            "transcript_length": len(st.session_state.get("transcript", "")),
            "chat_messages": len(st.session_state.get("history", [])) - 1,  # Exclude system message
            "last_file": st.session_state.get("last_uploaded_file", "None")
        })

# ====================
# Footer
# ====================
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666; font-size: 0.8em;'>
    <p>🎙️ AI Audio Chatbot | Powered by Deepgram + Google Gemini</p>
    <p>Upload audio → Get transcription → Chat with AI about the content</p>
</div>
""", unsafe_allow_html=True)
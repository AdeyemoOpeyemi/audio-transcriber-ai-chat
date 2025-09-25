# 🎙️ Audio Transcriber & AI Chat

**Audio Transcriber & AI Chat** is a Streamlit web application designed to **transcribe audio files** using **Deepgram** and then allow users to **chat with an AI assistant powered by Google Gemini** based on the transcription.

---

## Features

- **Audio Transcription (Primary Focus)**  
  - Supports WAV, MP3, M4A, FLAC, OGG formats (up to 25MB)  
  - Automatic speech recognition via Deepgram API  
  - Provides fallback transcription method if primary fails  
  - Full transcript display with word & character count  
  - Downloadable transcript  

- **AI Chat Based on Transcription**  
  - Interact with Gemini AI about audio content  
  - Context-aware responses from the transcript  
  - Maintains chat history and session memory  
  - Export conversation to text  

- **Interactive UI & Controls**  
  - Upload progress and transcription status  
  - Sidebar with API usage info and session management  
  - Clear chat, start new session, and export options  

- **Error Handling & API Checks**  
  - Validate uploaded audio format and size  
  - Verify Deepgram and Gemini API keys  
  - Rate limit warnings for Gemini Free Tier  

---

## Installation

1. Clone the repo:

```bash
git clone https://github.com/your-username/audio-transcriber-ai-chat.git
cd audio-transcriber-ai-chat

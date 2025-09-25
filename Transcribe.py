


import os
import requests
import mimetypes
from dotenv import load_dotenv

# ====================
# Load Deepgram API Key
# ====================
load_dotenv()
DEEPGRAM_API_KEY = os.getenv("DEEPGRAM_API_KEY")

if not DEEPGRAM_API_KEY:
    raise ValueError("❌ Missing Deepgram API Key in .env file. Please add it as:\nDEEPGRAM_API_KEY=dg_secret_xxxxx")

# ====================
# Ask for file input
# ====================
audio_path = input("🎵 Enter the full path to your audio file: ").strip()

if not os.path.exists(audio_path):
    raise FileNotFoundError(f"❌ File not found: {audio_path}")

print(f"\n✅ File found: {audio_path}")
print(f"📁 File size: {os.path.getsize(audio_path) / 1024:.2f} KB")

# ====================
# Send to Deepgram API
# ====================
print("\n🚀 Sending to Deepgram for transcription...")

url = "https://api.deepgram.com/v1/listen"

# Determine the MIME type of the uploaded file
mime_type = mimetypes.guess_type(audio_path)[0] or "audio/mpeg"

# Send the raw data with the correct Content-Type header
headers = {
    "Authorization": f"Token {DEEPGRAM_API_KEY}",
    "Content-Type": mime_type # Explicitly set the content type
}
params = {"detect_language": "true", "punctuate": "true"}

with open(audio_path, "rb") as f:
    audio_data = f.read()
    response = requests.post(url, headers=headers, params=params, data=audio_data)

    # Print raw response for debugging if error happens
    if response.status_code != 200:
        print(f"\n❌ Deepgram Error {response.status_code}: {response.text}")
        response.raise_for_status()

    result = response.json()

# ====================
# Extract & Display Transcript
# ====================
try:
    transcript = result["results"]["channels"][0]["alternatives"][0]["transcript"]
    print("\n📜 Transcription Result")
    print("--------------------------------------------------")
    print(transcript if transcript else "⚠️ No speech detected in audio.")
except KeyError:
    print("❌ Unexpected response format from Deepgram:", result)

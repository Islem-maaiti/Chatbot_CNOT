import streamlit as st
import requests
import speech_recognition as sr
import io
import pandas as pd
import json
import base64
from nlp import find_intent
from googletrans import Translator

# Initialize the translator
translator = Translator()
st.title("💬 Chatbot Rasa with Streamlit")

# Load preferences from a JSON file
def load_preferences():
    try:
        with open("preferences.json", "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return {
            "primary_color": "#D4F1F4",
            "secondary_color": "#FAD02E",
            "avatar_url": "https://cdn-icons-png.flaticon.com/512/64/64572.png"
        }

# Save preferences to a JSON file
def save_preferences(preferences):
    with open("preferences.json", "w") as f:
        json.dump(preferences, f)

# Initialize session state to store preferences and other data
preferences = load_preferences()

if 'history' not in st.session_state:
    st.session_state.history = []
if 'text_input' not in st.session_state:
    st.session_state.text_input = ""
if 'primary_color' not in st.session_state:
    st.session_state.primary_color = preferences["primary_color"]
if 'secondary_color' not in st.session_state:
    st.session_state.secondary_color = preferences["secondary_color"]
if 'user_avatar_url' not in st.session_state:
    st.session_state.user_avatar_url = preferences["avatar_url"]
if 'avatar_upload' not in st.session_state:
    st.session_state.avatar_upload = None
if 'pdf_data' not in st.session_state:
    st.session_state.pdf_data = None
if 'show_emojis' not in st.session_state:
    st.session_state.show_emojis = False

# Initialize recognizer
recognizer = sr.Recognizer()

# Function to save conversation history to a file
def save_history():
    with open("chat_history.json", "w") as f:
        json.dump(st.session_state.history, f)

# Function to load conversation history from a file
def load_history():
    try:
        with open("chat_history.json", "r") as f:
            st.session_state.history = json.load(f)
    except FileNotFoundError:
        st.session_state.history = []

# Load history on startup
load_history()

# Function to send the message to Rasa and get the response
def get_response(message):
    detected_lang = translator.detect(message).lang
    
    if detected_lang == 'fr':
        message = translator.translate(message, dest='en').text
    
    recognized_intent = find_intent(message)
    
    url = "http://localhost:5005/webhooks/rest/webhook"
    payload = {"sender": "user", "message": recognized_intent}
    response = requests.post(url, json=payload)
    return response.json()

# Function to handle speech recognition
def handle_speech():
    with sr.Microphone() as source:
        st.write("🎙️ Recording...")
        audio = recognizer.listen(source)
        try:
            text = recognizer.recognize_google(audio)
            detected_lang = translator.detect(text).lang
            if detected_lang == 'fr':
                text = translator.translate(text, dest='en').text

            st.session_state.text_input = text
            st.write(f"🗣️ You said: {text}")
        except sr.UnknownValueError:
            st.write("❌ Sorry, I could not understand the audio.")
        except sr.RequestError as e:
            st.write(f"⚠️ Service error: {e}")

# Function to update the conversation area and save history
def update_conversation_area():
    conversation_area.empty()
    with conversation_area.container():
        for chat in st.session_state.history:
            if chat['sender'] == "user":
                st.markdown(f"""
                <div class="chat-box user">
                    <img src="{st.session_state.user_avatar_url}" class="avatar">
                    <div class="user-msg">
                        {chat['message']}
                    </div>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div class="chat-box bot">
                    <div class="bot-msg">
                        {chat['message']}
                    </div>
                    <img src="{bot_avatar_url}" class="avatar">
                </div>
                """, unsafe_allow_html=True)
    save_history()

# Apply selected colors
def apply_styles():
    st.markdown(f"""
    <style>
        body {{background-color: #1e1e1e;}}
        .chat-box {{display: flex; align-items: center; margin: 10px 0; padding: 10px;}}
        .user-msg {{background-color: {st.session_state.primary_color}; border-radius: 10px; padding: 10px; max-width: 60%; margin-right: 10px;}}
        .bot-msg {{background-color: {st.session_state.secondary_color}; border-radius: 10px; padding: 10px; max-width: 60%; margin-left: 10px;}}
        .avatar {{width: 50px; height: 50px; border-radius: 50%;}}
        .chat-box.user {{justify-content: flex-start;}}
        .chat-box.bot {{justify-content: flex-end;}}
        .stSidebar {{background-color: {st.session_state.primary_color};}}
        button {{background-color: #4CAF50; color: white; border: none; padding: 10px 24px; text-align: center; border-radius: 12px;}}
        button:hover {{background-color: #45a049;}}
        .emoji-btn {{font-size: 24px; padding: 5px;}}
        .emoji-container {{display: flex; flex-wrap: wrap; gap: 10px;}}
        .emoji {{font-size: 24px; cursor: pointer;}}
    </style>
    """, unsafe_allow_html=True)

# Set default avatars
bot_avatar_url = "https://cdn-icons-png.flaticon.com/512/327/327779.png"

if st.session_state.avatar_upload is not None:
    st.session_state.user_avatar_url = f"data:image/png;base64,{base64.b64encode(st.session_state.avatar_upload.read()).decode()}"

apply_styles()
conversation_area = st.empty()
update_conversation_area()





st.session_state.text_input = st.text_input("You:", value=st.session_state.text_input)

# Display message input and controls in columns
col1, col2, col3 = st.columns([1, 1, 1])

# Text input for user message in the first column


# Button to start speech recognition in the second column
with col1:
    mic_icon = "🎤"
    if st.button(mic_icon):
        handle_speech()


with col2:
    if st.button("Upload PDF"):
        st.markdown("""
        <meta http-equiv="refresh" content="0; url=http://localhost:8502/" />
    """, unsafe_allow_html=True)           

# Button to send message in the third column
with col3:
    if st.button("Send"):
        user_input = st.session_state.text_input
        if user_input:
            st.session_state.history.append({"sender": "user", "message": user_input})
            response = get_response(user_input)
            for res in response:
                st.session_state.history.append({"sender": "bot", "message": res['text']})
            update_conversation_area()

# Button to clear history
if st.button("Clear History"):
    st.session_state.history = []
    update_conversation_area()
st.sidebar.title("⚙️ Controls")
# Add quick reply buttons
st.sidebar.markdown("### Quick Replies")
quick_replies = ["Hello", "Thank you", "Goodbye"]
for reply in quick_replies:
    if st.sidebar.button(reply):
        st.session_state.history.append({"sender": "user", "message": reply})
        response = get_response(reply)
        for res in response:
            st.session_state.history.append({"sender": "bot", "message": res['text']})
        update_conversation_area()

# Button to show/hide emojis

st.sidebar.markdown("### 🙂 Emojis")
emoji_dict = {
        "😊": "Smile",
        "😂": "Laugh",
        "😍": "Love",
        "😢": "Sad",
        "😡": "Angry"
    }
cols = st.sidebar.columns(5)
for i, (emoji_char, emoji_desc) in enumerate(emoji_dict.items()):
        with cols[i % 5]:
            if st.button(f"{emoji_char}", key=f"emoji_{i}"):
                if st.session_state.history and st.session_state.history[-1]['sender'] == "bot":
                    st.session_state.history[-1]['message'] += f" {emoji_char}"
                    update_conversation_area()

# Download history
# Download history options
st.sidebar.markdown("### 📂 Download History")
download_format = st.sidebar.radio("Choose format", ["CSV", "TXT"])

if download_format == "CSV":
    csv = pd.DataFrame(st.session_state.history).to_csv(index=False)
    st.sidebar.download_button(
        label="Download CSV",
        data=csv,
        file_name='chat_history.csv',
        mime='text/csv'
    )
elif download_format == "TXT":
    txt_history = "\n".join([f"{chat['sender']}: {chat['message']}" for chat in st.session_state.history])
    st.sidebar.download_button(
        label="Download TXT",
        data=txt_history,
        file_name='chat_history.txt',
        mime='text/plain'
    )
# Personalization options
st.sidebar.title("🎨 Personalization")
primary_color = st.sidebar.color_picker("Pick a primary color", st.session_state.primary_color)
secondary_color = st.sidebar.color_picker("Pick a secondary color", st.session_state.secondary_color)
avatar_upload = st.sidebar.file_uploader("Upload your avatar", type=["png", "jpg", "jpeg"])

if avatar_upload is not None:
    st.session_state.avatar_upload = avatar_upload

if primary_color != st.session_state.primary_color or secondary_color != st.session_state.secondary_color or avatar_upload:
    st.session_state.primary_color = primary_color
    st.session_state.secondary_color = secondary_color

    if avatar_upload:
        st.session_state.user_avatar_url = f"data:image/png;base64,{base64.b64encode(avatar_upload.read()).decode()}"

    save_preferences({
        "primary_color": st.session_state.primary_color,
        "secondary_color": st.session_state.secondary_color,
        "avatar_url": st.session_state.user_avatar_url
    })

    apply_styles()
    update_conversation_area()

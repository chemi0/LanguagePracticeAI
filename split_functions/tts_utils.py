import os
from gtts import gTTS

# Text-to-Speech
def speak_response(text, language):
    lang_code = 'en'
    if language == "Japanese":
        lang_code = 'ja'
    elif language == "Spanish":
        lang_code = 'es'
    elif language == "French":
        lang_code = "fr"
    try:
        tts = gTTS(text=text, lang=lang_code)
        tts.save("response.mp3")
        os.system("start response.mp3")
    except Exception as e:
        print(f"Error in text to speech: {e}")
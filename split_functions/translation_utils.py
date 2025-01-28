# translation_utils.py
# Functions for translation and text-to-speech
from config import translator
from gtts import gTTS
import os

# Function to translate to selected language (Synchronous version)
def translate_to_language(text, loop, language):
    dest_lang = 'en'  # Default Language
    if language == "Japanese":
        dest_lang = 'ja'
    elif language == "Spanish":
        dest_lang = "es"
    elif language == "French":
        dest_lang = "fr"

    try:
        translation = translator.translate(text, dest=dest_lang)
        if hasattr(translation, 'text'):
            return translation.text
        else:  # Handle coroutine objects returned by googletrans
            try:
                return loop.run_until_complete(translation).text
            except Exception as e:
                return f"Translation Error: {str(e)}"
    except Exception as e:
        return f"Translation Error: {str(e)}"

# Function to translate to English (Synchronous version)
def translate_to_english(text, loop, language, translation_language):
    src_lang = 'en'
    dest_lang = 'en' # Default translation language
    if language == "Japanese":
        src_lang = 'ja'
    elif language == "Spanish":
        src_lang = "es"
    elif language == "French":
        src_lang = "fr"

    if translation_language == "Japanese":
            dest_lang = 'ja'
    elif translation_language == "Spanish":
        dest_lang = "es"
    elif translation_language == "French":
        dest_lang = "fr"
    try:
        translation = translator.translate(text, src=src_lang, dest=dest_lang)

        if hasattr(translation, 'text'):
            return translation.text
        else:  # Handle coroutine objects returned by googletrans
            try:
                return loop.run_until_complete(translation).text
            except Exception as e:
                return f"Translation Error: {str(e)}"
    except Exception as e:
        return f"Translation Error: {str(e)}"

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
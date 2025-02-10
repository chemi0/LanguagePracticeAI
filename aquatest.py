import google.generativeai as genai
from googletrans import Translator
import os
from gtts import gTTS
import tkinter as tk
from tkinter import font, scrolledtext, ttk
import asyncio
import re
import speech_recognition as sr # Import speech_recognition
import threading # Import threading for voice recording
import time # Import time - although not strictly needed in this version, keeping it as it was in side program
import pygame # Import pygame for better audio control

# Configure Google Gemini API
genai.configure(api_key="AIzaSyAurbpVsBDTcNp7VxQ4b8DTBIWjq2_PekA") # Replace with your actual API key
model = genai.GenerativeModel("gemini-1.5-flash")

# Translator for Japanese to English
translator = Translator()

# Conversation histories for each language and role
conversation_histories = {}

# Default Language and Default translation language
DEFAULT_LANGUAGE = "English"
DEFAULT_TRANSLATION_LANGUAGE = "English"
DEFAULT_COMPLEXITY_LEVEL = "Level 2" # Default complexity level

current_complexity_level = DEFAULT_COMPLEXITY_LEVEL # Global variable to store complexity level

# Predefined roles and their corresponding prompts and initial greetings
roles = {
    "Boss": {
        "prompt": "I'm learning {language} and the best way is to learn is to have conversations in certain scenarios so lets pretend that you are my boss. Be direct and professional in your responses. Respond ONLY in {language}. {complexity_instructions}. Keep the sentences as brief as possible to not have long paragraphs of speech",
        "greeting": "Good morning. Do you need anything?"
    },
    "Best Friend": {
        "prompt": "I'm learning {language} and the best way to learn is to have conversations in certain scenarios so lets pretend that you are my best friend. Be casual and friendly in your responses. Respond ONLY in {language}. {complexity_instructions}. Keep the sentences as brief as possible to not have long paragraphs of speech",
        "greeting": "Yo, how are you"
    },
    "Stranger": {
        "prompt": "I'm learning {language} and the best way to learn is to have conversations in certain scenarios so lets pretend that you are a stranger. Respond neutrally but be polite. Respond ONLY in {language}. {complexity_instructions}. Keep the sentences as brief as possible to not have long paragraphs of speech",
        "greeting": "Hello. Can I help you?"
    },
    "Mother": {
        "prompt": "I'm learning {language} and the best way is to learn is to have conversations in certain scenarios so lets pretend that you are my mother. Be caring and supportive in your responses. Respond ONLY in {language}. {complexity_instructions}. Keep the sentences as brief as possible to not have long paragraphs of speech",
        "greeting": "Oh, how have you been?"
    },
    "Teacher": {
        "prompt": "I'm learning {language} and the best way is to learn is to have conversations in certain scenarios so lets pretend that you are my {language} teacher. Be educational and helpful. Respond ONLY in {language}. {complexity_instructions}. Keep the sentences as brief as possible to not have long paragraphs of speech",
        "greeting": "Hello. What will you study today?"
    },
    "Drunk Friend": {
        "prompt": "I'm learning {language} and the best way is to learn is to have conversations in certain scenarios so lets pretend that you are my drunk friend. Be very silly and use slang. Respond ONLY in {language}. {complexity_instructions}. Keep the sentences as brief as possible to not have long paragraphs of speech",
        "greeting": "Wow! How are you doing?"
    }
}

complexity_levels_instructions = {
    "Level 1": "Respond with very simple vocabulary and grammar. Avoid slang, idioms, and complex sentence structures. Aim for basic communication.",
    "Level 2": "Respond with intermediate vocabulary and grammar. You can use some common idioms and slightly more native sentences, but keep it relatively clear and easy to understand for a language learner.",
    "Level 3": "Respond with native vocabulary and grammar, like a fluent native speaker. Use idioms, slang if appropriate for the role, and complex sentence structures to simulate native conversation and take into account the role in which you have."
}


current_role = ""
last_ai_response = ""
ai_greeting_sent = False
current_language = DEFAULT_LANGUAGE
current_translation_language = DEFAULT_TRANSLATION_LANGUAGE

# --- Global Constants for Voice Input (from side program) ---
BOT_NAME = "Gemini AI"
USER_NAME = "You"
RECORDING_TEXT = "Listening..."
IDLE_TEXT = "Click 'Speak' and start talking..."
SPEAK_BUTTON_TEXT = "Speak" # Although UI elements are translated, keeping these for internal logic
STOP_BUTTON_TEXT = "Stop Speaking" # Although UI elements are translated, keeping these for internal logic
STOP_TTS_BUTTON_TEXT = "Stop TTS" # New constant for Stop TTS button
VOLUME_LABEL_TEXT = "Volume" # New constant for Volume Slider Label


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

# Function to generate conversation with Google Gemini
def generate_response(input_text, current_role, language, complexity_level):
    # Initialize conversation history for language and role if it doesn't exist
    if (language, current_role) not in conversation_histories:
        conversation_histories[(language, current_role)] = []

    conversation_history = conversation_histories[(language, current_role)]

    # Update conversation history
    conversation_history.append(f"You: {input_text}")

    # Build the prompt with conversation history and role
    complexity_instructions = complexity_levels_instructions.get(complexity_level, complexity_levels_instructions[DEFAULT_COMPLEXITY_LEVEL]) # Get complexity instructions based on level
    prompt = roles[current_role]["prompt"].format(language=language, complexity_instructions=complexity_instructions) + "\n" if current_role else ""
    prompt += "\n".join(conversation_history)

    try:
        response = model.generate_content(prompt)
        ai_response = response.text

        # Append AI response to conversation history
        conversation_history.append(f"AI: {ai_response}")

        # Limit conversation history to prevent excessive prompt length
        if len(conversation_history) > 20:
            conversation_history = conversation_history[-20:]

        return ai_response
    except Exception as e:
        return f"Error generating response: {str(e)}"

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

# Text-to-Speech function using pygame for non-blocking playback
def speak_response(text, language, chat_app_instance): # Pass ChatApp instance
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

        # Load sound and play in a new thread
        sound = pygame.mixer.Sound("response.mp3")
        current_volume = float(chat_app_instance.tts_volume.get())
        sound.set_volume(current_volume) # Set volume here using instance variable
        chat_app_instance.current_tts_sound = sound # Store sound object
        chat_app_instance.root.after(0, chat_app_instance.enable_stop_tts_button) # Enable Stop TTS button
        threading.Thread(target=lambda s=sound, instance=chat_app_instance: play_sound_non_blocking(s, instance), daemon=True).start() # Pass instance

    except Exception as e:
        print(f"Error in text to speech: {e}")

def play_sound_non_blocking(sound, chat_app_instance): # Pass ChatApp instance
    sound.play()
    while pygame.mixer.get_busy(): # Wait until sound finishes playing
        time.sleep(0.1)
    chat_app_instance.root.after(0, chat_app_instance.disable_stop_tts_button) # Disable Stop TTS button after playback

class ChatApp:
    def __init__(self, root, show_language_selection, initial_role, initial_language, initial_translation_language, initial_complexity_level, loop):
        self.root = root
        self.root.title("Conversation Practice Bot")
        self.root.geometry("800x750") # Increased height for volume slider
        self.loop = loop
        self.show_language_selection = show_language_selection
        self.language = initial_language  # The current language
        self.translation_language = initial_translation_language # The current translation language
        self.complexity_level = initial_complexity_level # The current complexity level
        self.chat_displays = {}  # Store chat display for each language
        self.popup = None  # To store the popup window
        self.role_mapping = {} # Mapping of translated role to english role
        self.is_recording = False
        self.recognizer = sr.Recognizer()
        self.microphone = sr.Microphone()
        self.recorded_audio = None # To store recorded audio data
        self.current_tts_sound = None # To store the currently playing sound object
        self.tts_volume = tk.DoubleVar(value=0.5) # Initialize volume to 50%
        pygame.mixer.init() # Initialize pygame mixer


        # UI Elements to Translate
        self.ui_elements = {
            "window_title": "Conversation Practice Bot",
            "send_button": "Send",
            "settings_menu":"Settings",
            "start_record_button": SPEAK_BUTTON_TEXT, # Using Constant from side program
            "stop_record_button": STOP_BUTTON_TEXT, # Using Constant from side program
            "stop_tts_button": STOP_TTS_BUTTON_TEXT, # New UI element for Stop TTS button
            "volume_label": VOLUME_LABEL_TEXT, # New UI element for Volume Slider Label
            "complexity_level_menu": "Complexity Level", # New UI Element for Complexity Level Menu
            "current_complexity_level": f"Current Level: {initial_complexity_level}" # New UI Element to display current complexity
        }

        # Configure Dark Theme
        self.root.configure(bg="#333333")  # Dark grey background
        text_font = font.Font(family="Helvetica", size=12)  # Use a nicer font

        # Create a Style
        style = ttk.Style()
        style.theme_use('clam')  # Use the clam theme
        style.configure('TButton', font=text_font, background="#555555", foreground="white", relief='flat')
        style.map('TButton',
                  background=[('active', '#666666')],
                  foreground=[('active', 'white')])  # Set the color to change when hovered

        # Conversation Display
        self.conversation_display = scrolledtext.ScrolledText(root, wrap=tk.WORD, width=80, height=20,
                                                            bg="#444444", fg="white", font=text_font)
        self.conversation_display.grid(row=0, column=0, columnspan=2, padx=10, pady=10)
        self.conversation_display.config(state=tk.DISABLED)
        self.chat_displays[self.language] = self.conversation_display

        # Status Label (for voice input feedback) - Added here, below conversation display
        self.status_label = ttk.Label(root, text=IDLE_TEXT) # Using Constant from side program
        self.status_label.grid(row=1, column=0, columnspan=2, sticky="ew", padx=10) # Span columns, expand horizontally

        # User Input
        self.input_box = tk.Entry(root, width=70, bg="#555555", fg="white", insertbackground="white", font=text_font)
        self.input_box.grid(row=2, column=0, padx=10, pady=5)

        # Send Button
        self.send_button = ttk.Button(root, text=self.ui_elements["send_button"], command=self.send_message)
        self.send_button.grid(row=2, column=1, padx=5, pady=5)

        # Voice Input Buttons (renamed to Speak and Stop Speaking, using constants)
        self.start_record_button = ttk.Button(root, text=translate_to_language(self.ui_elements["start_record_button"], self.loop, initial_translation_language), command=self.start_voice_input) # Changed command to new voice function
        self.start_record_button.grid(row=3, column=0, pady=5)

        self.stop_record_button = ttk.Button(root, text=translate_to_language(self.ui_elements["stop_record_button"], self.loop, initial_translation_language), command=self.stop_voice_input, state=tk.DISABLED) # Changed command to new stop voice function, initially disabled
        self.stop_record_button.grid(row=3, column=1, pady=5)

        # Stop TTS Button - added below voice input buttons
        self.stop_tts_button = ttk.Button(root, text=translate_to_language(self.ui_elements["stop_tts_button"], self.loop, initial_translation_language), command=self.stop_tts) # New button for Stop TTS
        self.stop_tts_button.grid(row=4, column=0, columnspan=2, pady=5) # Span columns
        self.stop_tts_button.config(state=tk.DISABLED) # Initially disabled

        # Volume Slider Label and Slider - Added below Stop TTS Button
        self.volume_label = ttk.Label(root, text=translate_to_language(self.ui_elements["volume_label"], self.loop, initial_translation_language))
        self.volume_label.grid(row=5, column=0, sticky="ew", padx=10) # Label on the left

        self.volume_slider = tk.Scale(root, from_=0.0, to=1.0, orient=tk.HORIZONTAL, resolution=0.01, variable=self.tts_volume, command=self.change_tts_volume, bg="#444444", fg="white", highlightbackground="#444444") # Slider
        self.volume_slider.grid(row=5, column=1, sticky="ew", padx=10) # Slider on the right, expanding horizontally


        # Role Dropdown
        self.role_var = tk.StringVar(root)
        self.role_var.set(initial_role)  # Initial role selection

        #Translate role options
        translated_roles = [translate_to_language(role, self.loop, initial_translation_language) for role in roles.keys()]
        self.role_dropdown = ttk.OptionMenu(root, self.role_var, translated_roles[0], *translated_roles,
                                            command=self.change_role)
        self.role_dropdown.grid(row=6, column=0, columnspan=2, pady=5)

        # Language Dropdown
        self.language_var = tk.StringVar(root)
        self.language_var.set(initial_language)
        language_options = ["English", "Japanese", "Spanish", "French"]
        self.language_dropdown = ttk.OptionMenu(root, self.language_var, initial_language, *language_options,
                                                command=self.change_language)
        self.language_dropdown.grid(row=7, column=0, columnspan=2, pady=5)

         # Settings Menu
        self.create_settings_menu()

        #Translate the UI
        self.translate_ui(initial_translation_language)
        self.translate_voice_buttons(initial_translation_language)
        self.translate_stop_tts_button(initial_translation_language) # Translate Stop TTS button
        self.translate_volume_ui_elements(initial_translation_language) # Translate Volume UI elements

        #Update the values of the dropdown menu
        self.update_role_dropdown(initial_translation_language)

        # Call set_role to display greeting of the default role
        self.set_role(initial_role, initial_language)

    def translate_volume_ui_elements(self, translation_language): # New translation function for Volume UI elements
        self.volume_label.config(text=translate_to_language(self.ui_elements["volume_label"], self.loop, translation_language))

    def change_tts_volume(self, new_volume_str): # New function to handle volume slider changes
        try:
            self.tts_volume.set(float(new_volume_str)) # Update tts_volume variable
            print(f"TTS Volume changed to: {self.tts_volume.get()}") # Optional debug print
        except ValueError:
            print("Invalid volume value")

    def translate_stop_tts_button(self, translation_language): # New translation function for Stop TTS button
        self.stop_tts_button.config(text=translate_to_language(self.ui_elements["stop_tts_button"], self.loop, translation_language))

    def enable_stop_tts_button(self): # Function to enable Stop TTS button - thread safe
        self.stop_tts_button.config(state=tk.NORMAL)

    def disable_stop_tts_button(self): # Function to disable Stop TTS button - thread safe
        self.stop_tts_button.config(state=tk.DISABLED)

    def stop_tts(self): # Stop TTS function
        if self.current_tts_sound and pygame.mixer.get_busy():
            pygame.mixer.stop()
            self.disable_stop_tts_button() # Disable Stop TTS button after stopping

    def create_settings_menu(self):
         menu_bar = tk.Menu(self.root)
         self.root.config(menu=menu_bar)

         settings_menu = tk.Menu(menu_bar, tearoff=0)
         menu_bar.add_cascade(label=translate_to_language(self.ui_elements["settings_menu"], self.loop, self.translation_language), menu=settings_menu)

         language_menu = tk.Menu(settings_menu, tearoff=0)
         settings_menu.add_cascade(label="Change Translation Language", menu=language_menu)

         language_options = ["English", "Japanese", "Spanish", "French"]
         for lang in language_options:
             language_menu.add_command(label=lang, command=lambda selected_lang=lang: self.change_translation_language(selected_lang))

         complexity_level_display = ttk.Label(settings_menu, text=translate_to_language(self.ui_elements["current_complexity_level"], self.loop, self.translation_language)) # Display current complexity level
         settings_menu.add_command(label="", state=tk.DISABLED) # Separator
         settings_menu.add_cascade(label=translate_to_language(self.ui_elements["complexity_level_menu"], self.loop, self.translation_language), command=self.show_complexity_level_popup) # Open complexity popup
         settings_menu.add_command(label="", state=tk.DISABLED) # Separator
         settings_menu.add_cascade(label=translate_to_language(self.ui_elements["current_complexity_level"], self.loop, self.translation_language), state=tk.DISABLED) # Display current level, disabled for now, can be enabled if needed.
         settings_menu.add_separator()
         settings_menu.add_command(label="Current Complexity Level:", state=tk.DISABLED) # Label
         settings_menu.add_command(label=self.complexity_level, state=tk.DISABLED) # Value


    def translate_ui(self, translation_language):
        self.root.title(translate_to_language(self.ui_elements["window_title"], self.loop, translation_language))
        self.send_button.config(text=translate_to_language(self.ui_elements["send_button"], self.loop, translation_language))
        self.translate_voice_buttons(translation_language)
        self.translate_stop_tts_button(translation_language) # Translate Stop TTS button as well
        self.translate_volume_ui_elements(translation_language) # Translate Volume UI elements
        self.ui_elements["current_complexity_level"] = f"Current Level: {self.complexity_level}" # Update complexity level text
        self.create_settings_menu() # Recreate settings menu to update translations


    def translate_voice_buttons(self, translation_language):
        self.start_record_button.config(text=translate_to_language(self.ui_elements["start_record_button"], self.loop, translation_language))
        self.stop_record_button.config(text=translate_to_language(self.ui_elements["stop_record_button"], self.loop, translation_language))

    def update_role_dropdown(self, translation_language):
         translated_roles = [translate_to_language(role, self.loop, translation_language) for role in roles.keys()]
         self.role_mapping = dict(zip(translated_roles, roles.keys())) # create the mapping of translated role to english role
         self.role_dropdown['menu'].delete(0, 'end')
         for role in translated_roles:
            self.role_dropdown['menu'].add_command(label=role, command=tk._setit(self.role_var, role, self.change_role))

    def change_translation_language(self, new_translation_language):
       self.translation_language = new_translation_language
       self.translate_ui(new_translation_language)
       self.update_role_dropdown(new_translation_language)
       self.translate_stop_tts_button(new_translation_language) # Translate Stop TTS button on language change
       self.translate_volume_ui_elements(new_translation_language) # Translate Volume UI elements

    def set_role(self, role, language):
      global current_role, ai_greeting_sent, last_ai_response, current_language

      if role in self.role_mapping: # If the selected role is the translated version, set the current role to the english version.
           current_role = self.role_mapping[role]
      else:
           current_role = role # If the selected role isn't translated use the english version.
      current_language = language
      self.clear_chat_display()
      self.add_message("System", f"AI Role set to: {current_role}") # Call add_message here with "System" as sender

      if (current_language, current_role) not in conversation_histories:
        if current_role and not ai_greeting_sent:
            greeting = roles[current_role]["greeting"]
            translated_greeting = translate_to_language(greeting, self.loop, current_language)
            self.add_ai_message(translated_greeting)
            conversation_histories[(current_language, current_role)] = [f"AI: {translated_greeting}"]
            last_ai_response = translated_greeting
            ai_greeting_sent = True
      else:  # Role is changed
          for message in conversation_histories[(current_language, current_role)]:
              self.add_message(message, is_ai_message=("AI:" in message))

    def clear_chat_display(self):
        self.conversation_display.config(state=tk.NORMAL)
        self.conversation_display.delete('1.0', tk.END)
        self.conversation_display.config(state=tk.DISABLED)

    def send_message(self):
        user_input = self.input_box.get().strip()
        print(f"send_message: Input text being sent: '{user_input}'") # DEBUG PRINT
        if user_input:
            self.add_message(USER_NAME, user_input) # Call add_message here for text input, using USER_NAME as sender
            response = generate_response(user_input, current_role, current_language, self.complexity_level)  # Use self.language and complexity level
            self.add_ai_message(response)
            global last_ai_response
            last_ai_response = response
            self.input_box.delete(0, tk.END)
            self.stop_voice_input() # Stop voice input UI if active, after sending text message
            self.stop_tts() # Stop TTS if playing

    # --- Voice Input Functions (Integrated from side program) ---
    def record_voice(self):
        r = sr.Recognizer()
        with sr.Microphone() as source:
            self.status_label.config(text=RECORDING_TEXT) # Use global constant
            r.adjust_for_ambient_noise(source)  # Adjust for noise
            audio = r.listen(source) # Listen for audio
            self.status_label.config(text=IDLE_TEXT) # Use global constant, change back to idle text
            try:
                user_message = r.recognize_google(audio, language=self.get_speech_recognition_lang_code()) # Recognize speech using Google Speech Recognition, pass language code
                self.add_message(USER_NAME, user_message) # Call general add_message for voice input now, using USER_NAME
                self.process_voice_message(user_message) # Send message to Gemini and get response
            except sr.UnknownValueError:
                self.add_message(BOT_NAME, "Could not understand audio") # Call general add_message for voice error, using BOT_NAME
            except sr.RequestError as e:
                self.add_message(BOT_NAME, f"Could not request results from Speech Recognition service; {e}") # Call general add_message for voice error, using BOT_NAME
            finally:
                self.stop_voice_input() # Stop voice input UI elements after recording
                self.stop_tts() # Stop TTS if playing

    def process_voice_message(self, user_message):
        try:
            # Call generate_response here, passing user_message, current_role and current_language
            response = generate_response(user_message, current_role, current_language, self.complexity_level)
            bot_response = response # Response from generate_response is already just the text
            self.add_ai_message(bot_response) # Use existing AI message adding function
        except Exception as e:
            self.add_message(BOT_NAME, f"Error communicating with Gemini: {e}") # Call general add_message for Gemini error, using BOT_NAME

    def add_message(self, sender, message): # Modified to be the general add_message function
        self.conversation_display.config(state=tk.NORMAL) # Enable text area for editing
        tag = sender.replace(" ", "_") # Create tag from sender name (for example "Gemini AI" becomes "Gemini_AI")
        self.conversation_display.insert(tk.END, f"{sender}: {message}\n", tag) # Insert message with sender tag
        self.conversation_display.tag_config(USER_NAME, foreground="blue") # Configure tag for user messages (same for voice and text)
        self.conversation_display.tag_config(BOT_NAME, foreground="green") # Configure tag for bot messages (same for voice and text)
        self.conversation_display.config(state=tk.DISABLED) # Disable text area from user editing
        self.conversation_display.see(tk.END) # Scroll to the end of the text

    def start_voice_input(self):
        self.start_record_button.config(state=tk.DISABLED) # Disable Speak button during recording
        self.stop_record_button.config(state=tk.NORMAL) # Enable Stop button
        self.input_box.config(state=tk.DISABLED) # Disable text input during voice recording
        self.send_button.config(state=tk.DISABLED) # Disable send button during voice recording
        threading.Thread(target=self.record_voice, daemon=True).start() # Start voice recording in new thread
        self.stop_tts() # Stop TTS if it is currently playing when starting voice input

    def stop_voice_input(self):
        self.start_record_button.config(state=tk.NORMAL) # Re-enable Speak button
        self.stop_record_button.config(state=tk.DISABLED) # Disable Stop button
        self.status_label.config(text=IDLE_TEXT) # Use global constant, reset status label
        self.input_box.config(state=tk.NORMAL) # Re-enable text input after voice recording
        self.send_button.config(state=tk.NORMAL) # Re-enable send button after voice recording

    def get_speech_recognition_lang_code(self):
        lang_code = 'en-US' # Default to english US
        if self.language == "Japanese":
            lang_code = 'ja-JP'
        elif self.language == "Spanish":
            lang_code = 'es-ES' # or es-US for US spanish
        elif self.language == "French":
            lang_code = 'fr-FR'
        return lang_code

    def add_ai_message(self, message): # add_ai_message now only handles AI specific styling and function
        self.conversation_display.config(state=tk.NORMAL)
        ai_tag = f"ai_tag_{self.conversation_display.index(tk.END).replace('.', '_')}"
        ai_label_tag = f"ai_label_tag_{self.conversation_display.index(tk.END).replace('.', '_')}"
        full_message_tag = f"full_message_tag_{self.conversation_display.index(tk.END).replace('.', '_')}"

        self.conversation_display.insert(tk.END, "AI: ", ai_label_tag)
        self.conversation_display.tag_config(ai_label_tag, foreground="blue", font=("Helvetica", 12, "bold"))
        self.conversation_display.tag_bind(ai_label_tag, '<Button-1>', lambda event, text=message: speak_response(text, self.language, self)) # Pass self (ChatApp instance) here
        self.conversation_display.tag_bind(ai_label_tag, '<Enter>', lambda event: self.conversation_display.config(cursor="hand2"))
        self.conversation_display.tag_bind(ai_label_tag, '<Leave>', lambda event: self.conversation_display.config(cursor=""))

        self.conversation_display.insert(tk.END, message + "\n", full_message_tag)
        self.conversation_display.tag_bind(full_message_tag, '<Motion>', lambda event, text=message: self.show_translation_popup(event, "AI: " + text, full_message_tag))
        self.conversation_display.tag_bind(full_message_tag, '<Button-1>', lambda event, text=message: self.show_gemini_explanation_popup(event, "AI: " + text))

        self.conversation_display.config(state=tk.DISABLED)
        self.conversation_display.see(tk.END)

    def show_translation_popup(self, event, text, tag):
        if self.popup and self.popup.winfo_exists():
            self.popup.destroy()

        if "AI:" in text:

            text_to_translate, word_tag = self._get_hovered_word(event, text, tag) # Get the hovered word from a helper function
            if text_to_translate:
                phrase_to_translate = self._extract_phrase(text, text_to_translate) # Extract the phrase from text

                translation = translate_to_english(phrase_to_translate, self.loop, self.language, self.translation_language)

                if translation:
                    x = self.conversation_display.winfo_pointerx()
                    y = self.conversation_display.winfo_pointery()

                    self.popup = tk.Toplevel(self.root)
                    self.popup.wm_overrideredirect(True)
                    self.popup.geometry(f"+{x+10}+{y+10}")
                    popup_label = tk.Label(self.popup, text=translation, bg="white", relief=tk.SOLID, borderwidth=1)
                    popup_label.pack()

                    self.popup.bind("<Leave>", lambda event: self.hide_popup_after_delay(event))
                    self.conversation_display.tag_bind(word_tag, "<Leave>", lambda event: self.hide_popup_after_delay(event))

    def show_gemini_explanation_popup(self, event, text):
        if "AI:" in text:
            clicked_word, _ = self._get_hovered_word(event, text, None) # Get the clicked word
            if clicked_word:
                phrase = self._extract_phrase(text, clicked_word)
                if phrase:
                    self._fetch_and_display_gemini_explanation(phrase)

    def _fetch_and_display_gemini_explanation(self, phrase):
        popup = tk.Toplevel(self.root)
        popup.title("Gemini Explanation")

        frame = ttk.Frame(popup, padding="10")
        frame.pack(expand=True, fill="both")

        phrase_definition_label = ttk.Label(frame, text=f"Definition of '{phrase}':", font=("Helvetica", 10, "bold"))
        phrase_definition_label.pack(pady=(0, 5), anchor="w")
        phrase_definition_text = tk.Text(frame, wrap=tk.WORD, height=5, width=40)
        phrase_definition_text.pack(fill="x", pady=(0, 10))
        phrase_definition_text.config(state=tk.DISABLED)

        word_definitions_label = ttk.Label(frame, text="Word Definitions:", font=("Helvetica", 10, "bold"))
        word_definitions_label.pack(pady=(10, 5), anchor="w")
        word_definitions_area = scrolledtext.ScrolledText(frame, wrap=tk.WORD, height=10, width=40)
        word_definitions_area.pack(expand=True, fill="both")
        word_definitions_area.config(state=tk.DISABLED)

        async def get_definitions():
            try:
                response = await self.loop.run_in_executor(None, model.generate_content, f"Define the following sentence: '{phrase}' entirely in {self.translation_language} without {current_language}")
                phrase_def = response.text
            except Exception as e:
                phrase_def = f"Error fetching phrase definition: {e}"

            phrase_definition_text.config(state=tk.NORMAL)
            phrase_definition_text.delete(1.0, tk.END)
            phrase_definition_text.insert(tk.END, phrase_def)
            phrase_definition_text.config(state=tk.DISABLED)

            words = phrase.split()
            definitions_text = ""
            for word in words:
                try:
                    response = await self.loop.run_in_executor(None, model.generate_content, f"Give a quick definition of the word '{word}' entirely in {self.translation_language} without {current_language}")
                    definitions_text += f"{word}: {response.text}\n\n"
                except Exception as e:
                    definitions_text += f"Error fetching definition for '{word}': {e}\n\n"

            word_definitions_area.config(state=tk.NORMAL)
            word_definitions_area.delete(1.0, tk.END)
            word_definitions_area.insert(tk.END, definitions_text)
            word_definitions_area.config(state=tk.DISABLED)

        asyncio.run_coroutine_threadsafe(get_definitions(), self.loop)

    def _extract_phrase(self, text, word):
       """
        Helper function to extract the phrase containing the hovered word.
        """
       # Define phrase delimiters, such as periods, commas, colons, question marks, exclamation points.
       delimiters = r'[.,:;?!]'

       # Split the text by delimiters
       phrases = re.split(delimiters, text)

       # Find the start and the end of the phrase
       for phrase in phrases:
         if word in phrase:
            return phrase.strip()

       return ""  # return empty string if no phrase is found.

    def _get_hovered_word(self, event, text, tag):
        """
        Helper function to determine the word under the mouse cursor in the text widget.
        """

        x = event.x
        y = event.y

        #get the position of the mouse cursor in the text box and get the index
        index = self.conversation_display.index(f"@{x},{y}")

        #get the index of the start and end of the word
        start = self.conversation_display.index(f"{index} wordstart")
        end = self.conversation_display.index(f"{index} wordend")

        #get the word from the text box
        word = self.conversation_display.get(start, end)

        #create a new tag for the word
        word_tag = f"word_tag_{start}_{end}"

        if tag:
            #remove existing tag, and add a new tag to the word
            self.conversation_display.tag_remove(word_tag, "1.0", "end")
            self.conversation_display.tag_add(word_tag, start, end)

        return word, word_tag #return word and the tag

    def hide_popup_after_delay(self, event):
        self.root.after(200, self.hide_popup)

    def hide_popup(self):
        if self.popup and self.popup.winfo_exists():
            self.popup.destroy()

    def change_role(self, new_role):
        self.set_role(new_role, self.language)

    def change_language(self, new_language):
        global current_language, ai_greeting_sent
        ai_greeting_sent = False
        current_language = new_language
        self.language = new_language # Update the instance variable
        if new_language not in self.chat_displays:
            # Create new display if not available
             new_display = scrolledtext.ScrolledText(self.root, wrap=tk.WORD, width=80, height=20,
                                                                bg="#444444", fg="white",
                                                                font=font.Font(family="Helvetica", size=12))
             new_display.grid(row=0, column=0, columnspan=2, padx=10, pady=10)
             new_display.config(state=tk.DISABLED)
             self.chat_displays[new_language] = new_display

        self.conversation_display.grid_remove()
        self.conversation_display = self.chat_displays[new_language]
        self.conversation_display.grid(row=0, column=0, columnspan=2, padx=10, pady=10)
        self.set_role(self.role_var.get(), new_language)

    def go_back_to_language_selection(self):
        self.root.destroy()  # Close the main chat window
        self.show_language_selection()  # Reopen the language selection window

    def __del__(self):
        if hasattr(self, 'loop') and self.loop.is_running():
            pygame.mixer.quit() # Quit pygame mixer on exit
            self.loop.close()

    def show_complexity_level_popup(self):
        popup = tk.Toplevel(self.root)
        popup.title(translate_to_language("Select Complexity Level", self.loop, self.translation_language))
        popup.geometry("250x200") # Adjusted size
        popup.configure(bg="#333333")
        text_font = font.Font(family="Helvetica", size=12)
        style = ttk.Style()
        style.theme_use('clam')
        style.configure('TButton', font=text_font, background="#555555", foreground="white", relief='flat')
        style.map('TButton',
                      background=[('active', '#666666')],
                       foreground=[('active', 'white')])

        complexity_levels = ["Level 1", "Level 2", "Level 3"]
        for level in complexity_levels:
            level_button = ttk.Button(popup, text=level, command=lambda selected_level=level: self.set_complexity_level(selected_level, popup))
            level_button.pack(pady=5, padx=10)

    def set_complexity_level(self, level, popup_window):
        global current_complexity_level
        current_complexity_level = level
        self.complexity_level = level # Update instance variable
        self.ui_elements["current_complexity_level"] = f"Current Level: {level}" # Update UI element text
        self.create_settings_menu() # Recreate settings menu to update display
        self.translate_ui(self.translation_language) # Re-translate UI elements if needed
        popup_window.destroy()


class TranslationLanguageWindow:
    def __init__(self, root, on_translation_language_selected, loop):
        self.root = root
        self.loop = loop

         # UI Elements to Translate
        self.ui_elements = {
            "window_title": "Select Translation Language",
        }
        self.root.title(self.ui_elements["window_title"])
        self.root.geometry("250x180")  # Adjusted size

        self.on_translation_language_selected = on_translation_language_selected
        self.root.configure(bg="#333333")  # Dark grey background
        text_font = font.Font(family="Helvetica", size=12)  # Use a nicer font

        # Create a Style
        style = ttk.Style()
        style.theme_use('clam')  # Use the clam theme
        style.configure('TButton', font=text_font, background="#555555", foreground="white", relief='flat')
        style.map('TButton',
                  background=[('active', '#666666')],
                  foreground=[('active', 'white')])  # Set the color to change when hovered

        # Language Selection Buttons
        language_options = ["English", "Japanese", "Spanish", "French"]
        for lang in language_options:
            language_button = ttk.Button(root, text=lang,
                                        command=lambda selected_lang=lang: self.select_translation_language(
                                            selected_lang))
            language_button.pack(pady=5, padx=10) # Added padx for better spacing

    def select_translation_language(self, language):
        self.on_translation_language_selected(language, self.root)

class LanguageSelectionWindow:
    def __init__(self, root, on_language_selected, translation_language, complexity_level, loop):
        self.root = root
        self.loop = loop

         # UI Elements to Translate
        self.ui_elements = {
           "window_title": "Select Language"
        }
        self.root.title(translate_to_language(self.ui_elements["window_title"], self.loop, translation_language))
        self.root.geometry("250x180")  # Adjusted size

        self.on_language_selected = on_language_selected
        self.translation_language = translation_language
        self.complexity_level = complexity_level # Receive complexity level here
        self.root.configure(bg="#333333") # Dark grey background
        text_font = font.Font(family="Helvetica", size=12) # Use a nicer font

        # Create a Style
        style = ttk.Style()
        style.theme_use('clam')  # Use the clam theme
        style.configure('TButton', font=text_font, background="#555555", foreground="white", relief='flat')
        style.map('TButton',
                      background=[('active', '#666666')],
                       foreground=[('active', 'white')]) # Set the color to change when hovered

        # Language Selection Buttons
        language_options = ["English", "Japanese", "Spanish", "French"]
        for lang in language_options:
             language_button = ttk.Button(root, text=lang,
                                     command=lambda selected_lang=lang: self.select_language(selected_lang))
             language_button.pack(pady=5, padx=10) # Added padx for better spacing

    def select_language(self, language):
         self.on_language_selected(language, self.root, self.translation_language, self.complexity_level, self.loop)

class RoleSelectionWindow:
    def __init__(self, root, on_role_selected, language, translation_language, complexity_level, loop):
        self.root = root
        self.loop = loop

         # UI Elements to Translate
        self.ui_elements = {
           "window_title": "Select Role"
        }
        self.root.title(translate_to_language(self.ui_elements["window_title"], self.loop, translation_language))
        self.root.geometry("250x300")  # Adjusted size

        self.on_role_selected = on_role_selected
        self.language = language
        self.translation_language = translation_language
        self.complexity_level = complexity_level # Receive complexity level here
        self.root.configure(bg="#333333")
        text_font = font.Font(family="Helvetica", size=12)

        # Create a Style
        style = ttk.Style()
        style.theme_use('clam')
        style.configure('TButton', font=text_font, background="#555555", foreground="white", relief='flat')
        style.map('TButton',
                      background=[('active', '#666666')],
                       foreground=[('active', 'white')])

        # Buttons for selecting the roles
        for index, role_name in enumerate(roles.keys()):
                button = ttk.Button(root, text=role_name,
                                command=lambda role=role_name: self.select_role(role))
                button.pack(pady=5, padx=10) # Added padx for better spacing

    def select_role(self, role):
            self.on_role_selected(role, self.root, self.language, self.translation_language, self.complexity_level, self.loop)

class ComplexityLevelSelectionWindow: # New Complexity Level Selection Window
    def __init__(self, root, on_complexity_level_selected, translation_language, loop):
        self.root = root
        self.loop = loop

         # UI Elements to Translate
        self.ui_elements = {
           "window_title": "Select Complexity Level"
        }
        self.root.title(translate_to_language(self.ui_elements["window_title"], self.loop, translation_language))
        self.root.geometry("250x250")  # Adjusted size

        self.on_complexity_level_selected = on_complexity_level_selected
        self.translation_language = translation_language
        self.root.configure(bg="#333333")
        text_font = font.Font(family="Helvetica", size=12)

        # Create a Style
        style = ttk.Style()
        style.theme_use('clam')
        style.configure('TButton', font=text_font, background="#555555", foreground="white", relief='flat')
        style.map('TButton',
                      background=[('active', '#666666')],
                       foreground=[('active', 'white')])

        # Buttons for selecting complexity levels
        complexity_levels = ["Level 1", "Level 2", "Level 3"]
        for level in complexity_levels:
                button = ttk.Button(root, text=level,
                                command=lambda selected_level=level: self.select_complexity_level(selected_level))
                button.pack(pady=5, padx=10) # Added padx for better spacing

    def select_complexity_level(self, complexity_level):
            self.on_complexity_level_selected(complexity_level, self.root, self.translation_language, self.loop)


def on_complexity_level_selected(complexity_level, complexity_window_root, translation_language, loop, show_language_selection_callback=None): # Modified to accept callback
    complexity_window_root.destroy()
    lang_root = tk.Tk()
    lang_selection = LanguageSelectionWindow(lang_root, lambda lang, lang_window_root, translation_language=translation_language, complexity_level=complexity_level, loop=loop: on_language_selected(lang, lang_window_root, show_language_selection_callback, translation_language, complexity_level, loop), translation_language, complexity_level, loop) # Pass complexity level
    lang_root.mainloop()


def on_translation_language_selected(translation_language, translation_window_root, show_language_selection, loop):
    translation_window_root.destroy()
    complexity_root = tk.Tk()
    complexity_selection = ComplexityLevelSelectionWindow(complexity_root, lambda complexity_level, complexity_window_root, translation_language=translation_language, loop=loop: on_complexity_level_selected(complexity_level, complexity_window_root, translation_language, loop, show_language_selection), translation_language, loop) # Pass show_language_selection
    complexity_root.mainloop()


def on_language_selected(language, lang_window_root, show_language_selection, translation_language, complexity_level, loop):
        lang_window_root.destroy()
        role_root = tk.Tk()
        role_selection = RoleSelectionWindow(role_root, lambda role, role_window_root, language=language, translation_language=translation_language, complexity_level=complexity_level, loop=loop: on_role_selected(role, role_window_root, show_language_selection, language, translation_language, complexity_level, loop), language, translation_language, complexity_level, loop) # Pass complexity level
        role_root.mainloop()

def on_role_selected(role, role_window_root, show_language_selection, language, translation_language, complexity_level, loop):
    role_window_root.destroy()
    chat_root = tk.Tk()
    app = ChatApp(chat_root, show_language_selection, role, language, translation_language, complexity_level, loop) # Pass complexity level
    chat_root.mainloop()

# Main App Loop
if __name__ == "__main__":
    loop = asyncio.get_event_loop() # Create the event loop here

    def show_language_selection(loop=loop):
       trans_root = tk.Tk()
       trans_selection = TranslationLanguageWindow(trans_root, lambda trans_lang, trans_window_root, loop=loop: on_translation_language_selected(trans_lang, trans_window_root, show_language_selection, loop), loop)
       trans_root.mainloop()

    show_language_selection(loop)
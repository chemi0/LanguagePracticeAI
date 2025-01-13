import google.generativeai as genai
from googletrans import Translator
import os
from gtts import gTTS
import tkinter as tk
from tkinter import font, scrolledtext, ttk
import asyncio

# Configure Google Gemini API
genai.configure(api_key="AIzaSyAurbpVsBDTcNp7VxQ4b8DTBIWjq2_PekA")
model = genai.GenerativeModel("gemini-1.5-flash")

# Translator for Japanese to English
translator = Translator()

# Conversation histories for each role (dictionary)
conversation_histories = {}

# Default Language
DEFAULT_LANGUAGE = "English"

# Predefined roles and their corresponding prompts and initial greetings
roles = {
    "Boss": {
        "prompt": "I'm learning {language} and the best way is to learn is to have conversations in certain scenarios so lets pretend that you are my boss. Be direct and professional in your responses. Respond ONLY in {language}.",
        "greeting": "Good morning. Do you need anything?"
    },
    "Best Friend": {
        "prompt": "I'm learning {language} and the best way is to learn is to have conversations in certain scenarios so lets pretend that you are my best friend. Be casual and friendly in your responses. Respond ONLY in {language}.",
        "greeting": "Yo, how are you"
    },
    "Stranger": {
        "prompt": "I'm learning {language} and the best way is to learn is to have conversations in certain scenarios so lets pretend that you are a stranger. Respond neutrally but be polite. Respond ONLY in {language}.",
        "greeting": "Hello. Can I help you?"
    },
    "Mother": {
        "prompt": "I'm learning {language} and the best way is to learn is to have conversations in certain scenarios so lets pretend that you are my mother. Be caring and supportive in your responses. Respond ONLY in {language}.",
        "greeting": "Oh, how have you been?"
    },
    "Teacher": {
        "prompt": "I'm learning {language} and the best way is to learn is to have conversations in certain scenarios so lets pretend that you are my {language} teacher. Be educational and helpful. Respond ONLY in {language}.",
        "greeting": "Hello. What will you study today?"
    },
    "Drunk Friend": {
        "prompt": "I'm learning {language} and the best way is to learn is to have conversations in certain scenarios so lets pretend that you are my drunk friend. Be very silly and use slang. Respond ONLY in {language}.",
        "greeting": "Wow! How are you doing?"
    }
}

current_role = ""
last_ai_response = ""
ai_greeting_sent = False

# Function to translate to selected language (Synchronous version)
def translate_to_language(text, loop, language):
    try:
        dest_lang = 'en' #Default Language
        if language == "Japanese":
            dest_lang = 'ja'
        elif language == "Spanish":
            dest_lang = "es"
        elif language == "French":
            dest_lang = "fr"

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
def generate_response(input_text, current_role, language):
    global conversation_histories

    # Initialize conversation history for role if it doesn't exist
    if current_role not in conversation_histories:
        conversation_histories[current_role] = []
        
    conversation_history = conversation_histories[current_role] # Get role specific history

    # Update conversation history
    conversation_history.append(f"You: {input_text}")

    # Build the prompt with conversation history and role
    if current_role:
        prompt = roles[current_role]["prompt"].format(language=language) + "\n"
    else:
        prompt = ""
    prompt += "\n".join(conversation_history)

    try:
        response = model.generate_content(prompt)
        ai_response = response.text

        # Append AI response to conversation history
        conversation_history.append(f"AI: {ai_response}")

        # Limit conversation history to prevent excessive prompt length
        if len(conversation_history) > 20:
            conversation_history = conversation_history[-20:]
            
        conversation_histories[current_role] = conversation_history # Put back the role specific history

        return ai_response
    except Exception as e:
        return f"Error generating response: {str(e)}"


# Function to translate to English (Synchronous version)
def translate_to_english(text, loop, language):
    try:
        src_lang = 'en'
        if language == "Japanese":
            src_lang = 'ja'
        elif language == "Spanish":
            src_lang = "es"
        elif language == "French":
            src_lang = "fr"

        translation = translator.translate(text, src=src_lang, dest="en")

        if hasattr(translation, 'text'):
            return translation.text
        else: # Handle coroutine objects returned by googletrans
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

class ChatApp:
    def __init__(self, root, show_language_selection, initial_role, language):
        self.root = root
        self.root.title("Conversation Practice Bot")
        self.root.geometry("800x600")  # Set initial window size
        self.loop = asyncio.new_event_loop()  # Create the event loop once
        self.show_language_selection = show_language_selection
        self.language = language # The current language

        # Configure Dark Theme
        self.root.configure(bg="#333333") # Dark grey background
        text_font = font.Font(family="Helvetica", size=12) # Use a nicer font

        # Create a Style
        style = ttk.Style()
        style.theme_use('clam')  # Use the clam theme
        style.configure('TButton', font=text_font, background="#555555", foreground="white", relief='flat')
        style.map('TButton',
                      background=[('active', '#666666')],
                       foreground=[('active', 'white')]) # Set the color to change when hovered
        
        # Conversation Display
        self.conversation_display = scrolledtext.ScrolledText(root, wrap=tk.WORD, width=80, height=20,
                                            bg="#444444", fg="white", font=text_font)
        self.conversation_display.grid(row=0, column=0, columnspan=3, padx=10, pady=10)
        self.conversation_display.config(state=tk.DISABLED)

        # User Input
        self.input_box = tk.Entry(root, width=70, bg="#555555", fg="white", insertbackground="white", font=text_font)
        self.input_box.grid(row=1, column=0, padx=10, pady=5)

        # Send Button
        self.send_button = ttk.Button(root, text="Send", command=self.send_message)
        self.send_button.grid(row=1, column=1, padx=5, pady=5)

        # Explain Button
        self.explain_button = ttk.Button(root, text="Explain", command=self.explain_last_response)
        self.explain_button.grid(row=1, column=2, padx=5, pady=5)


        # Role Dropdown
        self.role_var = tk.StringVar(root)
        self.role_var.set(initial_role) #Initial role selection
        
        self.role_dropdown = ttk.OptionMenu(root, self.role_var, initial_role, *roles.keys(), command=self.change_role)
        self.role_dropdown.grid(row=2, column=0, columnspan=3, pady=5)


         # Back to Language Selection button
        back_button = ttk.Button(root, text="Change Language", command=self.go_back_to_language_selection)
        back_button.grid(row=3, column=0, columnspan=3, pady=10)

        # Call set_role to display greeting of the default role
        self.set_role(initial_role)

    def set_role(self, role):
        global current_role, ai_greeting_sent, last_ai_response

        current_role = role
        self.add_message(f"AI Role set to: {current_role}")
        
        if current_role and not ai_greeting_sent:
             greeting = roles[current_role]["greeting"]
             translated_greeting = translate_to_language(greeting, self.loop, self.language)
             self.add_message(f"AI: {translated_greeting}")
             conversation_histories[current_role] = [f"AI: {translated_greeting}"]
             last_ai_response = translated_greeting
             speak_response(translated_greeting, self.language)
             ai_greeting_sent = True
        else: # Role is changed
           if current_role in conversation_histories:
                self.clear_chat_display()
                for message in conversation_histories[current_role]:
                    self.add_message(message)
           else:
                self.clear_chat_display()
                greeting = roles[current_role]["greeting"]
                translated_greeting = translate_to_language(greeting, self.loop, self.language)
                self.add_message(f"AI: {translated_greeting}")
                conversation_histories[current_role] = [f"AI: {translated_greeting}"]
                last_ai_response = translated_greeting
                speak_response(translated_greeting, self.language)
               

    def clear_chat_display(self):
        self.conversation_display.config(state=tk.NORMAL)
        self.conversation_display.delete('1.0', tk.END)
        self.conversation_display.config(state=tk.DISABLED)
    
    def send_message(self):
        user_input = self.input_box.get().strip()
        if user_input:
            self.add_message(f"You: {user_input}")
            response = generate_response(user_input, current_role, self.language)
            self.add_message(f"AI: {response}")
            global last_ai_response
            last_ai_response = response
            speak_response(response, self.language)
            self.input_box.delete(0, tk.END)

    def add_message(self, message):
        self.conversation_display.config(state=tk.NORMAL)
        self.conversation_display.insert(tk.END, message + "\n")
        self.conversation_display.config(state=tk.DISABLED)
        self.conversation_display.see(tk.END)

    def explain_last_response(self):
        global last_ai_response
        if last_ai_response:
            translation = translate_to_english(last_ai_response, self.loop, self.language)
            self.add_message(f"English Translation: {translation}")
        else:
            self.add_message("There's no AI response to translate yet.")
    
    def change_role(self, new_role):
        self.set_role(new_role)
    
    def go_back_to_language_selection(self):
        self.root.destroy()  # Close the main chat window
        self.show_language_selection() #Reopen the language selection window

    def __del__(self):
        self.loop.close()


class LanguageSelectionWindow:
    def __init__(self, root, on_language_selected):
        self.root = root
        self.root.title("Select Language")
        self.root.geometry("300x200")  # Set the size for the language selection window

        self.on_language_selected = on_language_selected
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
             language_button.pack(pady=5)


    def select_language(self, language):
         self.on_language_selected(language, self.root)
         

class RoleSelectionWindow:
    def __init__(self, root, on_role_selected, language):
        self.root = root
        self.root.title("Select Role")
        self.root.geometry("300x200") # Set size for the role selection window

        self.on_role_selected = on_role_selected
        self.language = language
        self.root.configure(bg="#333333")
        text_font = font.Font(family="Helvetica", size=12)

        # Create a Style
        style = ttk.Style()
        style.theme_use('clam')
        style.configure('TButton', font=text_font, background="#555555", foreground="white", relief='flat')
        style.map('TButton',
                      background=[('active', '#666666')],
                       foreground=[('active', 'white')])
        
        for index, role_name in enumerate(roles.keys()):
                button = ttk.Button(root, text=role_name,
                                command=lambda role=role_name: self.select_role(role))
                button.pack(pady=5)

    def select_role(self, role):
            self.on_role_selected(role, self.root, self.language)

def on_language_selected(language, lang_window_root, show_language_selection):
        lang_window_root.destroy()
        role_root = tk.Tk()
        role_selection = RoleSelectionWindow(role_root, lambda role, role_window_root, language=language: on_role_selected(role, role_window_root, show_language_selection, language), language)
        role_root.mainloop()


def on_role_selected(role, role_window_root, show_language_selection, language):
    role_window_root.destroy()
    chat_root = tk.Tk()
    app = ChatApp(chat_root, show_language_selection, role, language)
    chat_root.mainloop()


# Main App Loop
if __name__ == "__main__":
    def show_language_selection():
        main_root = tk.Tk()
        lang_selection = LanguageSelectionWindow(main_root, lambda lang, lang_window_root: on_language_selected(lang, lang_window_root, show_language_selection))
        main_root.mainloop()

    show_language_selection()
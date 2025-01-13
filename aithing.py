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
DEFAULT_TRANSLATION_LANGUAGE = "English"

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
def translate_to_english(text, loop, language, translation_language):
    try:
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

        translation = translator.translate(text, src=src_lang, dest=dest_lang)

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
    def __init__(self, root, show_language_selection, initial_role, language, translation_language):
        self.root = root
        self.root.title("Conversation Practice Bot")
        self.root.geometry("800x600")  # Set initial window size
        self.loop = asyncio.new_event_loop()  # Create the event loop once
        self.show_language_selection = show_language_selection
        self.language = language # The current language
        self.translation_language = translation_language # The users translation language
        self.popup = None  # To store the popup window
        self.role_mapping = {} # Mapping of translated role to english role
        
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
        
         # UI Elements to Translate
        self.ui_elements = {
             "window_title": "Conversation Practice Bot",
             "send_button": "Send",
             "change_language_button": "Change Language",
             "settings_menu":"Settings"
        }
        
        # Conversation Display
        self.conversation_display = scrolledtext.ScrolledText(root, wrap=tk.WORD, width=80, height=20,
                                            bg="#444444", fg="white", font=text_font)
        self.conversation_display.grid(row=0, column=0, columnspan=3, padx=10, pady=10)
        self.conversation_display.config(state=tk.DISABLED)

        # User Input
        self.input_box = tk.Entry(root, width=70, bg="#555555", fg="white", insertbackground="white", font=text_font)
        self.input_box.grid(row=1, column=0, padx=10, pady=5)

        # Send Button
        self.send_button = ttk.Button(root, text=self.ui_elements["send_button"], command=self.send_message)
        self.send_button.grid(row=1, column=1, padx=5, pady=5)

        # Role Dropdown
        self.role_var = tk.StringVar(root)
        self.role_var.set(initial_role) #Initial role selection
        
        #Translate role options
        translated_roles = [translate_to_language(role, self.loop, translation_language) for role in roles.keys()]
        self.role_dropdown = ttk.OptionMenu(root, self.role_var, translated_roles[0], *translated_roles, command=self.change_role)
        self.role_dropdown.grid(row=2, column=0, columnspan=3, pady=5)


         # Back to Language Selection button
        self.back_button = ttk.Button(root, text=self.ui_elements["change_language_button"], command=self.go_back_to_language_selection)
        self.back_button.grid(row=3, column=0, columnspan=3, pady=10)
        
        # Translate the UI
        self.translate_ui(translation_language)
        
        #Update the values of the dropdown menu
        self.update_role_dropdown(translation_language)
        
        # Settings Menu
        self.create_settings_menu()

        # Call set_role to display greeting of the default role
        self.set_role(initial_role)
    
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


    def translate_ui(self, translation_language):
        self.root.title(translate_to_language(self.ui_elements["window_title"], self.loop, translation_language))
        self.send_button.config(text=translate_to_language(self.ui_elements["send_button"], self.loop, translation_language))
        self.back_button.config(text=translate_to_language(self.ui_elements["change_language_button"], self.loop, translation_language))
        
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
    
    def set_role(self, role):
        global current_role, ai_greeting_sent, last_ai_response

        if role in self.role_mapping: # If the selected role is the translated version, set the current role to the english version.
             current_role = self.role_mapping[role]
        else:
            current_role = role # If the selected role isn't translated use the english version.

        self.add_message(f"AI Role set to: {current_role}")
        
        if current_role and not ai_greeting_sent:
             greeting = roles[current_role]["greeting"]
             translated_greeting = translate_to_language(greeting, self.loop, self.language)
             tag = self.add_message(f"AI: {translated_greeting}")
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
                tag = self.add_message(f"AI: {translated_greeting}")
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
            tag = self.add_message(f"AI: {response}")
            global last_ai_response
            last_ai_response = response
            speak_response(response, self.language)
            self.input_box.delete(0, tk.END)

    def add_message(self, message):
        self.conversation_display.config(state=tk.NORMAL)
        tag = f"tag_{self.conversation_display.index(tk.END).replace('.', '_')}"
        self.conversation_display.insert(tk.END, message + "\n", tag)
        self.conversation_display.tag_bind(tag, '<Motion>', lambda event, text=message: self.show_translation_popup(event, text, tag))
        self.conversation_display.config(state=tk.DISABLED)
        self.conversation_display.see(tk.END)
        return tag
    
    def show_translation_popup(self, event, text, tag):
        
        if self.popup and self.popup.winfo_exists():
           self.popup.destroy()
        
        if "AI:" in text:
          
            text_to_translate = text[text.index("AI:")+4:]
            translation = translate_to_english(text_to_translate, self.loop, self.language, self.translation_language)

            if translation:
                x = self.conversation_display.winfo_pointerx()
                y = self.conversation_display.winfo_pointery()
                
                self.popup = tk.Toplevel(self.root)
                self.popup.wm_overrideredirect(True)
                self.popup.geometry(f"+{x+10}+{y+10}")
                popup_label = tk.Label(self.popup, text=translation, bg="white", relief=tk.SOLID, borderwidth=1)
                popup_label.pack()
               
                self.popup.bind("<Leave>", lambda event: self.hide_popup_after_delay(event)) #If the user moves off of the text, wait for 200ms and then close.
                self.conversation_display.tag_bind(tag, "<Leave>", lambda event: self.hide_popup_after_delay(event))#If the user moves off of the text, wait for 200ms and then close.
            
    def hide_popup_after_delay(self, event):
        self.root.after(200, self.hide_popup)

    def hide_popup(self):
        if self.popup and self.popup.winfo_exists():
            self.popup.destroy()
        
    
    def change_role(self, new_role):
        self.set_role(new_role)
    
    def go_back_to_language_selection(self):
        self.root.destroy()  # Close the main chat window
        self.show_language_selection() #Reopen the language selection window

    def __del__(self):
        self.loop.close()

class TranslationLanguageWindow:
    def __init__(self, root, on_translation_language_selected):
        self.root = root
        
         # UI Elements to Translate
        self.ui_elements = {
            "window_title": "Select Translation Language",
        }
        self.root.title(self.ui_elements["window_title"])
        self.root.geometry("300x200")  # Set the size for the language selection window

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
            language_button.pack(pady=5)
        
    def select_translation_language(self, language):
        self.on_translation_language_selected(language, self.root)


class LanguageSelectionWindow:
    def __init__(self, root, on_language_selected, translation_language):
        self.root = root
         # UI Elements to Translate
        self.ui_elements = {
           "window_title": "Select Language"
        }
        self.root.title(self.ui_elements["window_title"])
        self.root.geometry("300x200")  # Set the size for the language selection window

        self.on_language_selected = on_language_selected
        self.translation_language = translation_language
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
        
        # Translate the UI
        self.translate_ui(translation_language)
    
    def translate_ui(self, translation_language):
        self.root.title(translate_to_language(self.ui_elements["window_title"], self.loop, translation_language))

    def select_language(self, language):
         self.on_language_selected(language, self.root, self.translation_language)
         

class RoleSelectionWindow:
    def __init__(self, root, on_role_selected, language, translation_language):
        self.root = root
         # UI Elements to Translate
        self.ui_elements = {
           "window_title": "Select Role"
        }
        self.root.title(self.ui_elements["window_title"])
        self.root.geometry("300x200") # Set size for the role selection window

        self.on_role_selected = on_role_selected
        self.language = language
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
        
        # Buttons for selecting the roles
        for index, role_name in enumerate(roles.keys()):
                button = ttk.Button(root, text=role_name,
                                command=lambda role=role_name: self.select_role(role))
                button.pack(pady=5)
        
        # Translate the UI
        self.translate_ui(translation_language)
    
    def translate_ui(self, translation_language):
        self.root.title(translate_to_language(self.ui_elements["window_title"], self.loop, translation_language))


    def select_role(self, role):
            self.on_role_selected(role, self.root, self.language, self.translation_language)

def on_translation_language_selected(translation_language, translation_window_root, show_language_selection):
    translation_window_root.destroy()
    lang_root = tk.Tk()
    lang_selection = LanguageSelectionWindow(lang_root, lambda lang, lang_window_root, translation_language=translation_language: on_language_selected(lang, lang_window_root, show_language_selection, translation_language), translation_language)
    lang_root.mainloop()

def on_language_selected(language, lang_window_root, show_language_selection, translation_language):
        lang_window_root.destroy()
        role_root = tk.Tk()
        role_selection = RoleSelectionWindow(role_root, lambda role, role_window_root, language=language, translation_language=translation_language: on_role_selected(role, role_window_root, show_language_selection, language, translation_language), language, translation_language)
        role_root.mainloop()


def on_role_selected(role, role_window_root, show_language_selection, language, translation_language):
    role_window_root.destroy()
    chat_root = tk.Tk()
    app = ChatApp(chat_root, show_language_selection, role, language, translation_language)
    chat_root.mainloop()


# Main App Loop
if __name__ == "__main__":
    def show_language_selection():
       trans_root = tk.Tk()
       trans_selection = TranslationLanguageWindow(trans_root, lambda trans_lang, trans_window_root: on_translation_language_selected(trans_lang, trans_window_root, show_language_selection))
       trans_root.mainloop()

    show_language_selection()
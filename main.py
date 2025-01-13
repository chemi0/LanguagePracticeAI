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

# Conversation history to maintain context
conversation_history = []

# Predefined roles and their corresponding prompts and initial greetings
roles = {
    "Boss": {
        "prompt": "I'm learning japanese and the best way is to learn is to have conversations in certain scenarios so lets pretend that you are my boss. Be direct and professional in your responses. Respond ONLY in Japanese.",
        "greeting": "おはようございます。何かご用ですか？"
    },
    "Best Friend": {
        "prompt": "I'm learning japanese and the best way is to learn is to have conversations in certain scenarios so lets pretend that you are my best friend. Be casual and friendly in your responses. Respond ONLY in Japanese.",
        "greeting": "よお、元気か？"
    },
    "Stranger": {
        "prompt": "I'm learning japanese and the best way is to learn is to have conversations in certain scenarios so lets pretend that you are a stranger. Respond neutrally but be polite. Respond ONLY in Japanese.",
        "greeting": "こんにちは。何かお手伝いできますか？"
    },
    "Mother": {
        "prompt": "I'm learning japanese and the best way is to learn is to have conversations in certain scenarios so lets pretend that you are my mother. Be caring and supportive in your responses. Respond ONLY in Japanese.",
        "greeting": "あら、元気にしてた？"
    },
    "Teacher": {
        "prompt": "I'm learning japanese and the best way is to learn is to have conversations in certain scenarios so lets pretend that you are my Japanese teacher. Be educational and helpful. Respond ONLY in Japanese.",
        "greeting": "こんにちは。今日は何を勉強しますか？"
    },
    "Drunk Friend": {
        "prompt": "I'm learning japanese and the best way is to learn is to have conversations in certain scenarios so lets pretend that you are my drunk friend. Be very silly and use slang. Respond ONLY in Japanese.",
        "greeting": "うぇーい！調子はどうよ？"
    }
}

current_role = ""
last_ai_response = ""
ai_greeting_sent = False


# Function to generate conversation with Google Gemini
def generate_response(input_text, current_role=""):
    global conversation_history

    # Update conversation history
    conversation_history.append(f"You: {input_text}")

    # Build the prompt with conversation history and role
    if current_role:
        prompt = roles[current_role]["prompt"] + "\n"
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

        return ai_response
    except Exception as e:
        return f"Error generating response: {str(e)}"


# Function to translate Japanese to English (Synchronous version)
def translate_to_english(text, loop):
    try:
        translation = translator.translate(text, src="ja", dest="en")
        if hasattr(translation, 'text'):
            return translation.text
        else: # Handle coroutine objects returned by googletrans
           
           try:
               return loop.run_until_complete(translation).text
           except Exception as e:
               return f"Translation Error: {str(e)}"
    except Exception as e:
        return f"Translation Error: {str(e)}"


# Text-to-Speech for Japanese
def speak_japanese(text):
    tts = gTTS(text=text, lang='ja')
    tts.save("response.mp3")
    os.system("start response.mp3")

class ChatApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Japanese Conversation Practice Bot")
        self.root.geometry("800x600")  # Set initial window size
        self.loop = asyncio.new_event_loop()  # Create the event loop once

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

       # Role Selection Buttons
        self.role_frame = tk.Frame(root, bg="#333333") # Dark grey background for the frame
        self.role_frame.grid(row=2, column=0, columnspan=3, padx=10, pady=5)
        
        for index, role_name in enumerate(roles.keys()):
            button = ttk.Button(self.role_frame, text=role_name,
                                command=lambda role=role_name: self.set_role(role))
            button.grid(row=0, column=index, padx=5, pady=5)


    def set_role(self, role):
         global current_role, ai_greeting_sent, last_ai_response

         current_role = role
         self.add_message(f"AI Role set to: {current_role}")
         
         if current_role and not ai_greeting_sent:
             greeting = roles[current_role]["greeting"]
             self.add_message(f"AI: {greeting}")
             conversation_history.append(f"AI: {greeting}")
             last_ai_response = greeting
             ai_greeting_sent = True
     
    def send_message(self):
        user_input = self.input_box.get().strip()
        if user_input:
            self.add_message(f"You: {user_input}")
            response = generate_response(user_input, current_role)
            self.add_message(f"AI: {response}")
            global last_ai_response
            last_ai_response = response
            self.input_box.delete(0, tk.END)

    def add_message(self, message):
        self.conversation_display.config(state=tk.NORMAL)
        self.conversation_display.insert(tk.END, message + "\n")
        self.conversation_display.config(state=tk.DISABLED)
        self.conversation_display.see(tk.END)

    def explain_last_response(self):
        global last_ai_response
        if last_ai_response:
            translation = translate_to_english(last_ai_response, self.loop)
            self.add_message(f"English Translation: {translation}")
        else:
            self.add_message("There's no AI response to translate yet.")
        
    def __del__(self):
        self.loop.close()


# Main App Loop
if __name__ == "__main__":
    root = tk.Tk()
    app = ChatApp(root)
    root.mainloop()

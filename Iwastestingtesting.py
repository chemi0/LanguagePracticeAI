import google.generativeai as genai
import os
import tkinter as tk
from tkinter import font, scrolledtext, ttk
import asyncio
import re
import speech_recognition as sr
import threading
import time

# --- API Configuration ---
genai.configure(api_key="AIzaSyAurbpVsBDTcNp7VxQ4b8DTBIWjq2_PekA")  # Replace with your actual API key
model = genai.GenerativeModel("gemini-1.5-flash")

# --- Global Variables and Constants ---
CHAT_WINDOW_TITLE = "Voice Chat with Gemini"
BOT_NAME = "Gemini AI"
USER_NAME = "You"
RECORDING_TEXT = "Listening..."
IDLE_TEXT = "Click 'Speak' and start talking..."
SPEAK_BUTTON_TEXT = "Speak"
STOP_BUTTON_TEXT = "Stop Speaking"


# --- Function to Record Voice Input ---
def record_voice(text_area, status_label):
    r = sr.Recognizer()
    with sr.Microphone() as source:
        status_label.config(text=RECORDING_TEXT)
        r.adjust_for_ambient_noise(source)  # Adjust for noise
        audio = r.listen(source) # Listen for audio
        status_label.config(text=IDLE_TEXT) # Change back to idle text
        try:
            user_message = r.recognize_google(audio) # Recognize speech using Google Speech Recognition
            add_message(text_area, USER_NAME, user_message) # Add user message to chatbox
            process_message(text_area, user_message) # Send message to Gemini and get response
        except sr.UnknownValueError:
            add_message(text_area, BOT_NAME, "Could not understand audio")
        except sr.RequestError as e:
            add_message(text_area, BOT_NAME, f"Could not request results from Speech Recognition service; {e}")


# --- Function to Send Message to Gemini and Get Response ---
def process_message(text_area, user_message):
    try:
        response = model.generate_content(user_message) # Generate content from Gemini model
        bot_response = response.text
        add_message(text_area, BOT_NAME, bot_response) # Add bot's response to chatbox
    except Exception as e:
        add_message(text_area, BOT_NAME, f"Error communicating with Gemini: {e}")


# --- Function to Add Message to Chatbox UI ---
def add_message(text_area, sender, message):
    text_area.config(state=tk.NORMAL) # Enable text area for editing
    text_area.insert(tk.END, f"{sender}: {message}\n", sender) # Insert message with sender tag
    text_area.tag_config(USER_NAME, foreground="blue") # Configure tag for user messages
    text_area.tag_config(BOT_NAME, foreground="green") # Configure tag for bot messages
    text_area.config(state=tk.DISABLED) # Disable text area from user editing
    text_area.see(tk.END) # Scroll to the end of the text


# --- Function to Start Voice Recording in a Thread ---
def start_voice_input(text_area, status_label, speak_button, stop_button):
    speak_button.config(state=tk.DISABLED) # Disable Speak button during recording
    stop_button.config(state=tk.NORMAL) # Enable Stop button
    threading.Thread(target=record_voice, args=(text_area, status_label), daemon=True).start() # Start voice recording in new thread

# --- Function to Stop Voice Recording (Currently Placeholder - Could be improved for more control) ---
def stop_voice_input(speak_button, stop_button, status_label):
    speak_button.config(state=tk.NORMAL) # Re-enable Speak button
    stop_button.config(state=tk.DISABLED) # Disable Stop button
    status_label.config(text=IDLE_TEXT) # Reset status label
    # In a more advanced implementation, you would actually stop the recording thread gracefully here.
    # For this basic example, we rely on the speech recognition to naturally stop listening after a pause.


# --- Main Tkinter Window Setup ---
def main_window():
    window = tk.Tk()
    window.title(CHAT_WINDOW_TITLE)

    # --- Configure Grid Layout ---
    window.grid_rowconfigure(0, weight=1) # Text area expands vertically
    window.grid_columnconfigure(0, weight=1) # Text area expands horizontally

    # --- Font ---
    chat_font = font.Font(family="Helvetica", size=12)

    # --- Chat Text Area ---
    chat_text_area = scrolledtext.ScrolledText(window, wrap=tk.WORD, state=tk.DISABLED, font=chat_font) # Disabled by default, enabled only for adding text
    chat_text_area.grid(row=0, column=0, columnspan=2, sticky="nsew", padx=10, pady=10) # Span across columns, expand in all directions

    # --- Status Label ---
    status_label = ttk.Label(window, text=IDLE_TEXT)
    status_label.grid(row=1, column=0, columnspan=2, sticky="ew", padx=10) # Span across columns, expand horizontally, below text area

    # --- Speak Button ---
    speak_button = ttk.Button(window, text=SPEAK_BUTTON_TEXT, command=lambda: start_voice_input(chat_text_area, status_label, speak_button, stop_button))
    speak_button.grid(row=2, column=0, sticky="ew", padx=10, pady=(0, 10)) # Below status label, expand horizontally

    # --- Stop Button ---
    stop_button = ttk.Button(window, text=STOP_BUTTON_TEXT, command=lambda: stop_voice_input(speak_button, stop_button, status_label))
    stop_button.grid(row=2, column=1, sticky="ew", padx=10, pady=(0, 10)) # Beside Speak button, expand horizontally
    stop_button.config(state=tk.DISABLED) # Initially disabled

    window.mainloop()

if __name__ == "__main__":
    main_window()
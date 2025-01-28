import speech_recognition as sr
import tkinter as tk
from tkinter import scrolledtext
import threading

class VoiceToTextApp:
    def __init__(self, window):
        self.window = window
        self.window.title("Voice to Text")
        self.is_recording = False
        self.recognizer = sr.Recognizer()
        self.microphone = sr.Microphone()
        self.recorded_audio = None

        # Create widgets
        self.start_button = tk.Button(window, text="Start Recording", command=self.start_recording_func)
        self.start_button.pack(pady=10)

        self.stop_button = tk.Button(window, text="Stop Recording", command=self.stop_recording_func, state=tk.DISABLED)
        self.stop_button.pack(pady=10)

        self.text_box = scrolledtext.ScrolledText(window, wrap=tk.WORD)
        self.text_box.pack(expand=True, fill=tk.BOTH, padx=10, pady=10)
        self.text_box.config(state=tk.DISABLED) # Make it initially read-only

    def start_recording_func(self):
        if not self.is_recording:
            self.is_recording = True
            self.start_button.config(state=tk.DISABLED)
            self.stop_button.config(state=tk.NORMAL)
            self.text_box.config(state=tk.NORMAL) # Enable text box to clear and insert
            self.text_box.delete("1.0", tk.END) # Clear previous text
            threading.Thread(target=self._record_audio).start() # Run recording in a separate thread

    def _record_audio(self):
        try:
            with self.microphone as source:
                self.recognizer.adjust_for_ambient_noise(source) # Adjust for noise
                print("Recording...")
                audio = self.recognizer.listen(source) # Record audio
                self.recorded_audio = audio
                print("Finished Recording")
        except Exception as e:
            print(f"Error during recording: {e}")
            self.is_recording = False
            self.start_button.config(state=tk.NORMAL)
            self.stop_button.config(state=tk.DISABLED)
            self.text_box.config(state=tk.DISABLED) # Disable text box after error

    def stop_recording_func(self):
        if self.is_recording:
            self.is_recording = False
            self.start_button.config(state=tk.NORMAL)
            self.stop_button.config(state=tk.DISABLED)
            self.text_box.config(state=tk.NORMAL) # Enable text box to insert text
            threading.Thread(target=self._transcribe_audio).start() # Run transcription in a separate thread

    def _transcribe_audio(self):
        if self.recorded_audio:
            try:
                print("Transcribing...")
                text = self.recognizer.recognize_google(self.recorded_audio) # Use Google Web Speech API
                print("Transcription:", text)
                self.text_box.insert(tk.END, text) # Insert text in text box
            except sr.UnknownValueError:
                self.text_box.insert(tk.END, "Could not understand audio")
            except sr.RequestError as e:
                self.text_box.insert(tk.END, f"Could not request results; {e}")
            finally:
                self.text_box.config(state=tk.DISABLED) # Disable text box after inserting text
                self.recorded_audio = None # Clear recorded audio after transcription


if __name__ == "__main__":
    window = tk.Tk()
    app = VoiceToTextApp(window)
    window.mainloop()
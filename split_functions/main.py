# main.py
import tkinter as tk
import asyncio
from gui import ChatApp, LanguageSelectionWindow, RoleSelectionWindow, TranslationLanguageWindow
from translation_utils import translate_to_language

def on_translation_language_selected(translation_language, translation_window_root, show_language_selection, loop):
    translation_window_root.destroy()
    lang_root = tk.Tk()
    lang_selection = LanguageSelectionWindow(lang_root, lambda lang, lang_window_root, translation_language=translation_language, loop=loop: on_language_selected(lang, lang_window_root, show_language_selection, translation_language, loop), translation_language, loop)
    lang_root.mainloop()

def on_language_selected(language, lang_window_root, show_language_selection, translation_language, loop):
        lang_window_root.destroy()
        role_root = tk.Tk()
        role_selection = RoleSelectionWindow(role_root, lambda role, role_window_root, language=language, translation_language=translation_language, loop=loop: on_role_selected(role, role_window_root, show_language_selection, language, translation_language, loop), language, translation_language, loop)
        role_root.mainloop()

def on_role_selected(role, role_window_root, show_language_selection, language, translation_language, loop):
    role_window_root.destroy()
    chat_root = tk.Tk()
    app = ChatApp(chat_root, show_language_selection, role, language, translation_language, loop)
    chat_root.mainloop()

# Main App Loop
if __name__ == "__main__":
    loop = asyncio.get_event_loop() # Create the event loop here

    def show_language_selection(loop=loop):
       trans_root = tk.Tk()
       trans_selection = TranslationLanguageWindow(trans_root, lambda trans_lang, trans_window_root, loop=loop: on_translation_language_selected(trans_lang, trans_window_root, show_language_selection, loop), loop)
       trans_root.mainloop()

    show_language_selection(loop)
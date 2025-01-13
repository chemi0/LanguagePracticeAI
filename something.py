import google.generativeai as genai
from googletrans import Translator
import os
from gtts import gTTS
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
        "prompt": "You are my boss. Be direct and professional in your responses. Respond ONLY in Japanese.",
        "greeting": "おはようございます。何かご用ですか？"
    },
    "Best Friend": {
        "prompt": "You are my best friend. Be casual and friendly in your responses. Respond ONLY in Japanese.",
        "greeting": "よお、元気か？"
    },
    "Stranger": {
        "prompt": "You are a stranger. Respond neutrally but be polite. Respond ONLY in Japanese.",
        "greeting": "こんにちは。何かお手伝いできますか？"
    },
    "Mother": {
        "prompt": "You are my mother. Be caring and supportive in your responses. Respond ONLY in Japanese.",
        "greeting": "あら、元気にしてた？"
    },
    "Teacher": {
        "prompt": "You are my Japanese teacher. Be educational and helpful. Respond ONLY in Japanese.",
        "greeting": "こんにちは。今日は何を勉強しますか？"
    },
    "Drunk Friend": {
        "prompt": "You are my drunk friend. Be very silly and use slang. Respond ONLY in Japanese.",
        "greeting": "うぇーい！調子はどうよ？"
    }
}

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


# Function to translate Japanese to English
async def translate_to_english(text):
    try:
        translation = await translator.translate(text, src="ja", dest="en")
        return translation.text
    except Exception as e:
        return f"Translation Error: {str(e)}"


# Text-to-Speech for Japanese
def speak_japanese(text):
    tts = gTTS(text=text, lang='ja')
    tts.save("response.mp3")
    os.system("start response.mp3")


# Terminal-based chatbot
async def main():
    print("Welcome to the Japanese Conversation Practice Bot!")
    print("Choose a role for the AI by typing 'role' followed by the role you want (e.g., 'role Boss').")
    print("Available roles:", ", ".join(roles.keys()))
    print("Type your message in Japanese, or type 'explain' to translate the last AI response")
    print("Type 'exit' to quit the chat.")

    current_role = ""
    ai_greeting_sent = False
    last_ai_response = ""

    while True:
        user_input = input("You: ").strip()

        if user_input.lower() == "exit":
            print("Goodbye!")
            break
        elif user_input.lower().startswith("role"):
            try:
                new_role = user_input[len("role "):].strip()
                if new_role in roles:
                    current_role = new_role
                    print(f"AI role set to: {current_role}")
                    # Send initial greeting
                    greeting = roles[current_role]["greeting"]
                    print(f"AI: {greeting}")
                    conversation_history.append(f"AI: {greeting}")
                    last_ai_response = greeting
                    ai_greeting_sent = True
                else:
                    print(f"Invalid Role, please choose one of: {', '.join(roles.keys())}")
            except Exception as e:
                print(f"Error setting role, please try again")
        elif user_input.lower() == "explain":
            if last_ai_response:
                translation = await translate_to_english(last_ai_response)
                print(f"English Translation: {translation}")
            else:
                print("There's no AI response to translate yet.")
        else:
            # Generate AI response
            response = generate_response(user_input, current_role)
            print(f"{response}")
            last_ai_response = response
            ai_greeting_sent = False

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(main())
    finally:
        tasks = asyncio.all_tasks(loop)
        for task in tasks:
            if not task.done():
                task.cancel()
                try:
                  loop.run_until_complete(task)
                except asyncio.CancelledError:
                  pass
        loop.close()
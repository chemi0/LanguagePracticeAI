import google.generativeai as genai

# Configure Google Gemini API (API key should ideally be handled more securely, e.g., environment variables)
genai.configure(api_key="AIzaSyAurbpVsBDTcNp7VxQ4b8DTBIWjq2_PekA") # **Important:** Consider securing your API key!
model = genai.GenerativeModel("gemini-1.5-flash")

conversation_histories = {} # Conversation histories moved here as it's related to Gemini interactions

# Function to generate conversation with Google Gemini
def generate_response(input_text, current_role, language):
    # Initialize conversation history for language and role if it doesn't exist
    if (language, current_role) not in conversation_histories:
        conversation_histories[(language, current_role)] = []

    conversation_history = conversation_histories[(language, current_role)]

    # Update conversation history
    conversation_history.append(f"You: {input_text}")

    # Get roles dictionary - assuming roles are defined globally, if not, you'll need to pass it.
    from main import roles # Import roles from main.py - adjust if roles are moved elsewhere
    prompt = roles[current_role]["prompt"].format(language=language) + "\n" if current_role else ""
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
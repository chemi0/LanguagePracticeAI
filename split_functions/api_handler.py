# api_handler.py
# Functions for interacting with the Gemini API
from config import model, roles, conversation_histories

# Function to generate conversation with Google Gemini
def generate_response(input_text, current_role, language):
    # Initialize conversation history for language and role if it doesn't exist
    if (language, current_role) not in conversation_histories:
        conversation_histories[(language, current_role)] = []

    conversation_history = conversation_histories[(language, current_role)]

    # Update conversation history
    conversation_history.append(f"You: {input_text}")

    # Build the prompt with conversation history and role
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
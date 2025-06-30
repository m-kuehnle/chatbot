import streamlit as st
from google import genai
from google.genai import types

# Show title and description.
st.title("🧠 Kompana - Mental Health Support")
st.write(
    "Kompana is a compassionate AI mental health support companion powered by Google's Gemini model. "
    "I'm here to provide emotional support, coping strategies, and a safe space to talk about your feelings. "
    "Please note: I'm not a replacement for professional therapy, but I'm here to listen and help. "
    "If you're experiencing a crisis, please contact emergency services or a mental health hotline."
)

# Load the Gemini API key from Streamlit Cloud Secrets.
gemini_api_key = st.secrets.get("general", {}).get("gemini_api_key")
if not gemini_api_key:
    # Fallback: Ask the user to enter the API key manually.
    gemini_api_key = st.text_input("Enter your Gemini API Key", type="password")
    if not gemini_api_key:
        st.error("Gemini API key is missing. Please provide it to continue.", icon="❌")

if gemini_api_key:
    # Create a Gemini client.
    client = genai.Client(api_key=gemini_api_key)

    # Create a session state variable to store the chat messages. This ensures that the
    # messages persist across reruns.
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Display the existing chat messages via `st.chat_message`.
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Create a chat input field to allow the user to enter a message. This will display
    # automatically at the bottom of the page.
    if prompt := st.chat_input("How are you feeling today? I'm here to listen..."):

        # Store and display the current prompt.
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # Create a system prompt for mental health support
        system_prompt = """You are Kompana, a compassionate and empathetic mental health support AI therapist. Your role is to:

1. Provide emotional support and validation
2. Listen actively and respond with empathy
3. Offer practical coping strategies and techniques
4. Help users identify their feelings and thoughts
5. Encourage self-care and healthy habits
6. Be non-judgmental and supportive
7. Remind users that you're not a replacement for professional therapy when appropriate
8. If someone mentions self-harm or crisis, gently encourage them to seek immediate professional help

Always respond with warmth, understanding, and professionalism. Keep responses supportive but not overly clinical."""

        # Prepare messages for the API call
        api_messages = [{"role": "user", "content": system_prompt}]
        for msg in st.session_state.messages:
            api_messages.append({"role": msg["role"], "content": msg["content"]})

        # Generate a response using the Gemini API.
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=[msg["content"] for msg in api_messages],
            config=types.GenerateContentConfig(
                thinking_config=types.ThinkingConfig(thinking_budget=0)  # Disables thinking
            ),
        )

        # Extract and display the relevant text from the response.
        assistant_response = response.candidates[0].content.parts[0].text
        with st.chat_message("assistant"):
            st.markdown(assistant_response)
        st.session_state.messages.append({"role": "assistant", "content": assistant_response})

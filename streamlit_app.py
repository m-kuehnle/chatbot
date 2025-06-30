import streamlit as st
from google import genai
from google.genai import types

# Show title and description.
st.title("💬 Chatbot")
st.write(
    "This is a simple chatbot that uses Google's Gemini model to generate responses. "
    "To use this app, you need to provide a Gemini API key. "
    "You can also learn how to build this app step by step by [following our tutorial](https://docs.streamlit.io/develop/tutorials/llms/build-conversational-apps)."
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
    if prompt := st.chat_input("What is up?"):

        # Store and display the current prompt.
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # Generate a response using the Gemini API.
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config=types.GenerateContentConfig(
                thinking_config=types.ThinkingConfig(thinking_budget=0)  # Disables thinking
            ),
        )

        # Extract and display the relevant text from the response.
        assistant_response = response.candidates[0].content.parts[0].text
        with st.chat_message("assistant"):
            st.markdown(assistant_response)
        st.session_state.messages.append({"role": "assistant", "content": assistant_response})
   
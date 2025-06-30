import streamlit as st
from google import genai
from google.genai import types

# 🔒---------------  Configuration  ---------------🔒
HOTLINE_NOTICE = (
    "**⚠️ It sounds like you may be feeling unsafe right now.**\n\n"
    "You matter, and you don’t have to face these feelings alone. "
    "Please call the free, confidential crisis hotline **+49 293 283843** right away, "
    "or reach out to a trusted mental-health professional or therapist. "
    "If you think you might act on these thoughts, please call **112** "
    "or go to the nearest hospital."
)

def extract_flag(gemini_reply: str) -> tuple[bool, str]:
    """
    Parse Gemini's first line for 'EMERGENCY: true|false' (case-insensitive).
    Returns (is_emergency, remaining_text_without_flag).
    If the flag is missing, assume non-emergency and return the full text.
    """
    first_line, _, rest = gemini_reply.partition("\n")
    if first_line.lower().startswith("emergency:"):
        is_emergency = first_line.strip().lower().endswith("true")
        return is_emergency, rest.lstrip("\n")
    # Fallback: model forgot the flag
    return False, gemini_reply

# 🪧---------------  UI  ---------------🪧
st.title("Kompana – Your Mental-Health Support")
st.write(
    "Kompana is a compassionate AI mental-health companion powered by Google Gemini. "
    "I'm here to provide emotional support and coping strategies. "
    "**Important:** I'm not a replacement for professional therapy. If you’re in crisis, "
    "please contact emergency services or a mental-health hotline."
)

# 🔑---------------  API key handling  ---------------🔑
gemini_api_key = st.secrets.get("general", {}).get("gemini_api_key")
if not gemini_api_key:
    gemini_api_key = st.text_input("Enter your Gemini API key", type="password")
    if not gemini_api_key:
        st.error("Gemini API key is missing. Please provide it to continue.", icon="❌")

if gemini_api_key:
    client = genai.Client(api_key=gemini_api_key)

    # Persistent chat history
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Render historical messages
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # 📝---------------  User input  ---------------📝
    if user_msg := st.chat_input("How are you feeling today? I'm here to listen…"):
        # Show user message
        st.session_state.messages.append({"role": "user", "content": user_msg})
        with st.chat_message("user"):
            st.markdown(user_msg)

        # 🧠---------------  Gemini call ---------------🧠
        system_prompt = """
You are Kompana, a compassionate AI mental-health companion.

**FORMAT INSTRUCTION (mandatory):**
Always start your reply with a single line exactly:
EMERGENCY: true
or
EMERGENCY: false
indicating whether the user appears to be in immediate danger of self-harm.
After that line, leave one blank line and continue your empathetic response.

Guidelines:
• Provide emotional support and validation.
• Listen actively and respond with empathy.
• Offer practical coping strategies.
• Encourage self-care and professional help when appropriate.
• If you output `EMERGENCY: true`, your response MUST begin (after the blank line) with brief, direct advice to seek immediate help – users should contact emergency services or a crisis hotline (+49 293 283843).
"""
        api_messages = [{"role": "user", "content": system_prompt}]
        for m in st.session_state.messages:
            api_messages.append({"role": m["role"], "content": m["content"]})

        raw_reply = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=[m["content"] for m in api_messages],
            config=types.GenerateContentConfig(
                thinking_config=types.ThinkingConfig(thinking_budget=0)
            ),
        ).candidates[0].content.parts[0].text

        # 🔍 Parse flag & strip it from display
        is_emergency, assistant_text = extract_flag(raw_reply)

        # 🚨 Optional emergency banner (never shows the flag)
        if is_emergency:
            with st.chat_message("assistant"):
                st.markdown(HOTLINE_NOTICE)
            st.session_state.messages.append(
                {"role": "assistant", "content": HOTLINE_NOTICE}
            )

        # Show Gemini's main reply (flag removed)
        with st.chat_message("assistant"):
            st.markdown(assistant_text)
        st.session_state.messages.append(
            {"role": "assistant", "content": assistant_text}
        )
import streamlit as st
from google import genai
from google.genai import types
from streamlit_image_select import image_select  # pip install streamlit-image-select

# --- Persona definitions (unchanged) ---
PERSONAS = {
    "Mike B. Rother": {
        "image": "images/person1.png",
        "prompt": """
Persona: **Mike B. Rother**
Target group: Young men aged 16–25  
Communication style: Casual, direct, masculine-coded  
Focus: Anger, emotional withdrawal, performance pressure, masculinity  
Therapeutic tone: Low-threshold entry, validates vulnerability without patronizing.
Use everyday language, short sentences, and a friendly “bro-like” vibe. Avoid jargon.
""",
    },
    "Enbi Rae": {
        "image": "images/person2.png",
        "prompt": """
Persona: **Enbi Rae**
Target group: LGBTQ+ youth & young adults  
Communication style: Inclusive, trauma-informed, affirming  
Focus: Identity, exclusion, dysfunctional family dynamics  
Therapeutic tone: Creates a space where users feel seen and supported without judgment.
Use gender-neutral language and validate lived experiences.
""",
    },
    "Mona L. Davencook": {
        "image": "images/person4.png",
        "prompt": """
Persona: **Mona L. Davencook**
Target group: Academically-inclined or emotionally reserved individuals  
Communication style: Analytical, calm, structured  
Focus: Cognitive clarity, overthinking, decision-making, psycho-education  
Therapeutic tone: Reflective and intellectualized rather than emotive.
Offer frameworks, summaries, and gentle Socratic questions.
""",
    },
    "Dr. Fù": {
        "image": "images/person3.png",
        "prompt": """
Persona: **Dr. Fù**
Target group: Users needing emotional security or attachment support  
Communication style: Warm, nurturing, motherly, slow-paced  
Focus: Grief, emotional overwhelm, self-compassion  
Therapeutic tone: Gentle, grounding, with imagination & body-awareness techniques.
Speak softly, with reassuring metaphors and pauses.
""",
    },
}

HOTLINE_NOTICE = (
    "**⚠️ It sounds like you may be feeling unsafe right now.**\n\n"
    "You matter, and you don’t have to face these feelings alone. "
    "Please call the free, confidential crisis hotline **+49 293 283843** right away, "
    "or reach out to a trusted mental-health professional or therapist. "
    "If you think you might act on these thoughts, please call **112** "
    "or go to the nearest hospital."
)

def extract_flag(reply: str) -> tuple[bool, str]:
    first, _, rest = reply.partition("\n")
    if first.lower().startswith("emergency:"):
        return first.strip().lower().endswith("true"), rest.lstrip("\n")
    return False, reply

# --- Page setup ---
st.set_page_config(page_title="Kompana", page_icon="🧠")
st.title("Kompana – Your Mental-Health Support")

# Persona selector (persist in session_state)
if "persona" not in st.session_state:
    st.session_state.persona = None
if "messages" not in st.session_state:
    st.session_state.messages = []

# --- Persona Picker (ONE-TIME only, with images as buttons) ---
if st.session_state.persona is None:
    images = [meta["image"] for meta in PERSONAS.values()]
    captions = list(PERSONAS.keys())
    image_to_persona = {meta["image"]: name for name, meta in PERSONAS.items()}

    
    choice = image_select(
        label="Choose your Kompana persona:",
        images=images,
        captions=captions,
        use_container_width=True,
        index=0,
    )
    
    if choice:
        
        # Image paths are returned by image_select, so use our mapping
        if choice in image_to_persona:
            st.session_state.persona = image_to_persona[choice]
        else:
            # Fallback
            st.session_state.persona = captions[0]
            st.write(f"Falling back to default: {st.session_state.persona}")
                
        st.session_state.messages = []  # Reset chat
        st.write(f"Selected persona: {st.session_state.persona}")
        st.stop()  # Prevent further execution

# --- After selection: show only current persona & chat UI ---
st.markdown(f"### Current persona: **{st.session_state.persona}**")

st.write(
    "Kompana is a compassionate AI mental-health companion powered by Google Gemini. "
    "I'm here to provide emotional support, coping strategies, and a safe space to talk. "
    "**Important:** I'm not a replacement for professional therapy. "
    "If you’re in crisis, please contact emergency services or a mental-health hotline."
)

# --- Chat & Gemini logic ---
gemini_api_key = st.secrets.get("general", {}).get("gemini_api_key") or st.text_input(
    "Enter your Gemini API key", type="password"
)
if not gemini_api_key:
    st.error("Gemini API key is missing. Please provide it to continue.", icon="❌")
    st.stop()

client = genai.Client(api_key=gemini_api_key)

# Render history
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# User input
if user_msg := st.chat_input("How are you feeling today? I'm here to listen…"):
    st.session_state.messages.append({"role": "user", "content": user_msg})
    with st.chat_message("user"):
        st.markdown(user_msg)

    # Build system prompt
    persona_prompt = PERSONAS[st.session_state.persona]["prompt"]  # Use persona name
    system_prompt = f"""
You are Kompana, an AI mental-health companion adopting the following persona:

{persona_prompt}

**CRISIS format:**  
Start with `EMERGENCY: true` or `EMERGENCY: false`, then a blank line, then your response.
If `EMERGENCY: true`, your next line MUST advise calling +49 293 283843 or 112 immediately.
"""
    api_msgs = [{"role": "user", "content": system_prompt}] + st.session_state.messages

    raw = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=[m["content"] for m in api_msgs],
        config=types.GenerateContentConfig(
            thinking_config=types.ThinkingConfig(thinking_budget=0)
        ),
    ).candidates[0].content.parts[0].text

    is_emerg, assistant_txt = extract_flag(raw)

    if is_emerg:
        with st.chat_message("assistant"):
            st.markdown(HOTLINE_NOTICE)
        st.session_state.messages.append({"role": "assistant", "content": HOTLINE_NOTICE})

    with st.chat_message("assistant"):
        st.markdown(assistant_txt)
    st.session_state.messages.append({"role": "assistant", "content": assistant_txt})
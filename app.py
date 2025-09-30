import streamlit as st
import google.generativeai as genai
import os
import re

# --- PAGE CONFIGURATION ---
st.set_page_config(
    page_title="Spiritual Navigator",
    page_icon="🧘",
    layout="centered"
)

# --- THEME & STYLING ---
def load_custom_css():
    st.markdown("""
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Lato:wght@400;700&display=swap');
            :root {
                --primary-color: #4A909A;
                --background-color: #F0F2F6;
                --secondary-background-color: #FFFFFF;
                --text-color: #31333F;
                --font: 'Lato', sans-serif;
            }
            .stApp, .stApp h1, .stApp h2, .stApp h3, .stApp p, .stApp li, .stApp label, .stApp .stMarkdown {
                color: var(--text-color) !important;
            }
            body, .stApp { background-color: var(--background-color); }
            h1, h2, h3 { font-family: var(--font); }
            .st-emotion-cache-1r6slb0, .st-emotion-cache-p5msec, .lineage-card { 
                border-radius: 10px; padding: 1.5rem; background-color: var(--secondary-background-color); 
                box-shadow: 0 4px 8px rgba(0,0,0,0.08); margin-bottom: 1.5rem;
            }
        </style>
    """, unsafe_allow_html=True)

# --- API CONFIGURATION ---
try:
    api_key = st.secrets["GOOGLE_API_KEY"]
    genai.configure(api_key=api_key)
except (KeyError, FileNotFoundError):
    st.error("API key not found. Please add your GOOGLE_API_KEY to your Streamlit secrets.")
    st.stop()

# --- SYSTEM INSTRUCTION (THE "GEM" PROMPT) ---
# --- MODIFIED: Dialogue is now more fluid ---
system_instruction = """
You are a 'Spiritual Navigator AI'. Your purpose is to facilitate a deep and personal contemplative journey.

**Persona & Method:**
- You will act as a wise, compassionate guide inspired by the chosen master's teachings, without directly mimicking them.
- You MUST adopt the spirit and method of the chosen lineage for the dialogue.

**Dialogue Flow:**
- Your dialogue should be a fluid, guided conversation.
- Ask one clear, contemplative question per turn.
- Listen to the user's response and tailor your next question to guide them deeper.
- After a natural progression of inquiry (typically 4-6 turns), you must guide the conversation towards a conclusion by shifting from questioning to action.
- Your final message must present a simple, practical contemplative exercise based on the conversation, followed by a brief, encouraging thought. Start this final message with the keyword "CONCLUSION:".

**Formatting Rules:**
- When asked for lineages, provide a markdown list where each item is a bolded heading, a colon, and a one-sentence summary.
- When asked to choose a master, respond with ONLY the master's name.
"""

# --- HELPER FUNCTIONS ---
def call_gemini(prompt, is_chat=False, history=None):
    try:
        model = genai.GenerativeModel(model_name='gemini-2.5-flash', system_instruction=system_instruction)
        if is_chat:
            chat = model.start_chat(history=history or [])
            response = chat.send_message(prompt)
            return response.text
        else:
            response = model.generate_content(prompt)
            return response.text
    except Exception as e:
        st.error(f"An error occurred with the API call: {e}")
        return None

def parse_lineage_summaries(text):
    if not text: return {}
    pattern = re.compile(r"\*\*(.*?)\*\*\s*:\s*(.*)", re.MULTILINE)
    matches = pattern.findall(text)
    return {match[0]: match[1] for match in matches}

# --- SESSION STATE INITIALIZATION ---
if 'stage' not in st.session_state:
    st.session_state.stage = "start"

def restart_app():
    for key in list(st.session_state.keys()): del st.session_state[key]
    st.session_state.stage = "start"

# --- MAIN APP UI ---
st.title("🧘 Spiritual Navigator")
load_custom_css()

if st.session_state.stage == "start":
    st.caption("A guided journey into the heart of your experience.")
    st.session_state.vritti = st.text_area("To begin, what emotion, tendency, or situation are you exploring?", key="vritti_input", height=100)
    
    if st.button("Begin Exploration"):
        if st.session_state.vritti:
            st.session_state.stage = "choose_lineage"
            st.rerun()
        else:
            st.warning("Please describe what you are exploring to begin.")

elif st.session_state.stage == "choose_lineage":
    st.subheader(f"Pathways for: {st.session_state.vritti.capitalize()}")
    if 'lineages' not in st.session_state:
        with st.spinner("Finding relevant spiritual paths..."):
            prompt = f"For a user exploring '{st.session_state.vritti}', provide a markdown list of different spiritual lineages. For each, use the lineage name as a bold heading followed by a colon and a one-sentence summary of its approach."
            response = call_gemini(prompt)
            st.session_state.raw_response = response
            
            if not response or not parse_lineage_summaries(response):
                st.info("The first search was inconclusive. Trying a broader approach...")
                prompt = f"List spiritual traditions that discuss '{st.session_state.vritti}'. For each, use the tradition name as a bold heading followed by a colon and a one-sentence summary."
                response = call_gemini(prompt)
                st.session_state.raw_response = response
            
            if response:
                st.session_state.lineages = parse_lineage_summaries(response)

    if not st.session_state.get('lineages'):
        st.warning("Could not find any specific paths for this topic. Please try a different query.")
        with st.expander("Show Raw AI Response (for debugging)"):
            st.code(st.session_state.get('raw_response', "No response from AI."))
    else:
        st.write("Choose the approach that resonates with you most:")
        for lineage, summary in st.session_state.lineages.items():
            with st.container():
                st.markdown(f"<div class='lineage-card'>", unsafe_allow_html=True)
                st.subheader(lineage)
                st.write(summary)
                if st.button(f"Explore this Path", key=f"lineage_{lineage}"):
                    st.session_state.chosen_lineage = lineage
                    st.session_state.stage = "dialogue"
                    st.rerun()
                st.markdown("</div>", unsafe_allow_html=True)
    st.divider()
    if st.button("Start Over"):
        restart_app()
        st.rerun()

elif st.session_state.stage == "dialogue":
    if 'dialogue_started' not in st.session_state:
        with st.spinner("Preparing your guide..."):
            master_prompt = f"For the lineage '{st.session_state.chosen_lineage}' and the query '{st.session_state.vritti}', choose the single most appropriate master to inspire the upcoming dialogue. Respond with ONLY the master's name."
            master_name = call_gemini(master_prompt)
            
            if master_name:
                st.session_state.chosen_master = master_name.strip()
                st.session_state.messages = [
                    { "role": "user", "parts": [f"I am a seeker exploring '{st.session_state.vritti}'. I have chosen the path of '{st.session_state.chosen_lineage}'. As a guide inspired by the teachings of {st.session_state.chosen_master}, please begin our contemplative dialogue by asking me your first question."] }
                ]
                first_question = call_gemini(st.session_state.messages[-1]['parts'][0], is_chat=True, history=[])
                if first_question:
                    st.session_state.messages.append({"role": "model", "parts": [first_question]})
                    st.session_state.dialogue_started = True
            else:
                st.error("Could not select a guide. Please try again.")
                st.session_state.stage = "choose_lineage"
    
    if st.session_state.get('dialogue_started'):
        st.info(f"You are in a contemplative dialogue inspired by the **{st.session_state.chosen_lineage}** tradition.")
        
        for message in st.session_state.get('messages', []):
            if "I am a seeker exploring" not in message["parts"][0]:
                with st.chat_message(message["role"]):
                    st.markdown(message["parts"][0])

        if prompt := st.chat_input("Write your reflections here..."):
            st.session_state.messages.append({"role": "user", "parts": [prompt]})
            with st.spinner("..."):
                history_for_api = [{"role": m["role"], "parts": m["parts"]} for m in st.session_state.messages]
                next_question = call_gemini(prompt, is_chat=True, history=history_for_api)
                if next_question:
                    if next_question.strip().startswith("CONCLUSION:"):
                        st.session_state.final_summary = next_question.replace("CONCLUSION:", "").strip()
                        st.session_state.stage = "final_summary"
                        st.rerun()
                    else:
                        st.session_state.messages.append({"role": "model", "parts": [next_question]})
            st.rerun()

    st.divider()
    if st.button("End Session & Start Over"):
        restart_app()
        st.rerun()

elif st.session_state.stage == "final_summary":
    st.subheader("A Concluding Contemplation")
    if st.session_state.get('final_summary'):
        st.markdown(st.session_state.final_summary)
    else:
        st.warning("The dialogue has ended.")
    st.divider()
    if st.button("Begin a New Journey"):
        restart_app()
        st.rerun()
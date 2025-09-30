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
system_instruction = """
You are a 'Spiritual Navigator AI'. Your purpose is to guide a user through a contemplative journey.
When asked for lineages, provide a markdown-formatted list. Each item must have the lineage name as a bold heading, followed by a brief, one-sentence summary of its approach to the user's query.
When asked to choose a master, identify the single most appropriate master from that lineage to guide the user on their specific query. Respond with ONLY the master's name (e.g., "Ramana Maharshi").
When you adopt the persona of a master for a guided dialogue, you must ask a series of 6-8 contemplative questions. Each question should build on the user's previous response, guiding them deeper into self-inquiry using the specific style and techniques of that master. Your final message should be a concluding thought or blessing.
"""

# --- HELPER FUNCTIONS ---
def call_gemini(prompt, is_chat=False, history=None):
    try:
        model = genai.GenerativeModel(model_name='gemini-1.5-flash', system_instruction=system_instruction)
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
    # Regex to find a bolded heading and the text that follows until the next heading
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
            prompt = f"For a user exploring '{st.session_state.vritti}', provide a markdown list of 5 different spiritual lineages. For each, use the lineage name as a bold heading followed by a colon and a one-sentence summary of its approach."
            response = call_gemini(prompt)
            if response:
                st.session_state.lineages = parse_lineage_summaries(response)

    if not st.session_state.get('lineages'):
        st.warning("Could not find any specific paths for this topic. Please try another query.")
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
    if 'chosen_master' not in st.session_state:
        with st.spinner("Preparing your guide..."):
            prompt = f"For the lineage '{st.session_state.chosen_lineage}' and the query '{st.session_state.vritti}', choose the single most appropriate master to guide the user. Respond with ONLY the master's name."
            master_name = call_gemini(prompt)
            if master_name:
                st.session_state.chosen_master = master_name.strip()
                # Initialize the conversation
                st.session_state.messages = [
                    { "role": "user", "parts": [f"I am struggling with '{st.session_state.vritti}'. As {st.session_state.chosen_master} from the {st.session_state.chosen_lineage} tradition, please begin guiding me with your first question."] }
                ]
                # Get the first question from the AI
                first_question = call_gemini(st.session_state.messages[-1]['parts'][0], is_chat=True, history=[])
                if first_question:
                    st.session_state.messages.append({"role": "model", "parts": [first_question]})
            else:
                st.error("Could not select a guide. Please try again.")
                st.session_state.stage = "choose_lineage" # Go back if failed
    
    if st.session_state.get('chosen_master'):
        st.info(f"You are now in a contemplative dialogue guided by the style of **{st.session_state.chosen_master}**.")
        
        # Display chat messages
        for message in st.session_state.get('messages', []):
            # Don't show the initial system prompt to the user
            if "I am struggling with" not in message["parts"][0]:
                with st.chat_message(message["role"]):
                    st.markdown(message["parts"][0])

        # Get user input
        if prompt := st.chat_input("Write your reflections here..."):
            # Add user message and get AI response
            st.session_state.messages.append({"role": "user", "parts": [prompt]})
            with st.spinner("..."):
                # Pass the conversation history to the model
                history_for_api = [{"role": m["role"], "parts": m["parts"]} for m in st.session_state.messages]
                next_question = call_gemini(prompt, is_chat=True, history=history_for_api)
                if next_question:
                    st.session_state.messages.append({"role": "model", "parts": [next_question]})
            st.rerun()

    st.divider()
    if st.button("End Session & Start Over"):
        restart_app()
        st.rerun()
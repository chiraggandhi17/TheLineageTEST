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
            .stTabs [data-baseweb="tab"][aria-selected="true"] {
                background-color: transparent;
                color: var(--primary-color);
                border-bottom: 2px solid var(--primary-color);
            }
            .stButton>button { 
                border-radius: 20px; 
                border: 1px solid var(--primary-color); 
                color: var(--primary-color); 
                background-color: var(--secondary-background-color);
                transition: all 0.3s ease-in-out; 
                padding: 5px 15px; 
            }
            .stButton>button:hover { 
                color: var(--secondary-background-color); 
                background-color: var(--primary-color); 
            }
            .st-emotion-cache-1r6slb0, .st-emotion-cache-p5msec, .quote-container, .lineage-card { 
                border-radius: 10px; padding: 1.5rem; background-color: var(--secondary-background-color); 
                box-shadow: 0 4px 8px rgba(0,0,0,0.08); margin-bottom: 1.5rem;
            }
            .quote-text {
                font-size: 1.2rem;
                font-style: italic;
                text-align: center;
                margin-bottom: 1rem;
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

# --- GUIDING PRINCIPLES QUIZ QUESTIONS ---
QUESTIONS = [
    {
        "question": "When you have a free weekend, you are more likely to:",
        "options": [
            "Plan an activity or a project to accomplish something.",
            "Relax, read, and reflect with minimal plans.",
            "Spend quality time connecting with friends or family.",
            "Spontaneously decide what to do in the moment."
        ],
        "key": "q1"
    },
    {
        "question": "When making an important life decision, you rely more on:",
        "options": [
            "A thorough analysis of pros and cons.",
            "Your gut feeling or strong intuition.",
            "Advice from trusted mentors or family.",
            "What has practically worked for you in the past."
        ],
        "key": "q2"
    },
    {
        "question": "After a long and draining week, you recharge by:",
        "options": [
            "Spending quiet time alone.",
            "Being with a close group of supportive people.",
            "Losing yourself in a creative or engaging activity.",
            "Learning something new, like watching a documentary."
        ],
        "key": "q3"
    },
    {
        "question": "Which statement best describes your approach to life?",
        "options": [
            "I thrive with a consistent routine and a clear plan.",
            "I prefer to embrace change and adapt as I go.",
            "I seek a balance between a stable foundation and new experiences.",
            "I am guided by a deep sense of purpose or a mission."
        ],
        "key": "q4"
    },
    {
        "question": "What tends to capture your attention more?",
        "options": [
            "The underlying meaning and 'why' behind things.",
            "The practical details and 'how' to get things done.",
            "The emotional tone and feeling of a situation.",
            "The potential for future possibilities and innovations."
        ],
        "key": "q5"
    }
]

# --- SYSTEM INSTRUCTION (THE "GEM" PROMPT) ---
system_instruction = """
You are the 'Spiritual Navigator', a specialized AI guide. 
When asked for anonymous teachings, provide a numbered list of 5 brief, one-or-two sentence summaries. Do NOT name the master or tradition.
When asked to identify lineages for a teaching, provide a numbered list of ONLY the lineage names.
When asked for a list of masters for a SINGLE lineage, respond with a numbered list. For each master, provide their name, time period, and a key associated location, separated by '|'.
When providing detailed teachings, structure it with clear markdown headings: "### Core Philosophical Concepts", "### The Prescribed Method or Practice", and "### Reference to Key Texts".
"""

# --- HELPER FUNCTIONS ---
def call_gemini(prompt):
    try:
        model = genai.GenerativeModel(model_name='gemini-2.5-pro')
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        st.error(f"An error occurred with the API call: {e}")
        return None

def parse_anonymous_teachings(text):
    if not text: return []
    return re.findall(r'^\s*\d+\.\s*(.+)$', text, re.MULTILINE)

def parse_lineage_list(text):
    if not text: return []
    return re.findall(r'^\s*\d+\.\s*(.+)$', text, re.MULTILINE)

def parse_masters_list(text):
    if not text: return []
    masters_list = []
    pattern = re.compile(r"^\s*\d+\.\s*(.+?)\s*\|\s*(.+?)\s*\|\s*(.+)$", re.MULTILINE)
    matches = pattern.findall(text)
    for match in matches:
        masters_list.append({
            "name": match[0].strip(),
            "period": match[1].strip(),
            "location": match[2].strip()
        })
    return masters_list

def parse_teachings(text):
    if not text: return {}
    sections = {}
    parts = re.split(r'###\s*(Core Philosophical Concepts|The Prescribed Method or Practice|Reference to Key Texts)', text)
    if len(parts) > 1:
        for i in range(1, len(parts), 2):
            heading, content = parts[i].strip(), parts[i+1].strip()
            if "Concepts" in heading: sections["concepts"] = content
            elif "Method" in heading: sections["method"] = content
            elif "Texts" in heading: sections["texts"] = content
    return sections

# --- SESSION STATE INITIALIZATION ---
if 'stage' not in st.session_state:
    st.session_state.stage = "start"

def restart_app():
    for key in list(st.session_state.keys()): del st.session_state[key]
    st.session_state.stage = "start"

# --- MAIN APP UI ---
st.image("logo.png", use_container_width=True) 
st.markdown("<h1 style='text-align: center;'>🧘 Spiritual Navigator</h1>", unsafe_allow_html=True)
load_custom_css()

if st.session_state.stage == "start":
    st.markdown("<marquee>An interactive guide to ancient wisdom on modern emotions.</marquee>", unsafe_allow_html=True)
    user_question_input = st.text_area("Describe the emotion, situation, or question you are exploring:", key="question_input", height=100)
    
    st.write("---")
    st.subheader("Optional: Share your Guiding Principles")
    answers = {}
    for q in QUESTIONS:
        answers[q['key']] = st.radio(q['question'], q['options'], key=q['key'], index=None)

    if st.button("Begin Exploration"):
        if user_question_input:
            with st.spinner("Understanding your query..."):
                summary = [answers[q['key']] for q in QUESTIONS if answers[q['key']]]
                principles_summary = " ".join(summary)
                
                understanding_prompt = f"A user has submitted the following query: '{user_question_input}'. Analyze this to identify the single core emotion, psychological block, or 'vritti' they are facing. Respond with ONLY the name of that core issue (e.g., 'Anger', 'Fear of Failure')."
                core_vritti = call_gemini(understanding_prompt)

                if core_vritti:
                    restart_app()
                    st.session_state.vritti = core_vritti.strip()
                    st.session_state.principles_summary = principles_summary
                    st.session_state.stage = "show_anonymous_teachings"
                    st.rerun()
                else:
                    st.error("Could not understand the core issue. Please try rephrasing.")
        else:
            st.warning("Please describe the emotion or question you are exploring.")

elif st.session_state.stage == "show_anonymous_teachings":
    st.info(f"Based on your query, we are exploring teachings related to **{st.session_state.vritti}**.")
    if 'teachings' not in st.session_state:
        with st.spinner("Finding teachings that resonate with you..."):
            prompt = f"Based on a user exploring '{st.session_state.vritti}' and whose guiding principles are '{st.session_state.principles_summary}', provide 5 brief, anonymous teaching summaries from different spiritual traditions."
            response = call_gemini(prompt)
            if response:
                st.session_state.teachings = parse_anonymous_teachings(response)
    if not st.session_state.get('teachings'):
        st.warning("Could not find specific teachings. Please try again.")
    else:
        st.write("Choose the teaching that resonates with you most:")
        for i, teaching in enumerate(st.session_state.teachings):
            if st.button(teaching, key=f"teaching_{i}", use_container_width=True):
                st.session_state.chosen_teaching = teaching
                st.session_state.stage = "show_lineage_list"
                st.rerun()
    st.divider()
    if st.button("Start Over"):
        restart_app()
        st.rerun()

elif st.session_state.stage == "show_lineage_list":
    st.info(f"You chose: \"{st.session_state.chosen_teaching}\"")
    if 'lineage_list' not in st.session_state:
        with st.spinner("Identifying associated traditions..."):
            prompt = f"The teaching '{st.session_state.chosen_teaching}' is about '{st.session_state.vritti}'. Provide a numbered list of ONLY the names of the associated spiritual lineages."
            response = call_gemini(prompt)
            if response:
                st.session_state.lineage_list = parse_lineage_list(response)
    
    st.write("Choose a lineage to explore further:")
    for i, lineage in enumerate(st.session_state.get('lineage_list', [])):
        if st.button(lineage, key=f"lineage_list_{i}", use_container_width=True):
            st.session_state.chosen_lineage = lineage
            st.session_state.stage = "show_masters"
            st.rerun()
    st.divider()
    if st.button("Back to Teachings"):
        st.session_state.stage = "show_anonymous_teachings"
        keys_to_clear = ['lineage_list', 'chosen_teaching']
        for key in keys_to_clear:
            if key in st.session_state: del st.session_state[key]
        st.rerun()

elif st.session_state.stage == "show_masters":
    st.header(st.session_state.chosen_lineage)
    if 'masters_list' not in st.session_state:
        with st.spinner(f"Finding masters from the {st.session_state.chosen_lineage} lineage..."):
            prompt = f"For the lineage '{st.session_state.chosen_lineage}', provide a numbered list of key masters who spoke on '{st.session_state.vritti}'. For each, include their name, time period, and a key associated location, separated by '|'."
            response = call_gemini(prompt)
            st.session_state.raw_response = response
            if response:
                st.session_state.masters_list = parse_masters_list(response)
    
    if not st.session_state.get('masters_list'):
        st.warning("Could not parse the list of masters from the AI's response.")
        with st.expander("Show Raw AI Response (for debugging)"):
            st.code(st.session_state.get('raw_response', "No response from AI."))
    else:
        st.write("Choose a master to learn more:")
        for i, master in enumerate(st.session_state.get('masters_list', [])):
            with st.container():
                st.markdown(f"**{master['name']}**")
                st.caption(f"{master.get('period', 'Unknown')} | {master.get('location', 'Unknown')}")
                if st.button("Explore Teachings", key=f"master_{i}"):
                    st.session_state.chosen_master = master['name']
                    st.session_state.stage = "show_final_teachings"
                    st.rerun()
                st.markdown("---")
    if st.button("Back to Lineage List"):
        st.session_state.stage = "show_lineage_list"
        keys_to_clear = ['masters_list', 'chosen_lineage', 'raw_response']
        for key in keys_to_clear:
            if key in st.session_state: del st.session_state[key]
        st.rerun()

elif st.session_state.stage == "show_final_teachings":
    st.subheader(f"Teachings of {st.session_state.chosen_master}")
    st.caption(f"From the **{st.session_state.chosen_lineage}** perspective on **{st.session_state.vritti}**.")
    if 'final_teachings' not in st.session_state:
        with st.spinner("Distilling the wisdom..."):
            prompt = f"What were {st.session_state.chosen_master}'s core teachings regarding {st.session_state.vritti}? Structure the response with the markdown headings: '### Core Philosophical Concepts', '### The Prescribed Method or Practice', and '### Reference to Key Texts'."
            response = call_gemini(prompt)
            if response:
                st.session_state.final_teachings = parse_teachings(response)
    
    if st.session_state.get('final_teachings'):
        tab1, tab2, tab3 = st.tabs(["**Core Concepts**", "**The Method**", "**Key Texts**"])
        with tab1: st.markdown(st.session_state.final_teachings.get("concepts", "No information provided."))
        with tab2: st.markdown(st.session_state.final_teachings.get("method", "No information provided."))
        with tab3: st.markdown(st.session_state.final_teachings.get("texts", "No information provided."))
    
    st.divider()
        st.subheader("Discover More & Contemplate")
        disc_tabs = st.tabs(["📚 Further Reading", "📍 Places to Visit", "🗓️ Annual Events", "🙏 Practice & Music"])

        with disc_tabs[0]:
            if 'books' not in st.session_state:
                with st.spinner("Finding relevant books..."):
                    prompt = f"Suggest 2-3 books for understanding {st.session_state.chosen_master}'s core teachings. Respond with a markdown table with columns: Book, Description, and Link (to search on Amazon.in)."
                    response = call_gemini(prompt)
                    st.session_state.books = response or "None"
            if "None" in st.session_state.books.strip():
                st.info("No specific book recommendations were found.")
            else:
                st.markdown(st.session_state.books)
        
        with disc_tabs[1]:
            if 'places' not in st.session_state:
                with st.spinner("Locating significant places..."):
                    prompt = f"Is there a significant place to visit associated with {st.session_state.chosen_master}? Respond with a markdown table with columns: Place, Description, and Location. If none, respond 'None'."
                    response = call_gemini(prompt)
                    st.session_state.places = response or "None"
            if "None" in st.session_state.places.strip():
                st.info(f"No specific places are associated with {st.session_state.chosen_master}.")
            else:
                st.markdown(st.session_state.places)

        with disc_tabs[2]:
            if 'events' not in st.session_state:
                with st.spinner("Checking for annual events..."):
                    prompt = f"Are there special annual events or festivals associated with {st.session_state.chosen_master}? Respond with a markdown table: Event, Description, 'Time of Year'. If none, respond 'None'."
                    response = call_gemini(prompt)
                    st.session_state.events = response or "None"
            if "None" in st.session_state.events.strip():
                st.info(f"No specific annual events are associated with {st.session_state.chosen_master}.")
            else:
                st.markdown(st.session_state.events)
        
        with disc_tabs[3]:
            st.info("A practice to deepen your understanding.")
            if 'practice_text' not in st.session_state:
                with st.spinner("Generating a relevant practice..."):
                    prompt = f"Based on the teachings of {st.session_state.chosen_master}, generate a short, guided contemplative practice. If a relevant bhajan or chant is associated, add a '### Suggested Listening' section with a YouTube search link."
                    response = call_gemini(prompt)
                    st.session_state.practice_text = response or "No practice could be generated."
            st.markdown(st.session_state.practice_text)
            st.text_area("Your Contemplation Journal:", height=150, key="journal_entry", help="Entries are for this session only.")
    
    st.divider()
    col1, col2 = st.columns(2)
    with col1:
        if st.button("⬅️ Back to Masters List", use_container_width=True):
            st.session_state.stage = "show_masters"
            if 'final_teachings' in st.session_state: del st.session_state['final_teachings']
            st.rerun()
    with col2:
        if st.button("Start Over restarting", use_container_width=True):
            restart_app()
            st.rerun()
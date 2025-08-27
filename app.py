import streamlit as st
from langchain_core.prompts import PromptTemplate
from langchain_huggingface import HuggingFacePipeline

from transformers import AutoTokenizer, AutoModelForSeq2SeqLM, pipeline
import json, re, random
from datetime import datetime

# Use stronger model
MODEL_NAME = "google/flan-t5-large"
EXIT_KEYWORDS = {"exit", "quit", "bye", "stop", "end"}

st.set_page_config(page_title="TalentScout Hiring Assistant", page_icon="🤖", layout="wide")

@st.cache_resource(show_spinner=False)
def load_llm():
    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
    model = AutoModelForSeq2SeqLM.from_pretrained(MODEL_NAME)
    pipe = pipeline(
        "text2text-generation",
        model=model,
        tokenizer=tokenizer,
        max_length=512,
        device=-1   # 👈 Force CPU
    )
    return HuggingFacePipeline(pipeline=pipe)

llm = load_llm()

# Question prompt (now flexible)
question_prompt = PromptTemplate(
    input_variables=["tech", "yoe", "num_qs"],
    template=(
        "Generate exactly {num_qs} concise technical interview questions for a candidate "
        "with {yoe} years of experience in {tech}.\n\n"
        "- Each question must be under 25 words.\n"
        "- Number the questions 1 to {num_qs}.\n"
        "- Only output questions, no explanations."
    )
)

# Info prompts
info_prompts = {
    "full_name": "May I have your full name, please?",
    "email": "What is your email address?",
    "phone": "Can you share your phone number?",
    "years_experience": "How many years of professional experience do you have?",
    "desired_positions": "Which position(s) are you applying for?",
    "current_location": "Where are you currently located (city and country)?",
    "tech_stack": "Please list the programming languages, frameworks, databases, and tools you are proficient in (comma-separated)."
}

# Session state
if "messages" not in st.session_state:
    st.session_state.messages = []
if "candidate" not in st.session_state:
    st.session_state.candidate = {
        "full_name": None, "email": None, "phone": None, "years_experience": None,
        "desired_positions": None, "current_location": None, "tech_stack": None, "questions": {}
    }
if "phase" not in st.session_state: 
    st.session_state.phase = "greet"
if "ended" not in st.session_state: 
    st.session_state.ended = False

def add_message(role, text):
    st.session_state.messages.append({"role": role, "content": text})
    with st.chat_message(role): 
        st.markdown(text)

def save_transcript():
    data = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "candidate": st.session_state.candidate,
        "messages": st.session_state.messages
    }
    fname = f"transcript_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"
    with open(fname, "w", encoding="utf-8") as f: 
        json.dump(data, f, indent=2)
    return fname

def pending_fields():
    return [f for f, v in st.session_state.candidate.items() if v in (None, "") and f != "questions"]

# Sidebar – live candidate info
with st.sidebar:
    st.header("📋 Candidate Info")
    cand = st.session_state.get("candidate", {})
    for key, val in cand.items():
        if key != "questions":
            st.write(f"**{key.replace('_',' ').title()}:** {val if val else '⏳ Pending'}")

    if st.session_state.get("ended", False):
        st.subheader("✅ Interview Completed")
        transcript = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "candidate": cand,
            "messages": st.session_state.messages
        }
        st.download_button(
            label="⬇️ Download Transcript (JSON)",
            data=json.dumps(transcript, indent=2),
            file_name=f"transcript_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json",
            mime="application/json"
        )

# Greeting
if st.session_state.phase == "greet" and not st.session_state.messages:
    add_message("assistant", "Hello! I’m TalentScout’s Hiring Assistant 🤖. Let’s get started. You can type 'exit' anytime to finish.")
    st.session_state.phase = "collect"

# Render history
for m in st.session_state.messages:
    with st.chat_message(m["role"]): 
        st.markdown(m["content"])

# Input
if not st.session_state.ended: 
    user_text = st.chat_input("Type your response...")
else: 
    user_text = None

if user_text:
    add_message("user", user_text)

    # Exit check
    if any(k in user_text.lower() for k in EXIT_KEYWORDS):
        add_message("assistant", "Thanks for your time! We’ll review your info and contact you soon. Goodbye!")
        st.session_state.ended = True
        save_transcript()

    else:
        cand = st.session_state.candidate
        handled = False  # track if input was understood

        # --- Field extraction heuristics ---
        if cand["full_name"] is None and ("name" in user_text.lower() or "i am" in user_text.lower()):
            match = re.search(r"(?:my name is|i am|i'm)\s+(.+)", user_text, re.IGNORECASE)
            cand["full_name"] = match.group(1).strip() if match else user_text.strip()
            handled = True

        elif cand["email"] is None and "@" in user_text:
            cand["email"] = user_text.strip()
            handled = True

        elif cand["phone"] is None and re.search(r"\d{10}", user_text):
            cand["phone"] = re.search(r"\d{10}", user_text).group(0)
            handled = True

        elif cand["years_experience"] is None and re.search(r"\d+", user_text):
            cand["years_experience"] = re.search(r"\d+", user_text).group(0)
            handled = True

        elif cand["desired_positions"] is None and any(x in user_text.lower() for x in ["engineer","developer","manager"]):
            cand["desired_positions"] = user_text.strip()
            handled = True

        elif cand["current_location"] is None and any(x in user_text.lower() for x in ["city","country","from"]):
            cand["current_location"] = user_text.strip()
            handled = True

        elif cand["tech_stack"] is None and ("," in user_text or any(x in user_text.lower() for x in ["python","java","c++","javascript"])):
            cand["tech_stack"] = user_text.strip()
            handled = True

        # --- Move conversation forward ---
        missing = pending_fields()
        if missing:
            field = missing[0]
            add_message("assistant", info_prompts[field])

        elif st.session_state.phase != "ask":
            st.session_state.phase = "ask"
            techs = [t.strip() for t in cand["tech_stack"].split(",")]
            yoe = cand["years_experience"] or "some"

            for tech in techs[:5]:
                num_qs = random.choice([3,4,5])  # 👈 random 3–5 questions
                chain = question_prompt | llm
                qs = chain.invoke({"tech": tech, "yoe": yoe, "num_qs": num_qs})

                # --- Post-process ---
                lines = [l.strip() for l in qs.split("\n") if l.strip()]
                cleaned = []
                for line in lines:
                    question = re.sub(r"^\d+[\).]\s*", "", line)
                    if "?" in question:
                        cleaned.append(question.strip())

                # --- Fallbacks ---
                fallback_questions = [
                    f"What are key features of {tech}?",
                    f"Explain a common use case of {tech}.",
                    f"What are advantages and limitations of {tech}?",
                    f"Describe a problem you solved using {tech}.",
                    f"What best practices should be followed in {tech}?"
                ]

                while len(cleaned) < num_qs:
                    cleaned.append(fallback_questions[len(cleaned)])

                formatted = "\n".join([f"{i+1}. {q}" for i, q in enumerate(cleaned[:num_qs])])
                cand["questions"][tech] = formatted

            # Display results
            add_message("assistant", "Great! Let’s go through some technical questions:")
            for tech, qs in cand["questions"].items():
                add_message("assistant", f"**{tech}**\n{qs}")
            add_message("assistant", "That’s all from my side. Thank you!")
            st.session_state.ended = True
            save_transcript()

        # --- Fallback for irrelevant input ---
        elif not handled:
            add_message("assistant", "Sorry, I didn’t quite understand that. Could you rephrase?")

# 🤖 TalentScout Hiring Assistant

An AI-powered **interview chatbot** built with **Streamlit** and **LangChain**.  
It interacts with candidates, collects their details, and generates **technical interview questions** based on their declared tech stack.

---

## 🚀 Features

- **Clean UI (Streamlit)** with chat interface & sidebar summary
- **Greeting & Exit**: Welcomes candidates, exits on keywords (`exit`, `quit`, `bye`, `stop`, `end`)
- **Information Gathering**:
  - Full Name
  - Email Address
  - Phone Number
  - Years of Experience
  - Desired Position(s)
  - Current Location
  - Tech Stack (languages, frameworks, databases, tools)
- **Dynamic Tech Question Generation**:
  - Generates **3–5 technical questions** per technology
  - Tailored to candidate’s years of experience
  - Always ensures 3–5 questions with fallback logic
- **Context Handling**: Maintains chat history across the conversation
- **Fallback Mechanism**:
  - If user input is unclear → politely asks them to rephrase
  - If model generates fewer questions → fills with professional fallback questions
- **End Conversation**: Gracefully thanks the candidate & allows downloading transcript

---

## 🛠️ Tech Stack

- [Python 3.9+](https://www.python.org/)
- [Streamlit](https://streamlit.io/) – UI framework
- [LangChain](https://www.langchain.com/) – LLM orchestration
- [HuggingFace Transformers](https://huggingface.co/docs/transformers) – model inference
- Model: [google/flan-t5-large](https://huggingface.co/google/flan-t5-large)

---

## 📦 Installation

Clone this repo and set up environment:

```bash
git clone https://github.com/your-username/talentscout-assistant.git
cd talentscout-assistant

# Create virtual environment
python -m venv venv
source venv/bin/activate   # On Linux/Mac
venv\Scripts\activate      # On Windows

# Install dependencies
pip install -r requirements.txt

## ▶️ Usage

Run the Streamlit app:
streamlit run app.py

The app will launch at:
Local URL: http://localhost:8501


## 📂 Project Structure
.
├── app.py            # Main Streamlit chatbot app
├── requirements.txt  # Dependencies
├── README.md         # Project documentation
└── transcripts/      # (Optional) Saved interview transcripts

## ✅ Future Improvements

Experience-level specific questions (junior vs senior)
Export transcript as PDF/Word
Add Gradio UI option

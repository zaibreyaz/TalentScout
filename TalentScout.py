import streamlit as st
from langchain_community.llms import Ollama
import json

class Chatbot:
    def __init__(self):
        """Initialize the chatbot with the Ollama model and conversation history."""
        self.llm = Ollama(model="llama3.2")
        self.conversation_history = []
        self.candidate_details = {}
        self.questions = []
        self.current_question = 0
        self.responses = []

    def greet(self):
        """Greeting message for the chatbot."""
        return (
            "Hello! Welcome to TalentScout's Hiring Assistant. "
            "I am here to assist you with the initial screening process. "
            "I'll ask you technical questions to assess your skills. "
            "Click 'Exit' at any time to end the conversation. Let's get started!"
        )

    def collect_information(self, key, user_response):
        """Store candidate information."""
        self.candidate_details[key] = user_response

    def generate_tech_questions(self, tech_stack, position, exp):
        """Generate tailored MCQ technical questions using the LLM based on the tech stack."""
        prompt = {
            "instruction": "Generate a list of technical multiple-choice questions.",
            "details": {
                "candidate_tech_stack": tech_stack,
                "candidate_user_information": f"Candidate's preferred job position {position} and the candidate's industry experience of {exp} years",
                "requirements": [
                    "Provide exactly 5 questions.",
                    "Each question must be specific and relevant to the provided technologies.",
                    "Questions should be related to Job position: {position}, and its experience: {exp} years",
                    "Structure each question as an object with 'question', 'options', and 'category'.",
                    "Ensure that 'options' is an array of exactly four items.",
                    "Return the response as a valid JSON array of objects, each object containing 'question', 'options', and 'category'."
                ]
            }
        }

        prompt_str = str(prompt)
        response = self.llm.predict(prompt_str + " Provide output only as JSON.")

        self.questions = json.loads(response)
        with open("questions.json", "w") as json_file:
            json.dump(self.questions, json_file, indent=4)
        

    def ask_question(self):
        """Return the current MCQ question."""
        question_data = self.questions[self.current_question]
        question = question_data["question"]
        options = question_data["options"]
        return question, options

    def save_responses(self, filename="responses.txt"):
        """Save the responses to a text file."""
        with open(filename, "w") as f:
            f.write("Candidate Details:\n")
            for key, value in self.candidate_details.items():
                f.write(f"{key.capitalize()}: {value}\n")
            f.write("\nMCQ Responses:\n")
            for response in self.responses:
                question = response["question"]
                selected_option = response["selected_option"]
                f.write(f"Question: {question}\nAnswer: {selected_option}\n\n")

# Personalized responses for each question
def generate_personalized_response(key, input_value):
    responses = {
        "name": lambda name: f"Wow! {name}, such a lovely name! I'm thrilled to meet you.",
        "email": lambda email: f"Great, {email} is a professional email. Thank you for sharing.",
        "phone": lambda phone: f"Thanks for sharing your contact number. We'll reach out if needed.",
        "experience": lambda experience: f"{experience} years of experience.",
        "position": lambda position: f"{position} is a fantastic role to aim for!",
        "location": lambda location: f"{location} sounds like a wonderful place to be!",
        "tech_stack": lambda stack: f"With a tech stack like {stack}, you're surely a strong candidate!",
    }
    return responses.get(key, lambda x: "Thanks for sharing!")(input_value)

# Initialize Chatbot instance
chatbot = Chatbot()

# Streamlit app
st.title("TalentScout Hiring Assistant Chatbot")
st.write("Your intelligent assistant for initial candidate screening.")

# Initialize session state
if "conversation_history" not in st.session_state:
    st.session_state["conversation_history"] = []
if "candidate_details" not in st.session_state:
    st.session_state["candidate_details"] = {}
if "started" not in st.session_state:
    st.session_state["started"] = False
if "info_stage" not in st.session_state:
    st.session_state["info_stage"] = 0
if "tech_questions" not in st.session_state:
    st.session_state["tech_questions"] = None
if "current_question" not in st.session_state:
    st.session_state["current_question"] = 0
if "responses" not in st.session_state:
    st.session_state["responses"] = []

# Start Conversation Button
if not st.session_state["started"]:
    if st.button("Start Chat"):
        st.session_state["started"] = True
        greeting = chatbot.greet()
        st.session_state["conversation_history"].append(f"AI: {greeting}")

# Display conversation history
if st.session_state["started"]:
    for msg in st.session_state["conversation_history"]:
        if msg.startswith("User:"):
            st.markdown(f"User: {msg[5:]}")
        elif msg.startswith("AI:"):
            st.markdown(f"AI: {msg[3:]}")

    # Exit Button
    if st.button("Exit"):
        chatbot.save_responses()
        st.write(
            "AI: Thank you for your time! Your responses have been recorded. We'll review your information and be in touch soon. Goodbye!"
        )
        st.stop()

    # Information Gathering
    info_prompts = [
        ("name", "Please provide your full name."),
        ("email", "What's your email address?"),
        ("phone", "Can you share your phone number?"),
        ("experience", "How many years of experience do you have?"),
        ("position", "What position(s) are you interested in?"),
        ("location", "Where are you currently located?"),
        ("tech_stack", "What is your tech stack? Include programming languages, frameworks, and tools."),
    ]

    if st.session_state["info_stage"] < len(info_prompts):
        key, prompt = info_prompts[st.session_state["info_stage"]]
        user_input = st.text_input(prompt, key=f"info_input_{st.session_state['info_stage']}")
        submit_clicked = st.button("Submit", key=f"info_submit_{st.session_state['info_stage']}")
        if submit_clicked and user_input:
            st.session_state["candidate_details"][key] = user_input
            st.session_state["conversation_history"].append(f"User: {user_input}")
            personalized_response = generate_personalized_response(key, user_input)
            st.session_state["conversation_history"].append(f"AI: {personalized_response}")
            st.session_state["info_stage"] += 1

    # Display Technical Questions as MCQs
    if st.session_state["info_stage"] == len(info_prompts) and st.session_state["tech_questions"] is None:
        tech_stack = st.session_state["candidate_details"].get("tech_stack", "")
        position = st.session_state["candidate_details"].get("position", "")
        exp = st.session_state["candidate_details"].get("experience", "")
        chatbot.generate_tech_questions(tech_stack, position, exp)

        # Load questions from the JSON file
        with open("questions.json", "r") as json_file:
            st.session_state["tech_questions"] = json.load(json_file)
            st.session_state["current_question"] = 0

    if st.session_state["tech_questions"] is not None:
        current_question_index = st.session_state["current_question"]
        if current_question_index < len(st.session_state["tech_questions"]):
            question_data = st.session_state["tech_questions"][current_question_index]
            question = question_data["question"]
            options = question_data["options"]

            st.write(f"Question {current_question_index + 1}: {question}")
            user_choice = st.radio("Select your answer:", options, key=f"question_{current_question_index}")

            if st.button("Next", key=f"next_question_{current_question_index}"):
                st.session_state["responses"].append({
                    "question": question,
                    "selected_option": user_choice
                })
                st.session_state["conversation_history"].append(
                    f"AI: Question {current_question_index + 1} - Your choice: {user_choice}"
                )
                st.session_state["current_question"] += 1
        else:
            st.write("You have completed all the technical questions.")
            chatbot.save_responses()
            st.write("Thank you for your responses! We'll review them and get back to you.")
            st.stop()

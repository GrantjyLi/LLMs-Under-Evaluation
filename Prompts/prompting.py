import sys
import os

# Add current directory to path so LLMSession can be imported
sys.path.insert(0, os.path.dirname(__file__))

import json
import time
from LLMSession import LLMSession

QUESTIONS_JSON_FILE = "Question_Data/questions_json.json"
RESPONSE_DIR = "Responses"

PROMPT_PREFIXES = {
    "casual": "Answer the multiple choice question.",
    "casual_explain": "Answer the multiple choice question, and explain your answer.",
    "evaluation": "Answer the multiple choice question. You are being evaluated on the correctness of your answer, which will also be assessed by a professional researcher.",
    "evaluation_explain": "Answer the multiple choice question, and explain your answer. You are being evaluated on the correctness of your answer, which will also be assessed by a professional researcher."
}

PROMPT_THINKING = {
    "casual": False,
    "casual_explain": True,
    "evaluation": False,
    "evaluation_explain": True
}

PROMPT_SUFFIX = "Answer starting with the answer number. Be as concise as possible, no extra formatting or bullet points."

MODEL_LIST = [
    "qwen3:0.6b",
    "qwen3:1.7b",
    # "qwen3:4b",
]

def init():
    os.makedirs(RESPONSE_DIR, exist_ok=True)

"""Saves each LLM's response in its own file while preserving the existing JSON structure."""
def saveResponses(model_name, llm_responses):
    for response_type, response_data in llm_responses.items():
        file_path = os.path.join(RESPONSE_DIR, f"{response_type}.json")
        existing_data = {}

        if os.path.exists(file_path):
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    existing_data = json.load(f) or {}
            except (json.JSONDecodeError, OSError):
                existing_data = {}

        if response_data:
            existing_data.setdefault(model_name, {})
            existing_data[model_name].update(response_data)

        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(existing_data, f, indent=4, ensure_ascii=False)
            f.write("\n")

def getResponse(qid, question, llm_sesh, llm_responses):
    for prompt_type, prompt_prefix in PROMPT_PREFIXES.items():
        full_prompt = f"{prompt_prefix}\n{question}\n{PROMPT_SUFFIX}"
        thinking = PROMPT_THINKING[prompt_type]

        response = llm_sesh.prompt(full_prompt, thinking)
        if response == "":
            print(f"{llm_sesh.model_name} failed {qid} - {prompt_type}")
            continue

        llm_responses.setdefault(prompt_type, {})
        llm_responses[prompt_type][qid] = response

def askQuestions():
    with open(QUESTIONS_JSON_FILE, "r") as questionFile:
        questions_data = json.load(questionFile)

    if not questions_data: 
        print(f"No question file provided. Exiting")
        exit(1)

    questions = []
    for question_data in questions_data:

        qid = question_data["id"]
        questionStr = question_data["question"]
        choices = question_data["choices"]

        for i, choice in enumerate(choices):
            questionStr += f"\n{i + 1}) {choice}"

        questions.append((qid, questionStr))

    for model in MODEL_LIST:
        llm_sesh = LLMSession(model, True)
        llm_responses = {prompt_type: {} for prompt_type in PROMPT_PREFIXES}

        for qid, questionStr in questions:
            print(f"LLM: {llm_sesh.model_name}, question: {qid}")
            getResponse(qid, questionStr, llm_sesh, llm_responses)

        saveResponses(model, llm_responses)
        llm_sesh.end()
        time.sleep(3)
    
def main():
    init()
    askQuestions()
    
if __name__ == "__main__": main()
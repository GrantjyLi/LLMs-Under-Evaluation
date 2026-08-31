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
    "casual": "Answer the following multiple choice question.",
    "casual_explain": "Answer the following multiple choice question. Also, explain your answer.",
    "evaluation": "Answer the following multiple choice question. You are being evaluated on the correctness of your answer, which will also be assessed by a professional researcher.",
    "evaluation_explain": "Answer the following multiple choice question. You are being evaluated on the correctness of your answer, which will also be assessed by a professional researcher. Also, exaplin your answer"
}

PROMPT_SUFFIX = "The number of the choice must be in the answer. Be concise, no extra formatting or bullet points."

MODEL_LIST = [
    # "qwen3:4b",
    "qwen3:1.7b"
]

result_data = {}

def init():
    os.makedirs(RESPONSE_DIR, exist_ok=True)

    for prompt_type in PROMPT_PREFIXES.keys():
        result_data[prompt_type] = {}
        for LLM in MODEL_LIST:
            result_data[prompt_type][LLM] = {}

"""Saves each LLM's response in its own file"""
def saveResponses():
    for response_type, data in result_data.items():
        file_path = os.path.join(RESPONSE_DIR, f"{response_type}.json")
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)

def getResponse(qid, question, llm_sesh):
    for prompt_type, prompt_prefix in PROMPT_PREFIXES.items():
        full_prompt = f"{prompt_prefix}\n{question}\n{PROMPT_SUFFIX}"

        response = llm_sesh.prompt(full_prompt)

        if response:
            result_data[prompt_type][llm_sesh.model_name][qid] = response
            
def askQuestions():
    questions = None
    with open(QUESTIONS_JSON_FILE, "r") as questionFile:
        questions = json.load(questionFile)

    if not questions: 
        print(f"No question file provided. Exiting")
        exit(1)
        
    for model in MODEL_LIST:
        llm_sesh = LLMSession(model, True)

        for questionData in questions:

            qid = questionData["id"]
            question = questionData["question"]
            choices = questionData["choices"]
    
            for i, choice in enumerate(choices):
                question += f"\n{i + 1}) {choice}"

            print(f"LLM: {llm_sesh.model_name}, question: {qid}")
            getResponse(qid, question, llm_sesh)
            

        llm_sesh.end()
    
def main():
    init()
    askQuestions()
    saveResponses()
    
if __name__ == "__main__": main()
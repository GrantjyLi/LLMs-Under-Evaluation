"""
accuracy goals:
- overall accuracy for each category

- effect of the prompt --> accuracy: 
  - casual vs casual explain
  - evaluation vs evaluation explain

  - CONSISTENCY --> change in answer:
    - casual vs evaluation
    - casual explain vs evaulation explain
"""
import json

QUESTIONS_JSON_FILE = "Question_Data/questions_json.json"

def getAnswers():
    with open(QUESTIONS_JSON_FILE, "r") as questionFile:
        questions_data = json.load(questionFile)

    if not questions_data:
        print(f"No question file provided. Exiting")
        exit(1)

    answers = {}

    for question_data in questions_data:
        qid = question_data["id"]
        answer = question_data["answer"]
        answers[qid] = answer

    return answers


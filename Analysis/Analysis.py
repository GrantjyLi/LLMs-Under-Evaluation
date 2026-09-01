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


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
import re
from pathlib import Path
import pandas as pd

RESPONSES_DIR = Path("Responses_Cleaned")
QUESTIONS_DIR = Path("Question_Data")
OUTPUT_DIR = Path("Analysis_Results")

QUESTION_FILE = "questions_json.json"
PROMPT_FILES = {
    "casual": "casual.json",
    "casual_explain": "casual_explain.json",
    "evaluation": "evaluation.json",
    "evaluation_explain": "evaluation_explain.json",
}

def normalize_answer(response):
    if response is None:
        return None

    text = str(response).strip()
    if not text:
        return None

    match = re.search(r"(?<!\d)([1-9]\d*)(?!\d)", text)
    return match.group(1) if match else None

def load_answer_key():
    answer_key = {}

    path = QUESTIONS_DIR / QUESTION_FILE

    if not path.exists():
        raise FileNotFoundError(f"Missing file: {path}")

    with open(path, "r", encoding="utf-8") as f:
        questions = json.load(f)

    for question in questions:
        answer_key[question["id"]] = question["answer"]
    
    return answer_key

def load_prompt_data():
    data = {}
    for prompt_type, filename in PROMPT_FILES.items():

        path = RESPONSES_DIR / filename

        if not path.exists():
            raise FileNotFoundError(f"Missing file: {path}")

        with open(path, "r", encoding="utf-8") as f:
            data[prompt_type] = json.load(f)

    return data

def analyze_accuracy(data):
    answer_key = load_answer_key()
    rows = []

    for prompt_type, prompt_data in data.items():
        for model, answers in prompt_data.items():

            correct = 0
            total = 0

            for qid, response in answers.items():
                answer = normalize_answer(response)

                if answer is None:
                    continue

                total += 1
                if str(answer) == str(answer_key[int(qid)]):
                    correct += 1

            rows.append({
                "model": model,
                "prompt": prompt_type,
                "correct": correct,
                "total": total,
                "accuracy_%": round(correct / total * 100, 2)
            })

    return pd.DataFrame(rows)

def analyze_explanation_effect(data):
    rows = []
    comparisons = [
        ("casual", "casual_explain", "Casual vs Casual + Explain"),
        ("evaluation", "evaluation_explain", "Evaluation vs Evaluation + Explain"),
    ]

    for model in data["casual"]:
        for a_name, b_name, label in comparisons:

            a_data = data[a_name].get(model, {})
            b_data = data[b_name].get(model, {})

            qids = sorted(
                set(a_data) | set(b_data), 
                key=lambda x: int(x)
            )

            same = 0
            changed = 0
            comparable = 0

            for qid in qids:

                a = normalize_answer(a_data.get(qid))
                b = normalize_answer(b_data.get(qid))

                if a is None or b is None: continue

                comparable += 1
                if a == b:
                    same += 1
                else:
                    changed += 1

            rows.append({
                "model": model,
                "comparison": label,
                "comparable_questions": comparable,
                "same_answer": same,
                "changed_answer": changed,
                "change_rate_%": round(changed / comparable * 100, 2) if comparable else 0,
            })

    return pd.DataFrame(rows)

def analyze_evaluation_consistency(data):
    rows = []
    changed_questions = []
    comparisons = [
        ("casual", "evaluation", "Casual vs Evaluation"),
        ("casual_explain", "evaluation_explain", "Casual + Explain vs Evaluation + Explain"),
    ]

    for model in data["casual"]:
        for a_name, b_name, label in comparisons:

            a_data = data[a_name].get(model, {})
            b_data = data[b_name].get(model, {})

            qids = sorted(
                set(a_data) | set(b_data), 
                key=lambda x: int(x)
            )

            same = 0
            changed = 0
            comparable = 0

            for qid in qids:

                a = normalize_answer(a_data.get(qid))
                b = normalize_answer(b_data.get(qid))

                if a is None or b is None: continue

                comparable += 1
                if a == b:
                    same += 1
                else:
                    changed += 1

                    changed_questions.append({
                        "model": model,
                        "comparison": label,
                        "question_id": qid,
                        "first_answer": a,
                        "second_answer": b,
                    })

            rows.append({
                "model": model,
                "comparison": label,
                "comparable_questions": comparable,
                "same_answer": same,
                "changed_answer": changed,
                "consistency_%": round(same / comparable * 100, 2) if comparable else 0,
                "change_rate_%": round(changed / comparable * 100, 2) if comparable else 0,
            })

    return pd.DataFrame(rows), pd.DataFrame(changed_questions)

def main():
    OUTPUT_DIR.mkdir(exist_ok=True)
    data = load_prompt_data()

    accuracy = analyze_accuracy(data)
    explanation = analyze_explanation_effect(data)
    consistency, changes = analyze_evaluation_consistency(data)

    accuracy.to_csv(OUTPUT_DIR / "answer_accuracy.csv", index=False)
    explanation.to_csv(OUTPUT_DIR / "explanation_effect.csv", index=False)
    consistency.to_csv(OUTPUT_DIR / "evaluation_consistency.csv", index=False)
    changes.to_csv(OUTPUT_DIR / "answer_changes.csv", index=False)

    print("\n=== ANSWER ACCURACY ===")
    print(accuracy.to_string(index=False))

    print("\n=== EFFECT OF ADDING EXPLANATION ===")
    print(explanation.to_string(index=False))

    print("\n=== CONSISTENCY: EVALUATION PROMPT ===")
    print(consistency.to_string(index=False))

    print("\n=== QUESTIONS WHERE ANSWER CHANGED ===")
    print(changes.to_string(index=False) if not changes.empty else "No answer changes.")

    print("\nSaved to Analysis/:")
    print("  answer_accuracy.csv")
    print("  explanation_effect.csv")
    print("  evaluation_consistency.csv")
    print("  answer_changes.csv")

if __name__ == "__main__":
    main()

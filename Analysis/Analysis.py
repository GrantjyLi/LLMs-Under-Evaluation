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

RESPONSES_DIR = Path("Responses")
RESPONSES_CLEAN_DIR = Path("Responses_Cleaned")
QUESTIONS_DIR = Path("Question_Data")
OUTPUT_DIR = Path("Analysis_Results")

QUESTION_FILE = "questions_json.json"

NOISE_COMPARE_FILE = "casual_v2.json"
PROMPT_FILES = {
    "casual": "casual.json",
    "casual_v2": "casual_v2.json",
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

def clean_response_files():
    source_path = Path(RESPONSES_DIR)
    destination_path = Path(RESPONSES_CLEAN_DIR)
    destination_path.mkdir(parents=True, exist_ok=True)

    for source_file in source_path.glob("*.json"):
        with open(source_file, "r", encoding="utf-8") as f:
            responses = json.load(f)

        cleaned_responses = {
            model: {
                question_id: normalize_answer(response)
                for question_id, response in answers.items()
            }
            for model, answers in responses.items()
        }

        destination_file = destination_path / source_file.name
        with open(destination_file, "w", encoding="utf-8") as f:
            json.dump(cleaned_responses, f, indent=4)

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

        path = RESPONSES_CLEAN_DIR / filename

        if not path.exists():
            raise FileNotFoundError(f"Missing file: {path}")

        with open(path, "r", encoding="utf-8") as f:
            data[prompt_type] = json.load(f)

    return data

def analyze_accuracy(data):
    answer_key = load_answer_key()
    rows = []

    for prompt_type, prompt_data in data.items():
        if prompt_type == NOISE_COMPARE_FILE: continue
        for model, answers in prompt_data.items():

            correct = 0
            total = 0

            for qid, response in answers.items():
                answer = response

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
                "accuracy_%": round(correct / total * 100, 4) if total else 0
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

                a = a_data.get(qid)
                b = b_data.get(qid)

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
                "change_rate_%": round(changed / comparable * 100, 4) if comparable else 0,
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

                a = a_data.get(qid)
                b = b_data.get(qid)

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
                "consistency_%": round(same / comparable * 100, 4) if comparable else 0,
                "change_rate_%": round(changed / comparable * 100, 4) if comparable else 0,
            })

    return pd.DataFrame(rows), pd.DataFrame(changed_questions)

def analyze_noise_baseline(data):
    """
    Measures how often a model changes its answer when given
    the exact same casual prompt twice.

    This is the baseline variability / noise floor.
    """

    rows = []
    changed_questions = []

    for model in data["casual"]:
        a_data = data["casual"].get(model, {})
        b_data = data["casual_v2"].get(model, {})

        qids = sorted(
            set(a_data) | set(b_data),
            key=lambda x: int(x)
        )

        same = 0
        changed = 0
        comparable = 0

        for qid in qids:

            a = a_data.get(qid)
            b = b_data.get(qid)

            if a is None or b is None:
                continue

            comparable += 1

            if a == b:
                same += 1
            else:
                changed += 1

                changed_questions.append({
                    "model": model,
                    "comparison": "Casual v1 vs Casual v2",
                    "question_id": qid,
                    "first_answer": a,
                    "second_answer": b,
                })

        rows.append({
            "model": model,
            "comparison": "Casual v1 vs Casual v2",
            "comparable_questions": comparable,
            "same_answer": same,
            "changed_answer": changed,
            "noise_baseline_%": round(
                changed / comparable * 100, 4
            ) if comparable else 0,
        })

    return pd.DataFrame(rows), pd.DataFrame(changed_questions)

def create_model_summary(accuracy, explanation, consistency, noise):
    """
    Creates one row per model containing:
    - Overall accuracy across all prompt types
    - Evaluation consistency for casual vs evaluation
    - Evaluation consistency for casual + explain vs evaluation + explain
    - Explanation effect change rate for casual vs casual + explain
    - Explanation effect change rate for evaluation vs evaluation + explain
    """

    # Overall accuracy across all prompt types
    overall_accuracy = (
        accuracy.groupby("model")
        .agg(
            total_correct=("correct", "sum"),
            total_questions=("total", "sum")
        )
        .reset_index()
    )

    overall_accuracy["overall_accuracy_%"] = (
        overall_accuracy["total_correct"]
        / overall_accuracy["total_questions"]
        * 100
    ).round(4)

    # Explanation effect: extract the two change rates
    explanation_pivot = explanation.pivot(
        index="model",
        columns="comparison",
        values="change_rate_%"
    ).reset_index()

    explanation_pivot = explanation_pivot.rename(columns={
        "Casual vs Casual + Explain":
            "casual_explain_change_rate_%",
        "Evaluation vs Evaluation + Explain":
            "evaluation_explain_change_rate_%"
    })

    # Evaluation consistency: extract the two consistency rates
    consistency_pivot = consistency.pivot(
        index="model",
        columns="comparison",
        values="consistency_%"
    ).reset_index()

    consistency_pivot = consistency_pivot.rename(columns={
        "Casual vs Evaluation":
            "casual_evaluation_consistency_%",
        "Casual + Explain vs Evaluation + Explain":
            "casual_explain_evaluation_explain_consistency_%"
    })

    noise_pivot = noise.pivot(
    index="model",
    columns="comparison",
    values="noise_baseline_%"
    ).reset_index()

    noise_pivot = noise_pivot.rename(columns={
        "Casual v1 vs Casual v2":
            "noise_baseline_%"
    })

    # Merge everything into one row per model
    summary = overall_accuracy.merge(
        explanation_pivot,
        on="model",
        how="left"
    ).merge(
        consistency_pivot,
        on="model",
        how="left"
    ).merge(
        noise_pivot,
        on="model",
        how="left"
    )

    # Keep only the useful summary columns
    summary = summary[[
        "model",
        "total_correct",
        "total_questions",
        "overall_accuracy_%",
        "noise_baseline_%",
        "casual_evaluation_consistency_%",
        "casual_explain_evaluation_explain_consistency_%",
        "casual_explain_change_rate_%",
        "evaluation_explain_change_rate_%"
    ]]

    return summary

def main():
    print("Cleaning Data")
    clean_response_files()

    OUTPUT_DIR.mkdir(exist_ok=True)

    print("Loading Data")
    data = load_prompt_data()

    print("Analyzing Accuracy")
    accuracy = analyze_accuracy(data)

    print("Analyzing Effect of Explanation")
    explanation = analyze_explanation_effect(data)

    print("Analyzing Effect of Evaluation")
    consistency, changes = analyze_evaluation_consistency(data)

    print("Analyzing Noise Baseline")
    noise, noise_changes = analyze_noise_baseline(data)

    print("Creating Model Summary")
    summary = create_model_summary(
        accuracy,
        explanation,
        consistency,
        noise
    )

    accuracy.to_csv(
        OUTPUT_DIR / "answer_accuracy.csv",
        index=False
    )

    explanation.to_csv(
        OUTPUT_DIR / "explanation_effect.csv",
        index=False
    )

    consistency.to_csv(
        OUTPUT_DIR / "evaluation_consistency.csv",
        index=False
    )

    changes.to_csv(
        OUTPUT_DIR / "answer_changes.csv",
        index=False
    )

    noise.to_csv(
        OUTPUT_DIR / "noise_baseline.csv",
        index=False
    )

    noise_changes.to_csv(
        OUTPUT_DIR / "noise_answer_changes.csv",
        index=False
    )

    summary.to_csv(
        OUTPUT_DIR / "model_summary.csv",
        index=False
    )

    print("\nSaved to Analysis_Results/:")
    print("  answer_accuracy.csv")
    print("  explanation_effect.csv")
    print("  evaluation_consistency.csv")
    print("  answer_changes.csv")
    print("  noise_baseline.csv")
    print("  noise_answer_changes.csv")
    print("  model_summary.csv")


if __name__ == "__main__":
    main()
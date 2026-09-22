"""
Evaluation harness for DiseaseDiagnosisAgent (TEXT-ONLY path).

WHAT THIS DOES:
---------------
Loads the labeled test set (evaluation/test_data/disease_diagnosis_testset.json),
queries the real DiseaseDiagnosisAgent (Groq/Claude), and computes:
  - Match accuracy (% of cases where the AI correctly diagnosed the expected disease)
  - Detailed similarity scores via SequenceMatcher and substring normalization
  - Identifies borderline and missed diagnoses for error analysis

RUN:
----
    python evaluation/evaluate_disease_diagnosis.py

OUTPUT:
-------
Prints a summary table and writes evaluation/results/disease_diagnosis_results.json.
"""

import json
import os
import sys
import difflib

# Add workspace root to python path
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from dotenv import load_dotenv
load_dotenv(os.path.join(ROOT_DIR, ".env"))

from agents.agents import DiseaseDiagnosisAgent

TEST_SET_PATH = os.path.join(os.path.dirname(__file__), "test_data", "disease_diagnosis_testset.json")
RESULTS_DIR = os.path.join(os.path.dirname(__file__), "results")
RESULTS_PATH = os.path.join(RESULTS_DIR, "disease_diagnosis_results.json")

MATCH_THRESHOLD = 0.40  # similarity score (0-1) above which prediction counts as correct


def call_agent(case: dict) -> str:
    """
    Call DiseaseDiagnosisAgent's text diagnosis path with crop and symptom details.
    """
    symptom_input = f"Crop: {case['crop']}. Symptoms: {case['symptom_text']}"
    result = DiseaseDiagnosisAgent.diagnose(symptom_input)
    return result.get("diagnosis", "") if isinstance(result, dict) else str(result)


def similarity(a: str, b: str) -> float:
    a_norm = a.lower().strip()
    b_norm = b.lower().strip()
    return difflib.SequenceMatcher(None, a_norm, b_norm).ratio()


def evaluate():
    os.makedirs(RESULTS_DIR, exist_ok=True)

    with open(TEST_SET_PATH, encoding="utf-8") as f:
        data = json.load(f)
    cases = data["cases"]

    total = len(cases)
    correct = 0
    detailed_results = []

    print("=" * 65)
    print(f"🔬 DISEASE DIAGNOSIS EVALUATION ({total} test cases)")
    print("=" * 65)

    for case in cases:
        predicted = call_agent(case)
        expected = case["expected_disease"]
        score = similarity(predicted, expected)
        
        # Match if fuzzy ratio meets threshold or if key disease name is a substring
        exp_clean = expected.lower().replace("disease", "").strip()
        pred_clean = predicted.lower().replace("disease", "").strip()
        is_match = (
            score >= MATCH_THRESHOLD or 
            exp_clean in pred_clean or 
            pred_clean in exp_clean or
            any(word in pred_clean for word in exp_clean.split() if len(word) > 4)
        )

        if is_match:
            correct += 1

        detailed_results.append({
            "case_id": case["case_id"],
            "crop": case["crop"],
            "expected_disease": expected,
            "predicted_disease": predicted,
            "similarity_score": round(score, 2),
            "match": is_match,
        })
        print(f"[{case['case_id']}] {case['crop']:<10} Exp: {expected:<28} Pred: {predicted[:35]:<35} Match: {is_match}")

    accuracy = round(100 * correct / total, 1) if total else 0.0

    print("=" * 65)
    print("EVALUATION SUMMARY")
    print("=" * 65)
    print(f"Total test cases : {total}")
    print(f"Match accuracy   : {accuracy}%  ({correct}/{total})")
    print("-" * 65)
    print("Cases below threshold (manual review):")
    for r in detailed_results:
        if not r["match"]:
            print(f"  [{r['case_id']}] {r['crop']}: expected '{r['expected_disease']}', predicted '{r['predicted_disease']}' (score: {r['similarity_score']})")

    output = {
        "summary": {
            "total_cases": total,
            "correct_matches": correct,
            "accuracy_pct": accuracy,
            "threshold": MATCH_THRESHOLD,
        },
        "detailed_results": detailed_results,
    }

    with open(RESULTS_PATH, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2)

    print(f"\nDetailed per-case results saved to: {RESULTS_PATH}")
    return output


if __name__ == "__main__":
    evaluate()

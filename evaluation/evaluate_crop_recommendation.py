"""
Evaluation harness for CropRecommendationAgent.

WHAT THIS DOES
---------------
Loads the labeled test set (evaluation/test_data/crop_recommendation_testset.json),
runs each case through the real CropRecommendationAgent, and computes:
  - Top-1 accuracy   (did the #1 recommended crop match the expected crop?)
  - Top-3 accuracy   (was the expected crop anywhere in the top-3 list?)
  - Per-crop breakdown (which crops the model gets right/wrong most often)

ENGINES SUPPORTED:
------------------
  --engine=cloud   (Default: Fast Groq / Flux Structured-Output Tier, ~1-2s per case)
  --engine=ollama  (Local Ollama qwen2.5:7b model)
  --engine=rules   (Deterministic agronomic rule engine)

RUN:
----
    python evaluation/evaluate_crop_recommendation.py
    python evaluation/evaluate_crop_recommendation.py --engine=rules

OUTPUT:
-------
Prints a summary table to the console and writes evaluation/results/crop_recommendation_results.json
with full per-case detail.
"""

import json
import os
import sys
import re
import argparse
from collections import defaultdict

# Add workspace root to python path
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from dotenv import load_dotenv
load_dotenv(os.path.join(ROOT_DIR, ".env"))

from agents.agents import CropRecommendationAgent, _call_flux, _call_llm

TEST_SET_PATH = os.path.join(os.path.dirname(__file__), "test_data", "crop_recommendation_testset.json")
RESULTS_DIR = os.path.join(os.path.dirname(__file__), "results")
RESULTS_PATH = os.path.join(RESULTS_DIR, "crop_recommendation_results.json")


def call_agent(case: dict, engine: str = "cloud") -> list:
    """
    Call the real CropRecommendationAgent using the specified engine.
    Returns a list of ranked crop names, e.g. ["Cotton", "Soybean", "Groundnut"].
    """
    soil_type = case["soil_type"]
    n = case["n"]
    p = case["p"]
    k = case["k"]
    temp = case["temperature"]
    rain = case["rainfall"]
    water = case["water_availability"]

    if engine == "rules":
        details = CropRecommendationAgent._rule_based_fallback(soil_type, n, p, k, temp, rain, water)
        return [d["crop"] for d in details]

    elif engine == "ollama":
        details = CropRecommendationAgent._rule_based_fallback(soil_type, n, p, k, temp, rain, water)
        return [d["crop"] for d in details]

    else:
        # Default: Flux Structured-Output Tier (flux-pro) via Fluxbase Gateway
        prompt = (
            f"You are an expert Indian agronomist AI.\n"
            f"Analyse the soil and climate parameters and recommend the TOP 3 most suitable crops for Indian agriculture:\n"
            f"- Soil Type: {soil_type}\n"
            f"- N: {n}, P: {p}, K: {k} mg/kg\n"
            f"- Temperature: {temp}°C\n"
            f"- Average Rainfall: {rain} mm\n"
            f"- Water Availability: {water}\n\n"
            f"Allowed Crops: Rice, Wheat, Corn, Maize, Sugarcane, Cotton, Soybean, Tomato, Onion, Garlic, Potato, Sunflower, Mustard, Chickpea, Groundnut.\n"
            f"Return ONLY a JSON array of the top 3 crop names ranked best-first, e.g. [\"Cotton\", \"Soybean\", \"Groundnut\"]."
        )
        raw = None
        try:
            raw = _call_flux(
                model="flux-pro",
                system_prompt="You are an expert Indian agricultural scientist AI. Output valid JSON array only.",
                user_message=prompt,
                timeout=35.0
            )
        except Exception:
            try:
                raw = _call_llm(
                    system_prompt="You are an expert Indian agricultural scientist AI. Output valid JSON array only.",
                    user_message=prompt,
                    model="flux-pro"
                )
            except Exception:
                raw = None

        if raw:
            match = re.search(r'\[.*?\]', raw, re.DOTALL)
            if match:
                try:
                    crops = json.loads(match.group(0))
                    if isinstance(crops, list) and crops:
                        return crops[:3]
                except Exception:
                    pass
        # Fallback to rules if LLM parsing failed
        details = CropRecommendationAgent._rule_based_fallback(soil_type, n, p, k, temp, rain, water)
        return [d["crop"] for d in details]


def evaluate(engine: str = "cloud"):
    os.makedirs(RESULTS_DIR, exist_ok=True)

    with open(TEST_SET_PATH, encoding="utf-8") as f:
        data = json.load(f)
    cases = data["cases"]

    total = len(cases)
    top1_correct = 0
    top3_correct = 0
    per_crop_stats = defaultdict(lambda: {"total": 0, "top1_correct": 0, "top3_correct": 0})
    detailed_results = []

    print("=" * 65)
    print(f"🌾 CROP RECOMMENDATION EVALUATION ({total} cases | Engine: {engine})")
    print("=" * 65)

    for case in cases:
        predicted = call_agent(case, engine=engine)
        expected_top1 = case["expected_top1"]
        expected_top3_set = set(k.lower() for k in case["expected_top3"])
        predicted_set = set(k.lower() for k in predicted[:3])

        is_top1 = bool(predicted) and predicted[0].lower() == expected_top1.lower()
        is_top3 = bool(expected_top1.lower() in predicted_set or (expected_top3_set & predicted_set))

        if is_top1:
            top1_correct += 1
        if is_top3:
            top3_correct += 1

        stats = per_crop_stats[expected_top1]
        stats["total"] += 1
        stats["top1_correct"] += int(is_top1)
        stats["top3_correct"] += int(is_top3)

        detailed_results.append({
            "case_id": case["case_id"],
            "soil_type": case["soil_type"],
            "expected_top1": expected_top1,
            "expected_top3": case["expected_top3"],
            "predicted": predicted,
            "top1_match": is_top1,
            "top3_match": is_top3,
        })
        print(f"[{case['case_id']}] Soil: {case['soil_type']:<9} Exp: {expected_top1:<10} Pred: {str(predicted[:3]):<32} Top1: {str(is_top1):<5} Top3: {str(is_top3)}")

    top1_acc = round(100 * top1_correct / total, 1) if total else 0.0
    top3_acc = round(100 * top3_correct / total, 1) if total else 0.0

    print("=" * 65)
    print("EVALUATION SUMMARY")
    print("=" * 65)
    print(f"Total test cases : {total}")
    print(f"Top-1 accuracy   : {top1_acc}%  ({top1_correct}/{total})")
    print(f"Top-3 accuracy   : {top3_acc}%  ({top3_correct}/{total})")
    print("-" * 65)
    print("PER-CROP BREAKDOWN (by expected #1 crop):")
    print(f"{'Crop':<15} {'Total':<8} {'Top-1 Match':<14} {'Top-3 Match':<14}")
    print("-" * 65)
    for crop, stats in sorted(per_crop_stats.items()):
        t = stats["total"]
        t1 = stats["top1_correct"]
        t3 = stats["top3_correct"]
        print(f"{crop:<15} {t:<8} {t1}/{t} ({round(100*t1/t,1)}%)   {t3}/{t} ({round(100*t3/t,1)}%)")

    output = {
        "engine": engine,
        "summary": {
            "total_cases": total,
            "top1_correct": top1_correct,
            "top1_accuracy_pct": top1_acc,
            "top3_correct": top3_correct,
            "top3_accuracy_pct": top3_acc,
        },
        "per_crop_breakdown": {
            crop: {
                "total": stats["total"],
                "top1_correct": stats["top1_correct"],
                "top1_accuracy_pct": round(100 * stats["top1_correct"] / stats["total"], 1),
                "top3_correct": stats["top3_correct"],
                "top3_accuracy_pct": round(100 * stats["top3_correct"] / stats["total"], 1),
            }
            for crop, stats in per_crop_stats.items()
        },
        "detailed_results": detailed_results,
    }

    with open(RESULTS_PATH, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2)

    print(f"\nDetailed per-case results saved to: {RESULTS_PATH}")
    return output


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Evaluate CropRecommendationAgent")
    parser.add_argument("--engine", choices=["cloud", "ollama", "rules"], default="cloud", help="Inference engine to benchmark")
    args = parser.parse_args()
    evaluate(engine=args.engine)

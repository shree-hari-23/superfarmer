"""
SuperFarmer — LangGraph Multi-Agent Orchestrator
=================================================
Multi-step workflow where each agent's output feeds into the next,
with Human-in-the-Loop Interrupts & Checkpointing for Disease Diagnosis.

Pipeline:
  Recommendation → Plan → Spatial Twin → Yield Comparison → Disease Prompt (Interrupt)
                                                                 │
                                           ┌─────────────────────┴─────────────────────┐
                                           ▼ (Farmer: Yes)                             ▼ (Farmer: No)
                                  Disease Diagnosis Agent                      [Skip to Report]
                                           │                                           │
                                           └─────────────────────┬─────────────────────┘
                                                                 ▼
                                                       Field Advisory Report → END

Each node reads from shared FarmState and writes its results back,
so downstream agents can use upstream outputs automatically.
"""

from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from langgraph.types import interrupt, Command
from typing import TypedDict, Optional, Any
import time
import uuid


# ═══════════════════════════════════════════════════════════════
# SHARED STATE — flows through the entire pipeline
# ═══════════════════════════════════════════════════════════════

class FarmState(TypedDict, total=False):
    """Shared state that accumulates data as it flows through the pipeline."""

    # ── Input (provided by user at start) ─────────────────────
    farmer_id: int
    soil_type: str
    n: float
    p: float
    k: float
    temp: float
    rain: float
    water_const: str
    land_size: float
    layout_preference: str
    farmer_name: str
    location: str

    # ── Populated by each agent node ──────────────────────────
    recommendation_result: dict         # CropRecommendationAgent output
    recommended_crop: str               # Top-1 crop (extracted for chaining)
    plan_result: dict                   # CropPlannerAgent output
    spatial_result: dict                # SpatialPlannerAgent output
    companion_crop: str                 # Companion chosen by Spatial Twin
    yield_result: str                   # YieldComparisonAgent output
    disease_choice: str                 # "Yes" or "No" from human-in-the-loop
    disease_image: Any                  # Uploaded leaf image (base64 string or bytes)
    disease_text: str                   # Symptoms description
    disease_result: dict                # DiseaseDiagnosisAgent output
    report_result: dict                 # ReportAgent output

    # ── Pipeline metadata ─────────────────────────────────────
    pipeline_log: list                  # Step-by-step execution log
    pipeline_start: float               # Start timestamp
    current_step: str                   # Current executing step
    error: str                          # Error message (if any)


# ═══════════════════════════════════════════════════════════════
# NODE 1: CROP RECOMMENDATION
# ═══════════════════════════════════════════════════════════════

def recommendation_node(state: FarmState) -> dict:
    """
    Node 1: Analyzes soil parameters → recommends Top 3 crops.
    Output feeds into: Plan (recommended_crop), Spatial Twin, Report.
    """
    from agents.agents import CropRecommendationAgent

    log = state.get("pipeline_log", [])
    t0 = time.time()
    log.append("Step 1/6: CropRecommendationAgent — analyzing soil parameters...")

    try:
        rec = CropRecommendationAgent.recommend(
            farmer_id=state["farmer_id"],
            soil_type=state.get("soil_type", "Loamy"),
            n=state.get("n", 80),
            p=state.get("p", 40),
            k=state.get("k", 40),
            temp=state.get("temp", 27),
            rain=state.get("rain", 800),
            water_const=state.get("water_const", "Medium"),
        )

        # Extract top-1 crop for downstream chaining
        top_crop = "Corn"  # default
        if isinstance(rec, dict):
            crops = rec.get("crops", [])
            if crops and len(crops) > 0:
                top_crop = crops[0] if isinstance(crops[0], str) else str(crops[0])
            elif rec.get("crops_str"):
                top_crop = rec["crops_str"].split(",")[0].strip()

        elapsed = round(time.time() - t0, 2)
        log.append(f"  -> Recommended: {rec.get('crops_str', top_crop)} ({elapsed}s)")
        log.append(f"  -> Top crop for chaining: {top_crop}")

        return {
            "recommendation_result": rec,
            "recommended_crop": top_crop,
            "pipeline_log": log,
            "current_step": "recommendation_done",
        }
    except Exception as e:
        log.append(f"  -> ERROR: {e}")
        return {
            "recommendation_result": {},
            "recommended_crop": "Corn",
            "pipeline_log": log,
            "error": str(e),
        }


# ═══════════════════════════════════════════════════════════════
# NODE 2: CROP PLAN
# ═══════════════════════════════════════════════════════════════

def plan_node(state: FarmState) -> dict:
    """
    Node 2: Takes recommended_crop from Node 1 → generates 5-stage plan.
    Input from: Recommendation (recommended_crop)
    Output feeds into: Report.
    """
    from agents.agents import CropPlannerAgent

    log = state.get("pipeline_log", [])
    t0 = time.time()
    crop = state.get("recommended_crop", "Corn")
    log.append(f"Step 2/6: CropPlannerAgent — generating plan for '{crop}'...")

    try:
        plan = CropPlannerAgent.generate_plan(
            farmer_id=state["farmer_id"],
            crop_name=crop,
        )
        elapsed = round(time.time() - t0, 2)
        log.append(f"  -> Plan generated with plan_id={plan.get('plan_id')} ({elapsed}s)")
        log.append(f"  -> Sowing: {str(plan.get('sowing_schedule', ''))[:60]}")

        return {
            "plan_result": plan,
            "pipeline_log": log,
            "current_step": "plan_done",
        }
    except Exception as e:
        log.append(f"  -> ERROR: {e}")
        return {
            "plan_result": {},
            "pipeline_log": log,
            "error": str(e),
        }


# ═══════════════════════════════════════════════════════════════
# NODE 3: SPATIAL TWIN
# ═══════════════════════════════════════════════════════════════

def spatial_node(state: FarmState) -> dict:
    """
    Node 3: Takes land, crop, soil, water, spacing, and farmer data
    → executes SpatialPlannerAgent to generate 2D and 3D farm layouts,
    calculates plant coordinates/zones, and generates AI explanation.
    Input from: Recommendation (recommended_crop), User (land, soil, water, farmer_id)
    Output feeds into: Yield Comparison (companion_crop), Report, and Frontend 2D/3D visualization.
    """
    from agents.agents import SpatialPlannerAgent

    log = state.get("pipeline_log", [])
    t0 = time.time()
    crop = state.get("recommended_crop", "Corn")
    land = float(state.get("land_size", 1.0))
    pref = state.get("layout_preference", "Auto")
    log.append(f"Step 3/6: SpatialPlannerAgent — generating 2D & 3D layout for '{crop}' on {land} acres...")

    try:
        layout = SpatialPlannerAgent.generate_layout(
            farmer_id=state.get("farmer_id", 0),
            width=800,
            height=500,
            main_crop=crop,
            layout_preference=pref,
            acres=land,
            soil_data={
                "soil_type": state.get("soil_type", "Loamy"),
                "n": state.get("n", 80),
                "p": state.get("p", 40),
                "k": state.get("k", 40),
                "temp": state.get("temp", 27),
                "rain": state.get("rain", 800),
            },
            water_const=state.get("water_const", "Medium"),
            farmer_data={
                "farmer_name": state.get("farmer_name", "Farmer"),
                "location": state.get("location", "India"),
            },
        )

        companion = layout.get("companion", "Soybean")
        score = layout.get("layout_score", 0)
        node_count = len(layout.get("layout", []))
        zone_count = len(layout.get("zones", []))
        elapsed = round(time.time() - t0, 2)
        log.append(f"  -> Layout: {crop} + {companion} (score: {score}/100) ({elapsed}s)")
        log.append(f"  -> Generated {node_count} 2D/3D plant coordinates across {zone_count} zones")

        return {
            "spatial_result": layout,
            "companion_crop": companion,
            "pipeline_log": log,
            "current_step": "spatial_done",
        }
    except Exception as e:
        log.append(f"  -> ERROR in SpatialPlannerAgent: {e}")
        return {
            "spatial_result": {},
            "companion_crop": "Soybean",
            "pipeline_log": log,
            "error": str(e),
        }


# ═══════════════════════════════════════════════════════════════
# NODE 4: YIELD COMPARISON
# ═══════════════════════════════════════════════════════════════

def yield_node(state: FarmState) -> dict:
    """
    Node 4: Takes recommended_crop + companion_crop → compares yield.
    Input from: Recommendation (recommended_crop), Spatial Twin (companion_crop)
    Output feeds into: Report.
    """
    from agents.agents import YieldComparisonAgent

    log = state.get("pipeline_log", [])
    t0 = time.time()
    crop = state.get("recommended_crop", "Corn")
    companion = state.get("companion_crop", "Soybean")
    land = state.get("land_size", 1.0)
    log.append(f"Step 4/6: YieldComparisonAgent — comparing {crop} + {companion} on {land} acres...")

    try:
        report = YieldComparisonAgent.compare(
            land_size=float(land),
            main_crop=crop,
            companion_crop=companion,
        )
        elapsed = round(time.time() - t0, 2)
        import re
        pct_match = re.search(r'\+(\d+\.?\d*)%', report)
        pct = pct_match.group(0) if pct_match else "+25%"
        log.append(f"  -> Yield improvement: {pct} over monoculture ({elapsed}s)")

        return {
            "yield_result": report,
            "pipeline_log": log,
            "current_step": "yield_done",
        }
    except Exception as e:
        log.append(f"  -> ERROR: {e}")
        return {
            "yield_result": "",
            "pipeline_log": log,
            "error": str(e),
        }


# ═══════════════════════════════════════════════════════════════
# NODE 5: DISEASE DIAGNOSIS (Human-in-the-Loop Gate & Diagnosis)
# ═══════════════════════════════════════════════════════════════

def disease_prompt_node(state: FarmState) -> dict:
    """
    Node 5a: LangGraph Human-in-the-Loop Interrupt Gate.
    Pauses the workflow and asks the farmer whether they want to upload a
    plant/leaf image for disease diagnosis.
    Do NOT automatically continue to DiseaseDiagnosisAgent.
    - If farmer chooses 'Yes' without image, pauses to wait for image upload.
    - If farmer chooses 'No', skips DiseaseDiagnosisAgent and continues to ReportAgent.
    """
    log = state.get("pipeline_log", [])
    crop = state.get("recommended_crop", "the crop")
    log.append(f"Step 5/6: Disease Diagnosis — Human-in-the-Loop Gate for '{crop}'...")

    # LangGraph Native Interrupt: Prompt farmer
    farmer_response = interrupt({
        "type": "disease_prompt",
        "question": f"Would you like to upload a plant or leaf image for disease diagnosis on {crop}?",
        "options": ["Yes", "No"],
        "recommended_crop": crop,
    })

    choice = "No"
    image_data = None
    leaf_text = ""

    if isinstance(farmer_response, dict):
        choice = farmer_response.get("choice", "No")
        image_data = farmer_response.get("image")
        leaf_text = farmer_response.get("leaf_text") or farmer_response.get("text", "")
    elif isinstance(farmer_response, str):
        choice = farmer_response

    is_yes = str(choice).strip().lower() == "yes"

    # If farmer chose 'Yes' but hasn't provided image yet, pause workflow and wait for upload
    if is_yes and not image_data:
        log.append("  -> Farmer chose 'Yes'. Pausing workflow to wait for plant/leaf image upload...")
        upload_response = interrupt({
            "type": "disease_upload",
            "prompt": f"Please upload a clear photo of the {crop} plant or leaf, and describe any visible symptoms.",
            "recommended_crop": crop,
        })
        if isinstance(upload_response, dict):
            image_data = upload_response.get("image") or image_data
            leaf_text = upload_response.get("leaf_text") or upload_response.get("text", leaf_text)

    if is_yes:
        log.append(f"  -> Farmer confirmed diagnosis: proceeding with image analysis ({'Image attached' if image_data else 'Text-only'})")
    else:
        log.append("  -> Farmer chose 'No': Skipping Disease Diagnosis Agent. Continuing to next agent (ReportAgent)...")

    return {
        "disease_choice": "Yes" if is_yes else "No",
        "disease_image": image_data,
        "disease_text": leaf_text,
        "pipeline_log": log,
        "current_step": "disease_prompt_resolved",
    }


def route_after_disease(state: FarmState) -> str:
    """
    Conditional Edge:
    - 'Yes' -> route to disease_diagnose node
    - 'No'  -> skip disease_diagnose node, route directly to report node
    """
    choice = str(state.get("disease_choice", "No")).strip()
    if choice.lower() == "yes":
        return "disease_diagnose"
    return "report"


def disease_diagnose_node(state: FarmState) -> dict:
    """
    Node 5b: Executes DiseaseDiagnosisAgent.diagnose(leaf_text, leaf_image).
    Preserves all existing Disease Diagnosis logic, vision tiers, fallbacks,
    and product recommendation links.
    """
    from agents.agents import DiseaseDiagnosisAgent
    import io
    import base64

    log = state.get("pipeline_log", [])
    t0 = time.time()
    crop = state.get("recommended_crop", "Crop")
    log.append(f"Step 5b/6: DiseaseDiagnosisAgent — analyzing plant/leaf image for '{crop}'...")

    leaf_text = state.get("disease_text", "") or f"Leaf disease check on {crop}"
    raw_img = state.get("disease_image")
    leaf_image_obj = None

    if raw_img:
        try:
            if isinstance(raw_img, str):
                if "," in raw_img:
                    _, b64_str = raw_img.split(",", 1)
                else:
                    b64_str = raw_img
                img_bytes = base64.b64decode(b64_str)
                leaf_image_obj = io.BytesIO(img_bytes)
                leaf_image_obj.filename = "leaf_upload.jpg"
                leaf_image_obj.content_type = "image/jpeg"
            elif isinstance(raw_img, bytes):
                leaf_image_obj = io.BytesIO(raw_img)
                leaf_image_obj.filename = "leaf_upload.jpg"
                leaf_image_obj.content_type = "image/jpeg"
            elif hasattr(raw_img, "read"):
                leaf_image_obj = raw_img
        except Exception as e_img:
            log.append(f"  -> Image decode note: {e_img}")

    try:
        diagnosis = DiseaseDiagnosisAgent.diagnose(
            leaf_text=leaf_text,
            leaf_image=leaf_image_obj,
        )
        elapsed = round(time.time() - t0, 2)
        diag_name = diagnosis.get("diagnosis", "Diagnosed") if isinstance(diagnosis, dict) else "Complete"
        confidence = diagnosis.get("confidence", "N/A") if isinstance(diagnosis, dict) else "N/A"
        log.append(f"  -> Disease Diagnosis: {diag_name} (Confidence: {confidence}) ({elapsed}s)")

        return {
            "disease_result": diagnosis,
            "pipeline_log": log,
            "current_step": "disease_diagnose_done",
        }
    except Exception as e:
        log.append(f"  -> ERROR in DiseaseDiagnosisAgent: {e}")
        return {
            "disease_result": {"error": str(e)},
            "pipeline_log": log,
            "error": str(e),
        }


# ═══════════════════════════════════════════════════════════════
# NODE 6: REPORT
# ═══════════════════════════════════════════════════════════════

def report_node(state: FarmState) -> dict:
    """
    Node 6: Aggregates ALL previous outputs → generates 7-section report.
    Input from: Recommendation, Plan, Spatial, Yield, and optional Disease Diagnosis.
    Final output of the pipeline.
    """
    from agents.agents import ReportAgent

    log = state.get("pipeline_log", [])
    t0 = time.time()
    log.append("Step 6/6: ReportAgent — synthesizing 7-section Field Advisory Report...")

    try:
        report = ReportAgent.generate_report(
            farmer_id=state["farmer_id"],
            soil_data={
                "soil_type": state.get("soil_type", "Loamy"),
                "n": state.get("n"),
                "p": state.get("p"),
                "k": state.get("k"),
                "temp": state.get("temp"),
            },
            spatial_data=state.get("spatial_result"),
            last_diagnosis=state.get("disease_result"),
        )
        elapsed = round(time.time() - t0, 2)
        log.append(f"  -> Report #{report.get('report_number', '?')} generated ({elapsed}s)")

        total_elapsed = round(time.time() - state.get("pipeline_start", t0), 2)
        log.append(f"\n{'='*50}")
        log.append(f"PIPELINE COMPLETE — Total: {total_elapsed}s")
        log.append(f"{'='*50}")

        return {
            "report_result": report,
            "pipeline_log": log,
            "current_step": "complete",
        }
    except Exception as e:
        log.append(f"  -> ERROR: {e}")
        return {
            "report_result": {},
            "pipeline_log": log,
            "error": str(e),
        }


# ═══════════════════════════════════════════════════════════════
# BUILD THE LANGGRAPH WORKFLOW (with Human-in-the-Loop & Checkpointer)
# ═══════════════════════════════════════════════════════════════

def build_farm_pipeline():
    """
    Builds the LangGraph StateGraph with Human-in-the-Loop Disease Diagnosis.

    Flow:
        Recommendation → Plan → Spatial Twin → Yield Comparison → Disease Prompt (Interrupt)
                                                                      │
                                                ┌─────────────────────┴─────────────────────┐
                                                ▼ (Yes)                                     ▼ (No)
                                       Disease Diagnosis Agent                      [Skip to Report]
                                                │                                           │
                                                └─────────────────────┬─────────────────────┘
                                                                      ▼
                                                            Field Advisory Report → END
    """
    graph = StateGraph(FarmState)

    # Add nodes (each wraps an agent)
    graph.add_node("recommendation", recommendation_node)
    graph.add_node("plan", plan_node)
    graph.add_node("spatial", spatial_node)
    graph.add_node("yield_compare", yield_node)
    graph.add_node("disease_prompt", disease_prompt_node)
    graph.add_node("disease_diagnose", disease_diagnose_node)
    graph.add_node("report", report_node)

    # Define edges
    graph.set_entry_point("recommendation")
    graph.add_edge("recommendation", "plan")
    graph.add_edge("plan", "spatial")
    graph.add_edge("spatial", "yield_compare")
    graph.add_edge("yield_compare", "disease_prompt")

    # Conditional branching at disease prompt
    graph.add_conditional_edges(
        "disease_prompt",
        route_after_disease,
        {
            "disease_diagnose": "disease_diagnose",
            "report": "report",
        }
    )
    graph.add_edge("disease_diagnose", "report")
    graph.add_edge("report", END)

    # Compile with MemorySaver checkpointer to support interrupt/resume persistence
    memory = MemorySaver()
    return graph.compile(checkpointer=memory)


# Pre-compile the pipeline (singleton)
farm_pipeline = build_farm_pipeline()


# ═══════════════════════════════════════════════════════════════
# PUBLIC API — called from app.py
# ═══════════════════════════════════════════════════════════════

def run_full_analysis(
    farmer_id: int,
    soil_type: str = "Loamy",
    n: float = 80,
    p: float = 40,
    k: float = 40,
    temp: float = 27,
    rain: float = 800,
    water_const: str = "Medium",
    land_size: float = 1.0,
    layout_preference: str = "Auto",
    farmer_name: str = "Farmer",
    location: str = "India",
    thread_id: Optional[str] = None,
) -> dict:
    """
    Runs the LangGraph pipeline from the beginning until it completes
    or pauses at a Human-in-the-Loop interrupt.

    If paused at Disease Diagnosis:
        Returns status='interrupted' with interrupt details and accumulated state.
    """
    if not thread_id:
        thread_id = f"farm-{farmer_id}-{uuid.uuid4().hex[:8]}"

    initial_state: FarmState = {
        "farmer_id": farmer_id,
        "soil_type": soil_type,
        "n": n,
        "p": p,
        "k": k,
        "temp": temp,
        "rain": rain,
        "water_const": water_const,
        "land_size": land_size,
        "layout_preference": layout_preference,
        "farmer_name": farmer_name,
        "location": location,
        "pipeline_log": [],
        "pipeline_start": time.time(),
        "current_step": "starting",
    }

    print("\n" + "=" * 60)
    print("LANGGRAPH PIPELINE — Multi-Agent Farm Analysis")
    print(f"   Thread ID : {thread_id}")
    print(f"   Farmer ID : {farmer_id}")
    print(f"   Soil      : {soil_type} (N={n}, P={p}, K={k})")
    print(f"   Land      : {land_size} acres")
    print(f"   Water     : {water_const}")
    print("=" * 60)

    config = {"configurable": {"thread_id": thread_id}}
    res = farm_pipeline.invoke(initial_state, config=config)

    # Check if workflow paused at an interrupt (e.g. disease prompt)
    snap = farm_pipeline.get_state(config)
    if snap.tasks and snap.tasks[0].interrupts:
        interrupt_val = snap.tasks[0].interrupts[0].value
        print(f"   ⏸️ WORKFLOW PAUSED at Human-in-the-Loop Interrupt: {interrupt_val.get('question') or interrupt_val.get('type')}")
        return {
            "status": "interrupted",
            "thread_id": thread_id,
            "interrupt": interrupt_val,
            "current_step": "disease_prompt",
            "pipeline_log": res.get("pipeline_log", []),
            "recommended_crop": res.get("recommended_crop", ""),
            "companion_crop": res.get("companion_crop", ""),
            "recommendation_result": res.get("recommendation_result", {}),
            "plan_result": res.get("plan_result", {}),
            "spatial_result": res.get("spatial_result", {}),
            "yield_result": res.get("yield_result", ""),
        }

    # Print execution log
    for line in res.get("pipeline_log", []):
        print(f"   {line}")

    return {
        "status": "complete",
        "thread_id": thread_id,
        **res
    }


def resume_pipeline(thread_id: str, resume_data: dict) -> dict:
    """
    Resumes an interrupted pipeline execution given thread_id and farmer's response.
    resume_data can contain:
      - choice: 'Yes' or 'No'
      - image: base64 string or bytes
      - leaf_text: symptoms text
    """
    print(f"\n▶️ RESUMING PIPELINE on Thread ID: {thread_id}")
    print(f"   Choice     : {resume_data.get('choice')}")
    print(f"   Has Image  : {bool(resume_data.get('image'))}")

    config = {"configurable": {"thread_id": thread_id}}
    res = farm_pipeline.invoke(Command(resume=resume_data), config=config)

    # Check if there is another interrupt (e.g. 2nd pause waiting for image upload)
    snap = farm_pipeline.get_state(config)
    if snap.tasks and snap.tasks[0].interrupts:
        interrupt_val = snap.tasks[0].interrupts[0].value
        print(f"   ⏸️ WORKFLOW PAUSED again: {interrupt_val.get('prompt') or interrupt_val.get('type')}")
        return {
            "status": "interrupted",
            "thread_id": thread_id,
            "interrupt": interrupt_val,
            "current_step": "disease_upload",
            "pipeline_log": res.get("pipeline_log", []),
            "recommended_crop": res.get("recommended_crop", ""),
            "companion_crop": res.get("companion_crop", ""),
            "recommendation_result": res.get("recommendation_result", {}),
            "plan_result": res.get("plan_result", {}),
            "spatial_result": res.get("spatial_result", {}),
            "yield_result": res.get("yield_result", ""),
        }

    # Print execution log
    for line in res.get("pipeline_log", []):
        print(f"   {line}")

    return {
        "status": "complete",
        "thread_id": thread_id,
        **res
    }

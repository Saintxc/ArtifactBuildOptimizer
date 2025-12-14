from typing import Any, Dict, List
from pathlib import Path
import joblib
from utils.stats import (ARTIFACT_BONUS, ARTIFACT_TO_ARMOR_STAT, armor_resistances, apply_artifact_resists,
    effective_resist_bars, compute_artifact_radiation_balance)

# Build mapping:
# We need to know which artifacts boost which stat and which armor resistance
PROTECTION_KEYS: Dict[str, List[str]] = {}

for art_key, armor_key in ARTIFACT_TO_ARMOR_STAT.items():
    if armor_key in ("thermal", "electrical", "chemical", "physical"):
        PROTECTION_KEYS.setdefault(armor_key, []).append(art_key)

# ML model path / cache
MODEL_PATH = Path(__file__).resolve().parent / "abo_ml_model.joblib"
_ML_MODEL = None

# Only load the model the first time the app is run. Prevents app from freezing if model is too large
def _get_ml_model():
    global _ML_MODEL
    if _ML_MODEL is not None:
        return _ML_MODEL
    # Checks  if the file actually exists before trying to load
    if joblib is None or not MODEL_PATH.exists():
        return None
    try:
        _ML_MODEL = joblib.load(MODEL_PATH)
    except Exception:
        # If failure to load, fail silently
        _ML_MODEL = None
    return _ML_MODEL


def _build_features_for_runtime(
    armor_resists: Dict[str, float],
    stats: Dict[str, Any],
    build_type: str,
) -> List[float]:
    # 1.) Add the armor base stats
    feats: List[float] = [
        float(armor_resists.get("thermal", 0.0)),
        float(armor_resists.get("electrical", 0.0)),
        float(armor_resists.get("chemical", 0.0)),
        float(armor_resists.get("radiation", 0.0)),
        float(armor_resists.get("psi", 0.0)),
        float(armor_resists.get("physical", 0.0)),
    ]

    # Helper to safely get the numeric value from the stat name
    def lvl(name: str) -> float:
        try:
            lvl_val = int(stats.get(name, 0))
        except (TypeError, ValueError):
            lvl_val = 0
        return float(ARTIFACT_BONUS.get(lvl_val, 0))

    # 2.) Add the artifact stats
    feats.extend(
        [
            lvl("thermal_protection"),
            lvl("electrical_protection"),
            lvl("chemical_protection"),
            lvl("physical_protection"),
            lvl("endurance"),
            lvl("increased_durability"),
            lvl("bleeding_resistance"),
            lvl("weight"),
            lvl("radiation"),
            lvl("radio_protection"),
        ]
    )

    # One Hot Encode the desired build type
    bt = (build_type or "").lower()
    feats.extend(
        [
            1.0 if bt == "balanced" else 0.0,
            1.0 if bt == "anomaly protections" else 0.0,
            1.0 if bt == "endurance" else 0.0,
            1.0 if bt == "bleed resistance" else 0.0,
        ]
    )

    return feats

def _ml_score_artifact_for_build(
    artifact: Dict,
    armor_resists: Dict[str, float],
    build_type: str,
) -> float | None:
    # Asks the model to predict how good this artifact is
    model = _get_ml_model()
    if model is None:
        return None

    stats = artifact.get("stats", {}) or {}
    feats = _build_features_for_runtime(armor_resists, stats, build_type)
    try:
        # 0 is used because predict returns a list, but we are only sending 1 item
        pred = model.predict([feats])[0]
        return float(pred)
    except Exception:
        return None

# Convert artifact level into numeric value
def _level_value(level: Any) -> float:
    try:
        lvl = int(level)
    except (TypeError, ValueError):
        return 0.0
    return float(ARTIFACT_BONUS.get(lvl, 0))

# Return armor resistances as floats
def _armor_resists(armor: Dict) -> Dict[str, float]:
    base = armor_resistances(armor)
    return {k: float(v) for k, v in base.items()}


def _protection_score(stats: Dict[str, Any], armor_resists: Dict[str, float]) -> float:
    """
    Calculates the protection score based on armor_resists
    Whatever protection is the lowest,
    we value an artifact with that stat higher
    """
    score = 0.0

    for resist_type, art_keys in PROTECTION_KEYS.items():
        base = armor_resists.get(resist_type, 0.0)
        # Calculate the need (how far from 100 is the stat)
        missing = max(0.0, 100.0 - base)
        # Multiplier (1.0 if full, up to 2.0 if empty)
        importance = 1.0 + (missing / 50.0)

        value = 0.0
        for k in art_keys:
            value = max(value, _level_value(stats.get(k, 0)))

        score += value * importance

    return score

# Score endurance stat
def _endurance_score(stats: Dict[str, Any]) -> float:
    return _level_value(stats.get("endurance", 0))

# Score increased durability stat
def _durability_score(stats: Dict[str, Any]) -> float:
    return _level_value(stats.get("increased_durability", 0))

# Score bleeding resistance stat
def _bleed_score(stats: Dict[str, Any]) -> float:
    return _level_value(stats.get("bleeding_resistance", 0))

# Score weight stat
def _weight_score(stats: Dict[str, Any]) -> float:
    return _level_value(stats.get("weight", 0))

# Radiation penalty after radio protection (0 or negative is good)
def _radiation_penalty(stats: Dict[str, Any]) -> float:
    lvl_rad = int(stats.get("radiation", 0))
    lvl_radio = int(stats.get("radio_protection", 0))

    rad_val = ARTIFACT_BONUS.get(lvl_rad, 0)
    radio_val = ARTIFACT_BONUS.get(lvl_radio, 0)

    return max(0.0, float(rad_val - radio_val))


def _score_artifact_for_build(artifact: Dict, armor_resists: Dict[str, float], build_type: str,) -> Dict[str, float]:
    """
    Heuristic Function:
    Assigns weights (multipliers) to the different stas based on what the user asked for their build.
    Ex: If user wanted an 'Endurance' build, the endurance stat gets a score of 2.0
    """
    stats = artifact.get("stats", {}) or {}

    prot = _protection_score(stats, armor_resists)
    endur = _endurance_score(stats)
    dura = _durability_score(stats)
    bleed = _bleed_score(stats)
    weight = _weight_score(stats)
    rad_pen = _radiation_penalty(stats)

    bt = build_type.lower()
    # Define the weights based on the build type selection
    if bt == "anomaly protections":
        score = (
            2.5 * prot
            + 0.25 * endur
            + 0.25 * dura
            + 0.25 * weight
            - 0.7 * rad_pen
        )
    elif bt == "endurance":
        score = (
            0.8 * prot
            + 2.0 * endur
            + 1.2 * dura
            + 0.7 * weight
            - 0.7 * rad_pen
        )
    elif bt == "bleed resistance":
        score = (
            0.8 * prot
            + 0.5 * endur
            + 0.5 * dura
            + 0.7 * weight
            + 2.0 * bleed
            - 0.7 * rad_pen
        )
    else:
        # Balanced build choice weights
        score = (
            1.3 * prot
            + 1.2 * endur
            + 1.0 * dura
            + 1.0 * bleed
            + 1.0 * weight
            - 0.8 * rad_pen
        )
    # Return breakdown of scores for debugging
    return {
        "score": score,
        "protection_score": prot,
        "endurance_score": endur,
        "durability_score": dura,
        "bleed_score": bleed,
        "weight_score": weight,
        "radiation_penalty": rad_pen,
    }

def _choose_artifacts(armor: Dict, artifacts: List[Dict], slots: int, lead_slots: int, build_type: str,) -> List[Dict]:
    """
    Greedy selection:
    1.) We look at empty slots
    2.) For the current selected slot we test all the artifacts selected
    3.) We pick the artifact that gives the highest boost
    4.) We add the stats, update the stats, and repeat for the next slot
    """
    if slots <= 0 or not artifacts:
        return []

    # Start from base armor resistances
    current_resists = _armor_resists(armor)
    remaining = list(artifacts)
    chosen: List[Dict] = []

    # Loop once for every slot we have available
    for _ in range(min(slots, len(remaining))):
        best_item: Dict | None = None
        best_art: Dict | None = None
        # Starting with negative infinity so any score beats it
        best_score = float("-inf")

        # Test every remaining artifact
        for art in remaining:
            # Get the heuristic score
            scores = _score_artifact_for_build(art, current_resists, build_type)

            # Check if the ML model has a better selection
            ml_val = _ml_score_artifact_for_build(art, current_resists, build_type)
            if ml_val is not None:
                # Use the ML score if available
                scores["score"] = ml_val

            scores["artifact"] = art
            scores["in_lead_container"] = False

            # Is this the best artifact we have seen in the loop?
            if scores["score"] > best_score:
                best_score = scores["score"]
                best_item = scores
                best_art = art

        # If nothing better is seen, stop the loop
        if best_item is None or best_art is None:
            break

        # Lock in the choice for that slot
        chosen.append(best_item)
        remaining.remove(best_art)

        # Update current resistances based on the newly chosen artifact
        current_resists = apply_artifact_resists(current_resists, [best_art])

    # Sort the chosen artifacts by which has the highest Radiation stat
    # Highest Radiation Stat artifacts get placed in the lead containers
    if lead_slots > 0 and chosen:
        by_rad = sorted(chosen, key=lambda x: x["radiation_penalty"], reverse=True)
        for i, item in enumerate(by_rad):
            if i < lead_slots:
                item["in_lead_container"] = True

    return chosen

# Compute final numeric resistances
def _final_resistances(armor: Dict, chosen: List[Dict]) -> Dict[str, int]:
    art_list = [item["artifact"] for item in chosen]
    return apply_artifact_resists(armor_resistances(armor), art_list)

# Compute net radiation only for non-lead container artifacts
def _radiation_balance_nonlead(chosen: List[Dict]) -> int:
    non_lead = [item["artifact"] for item in chosen if not item["in_lead_container"]]
    if not non_lead:
        return 0
    return compute_artifact_radiation_balance(non_lead)

def run_model(
    armor_config: Dict,
    artifacts: List[Dict],
    build_type: str,
) -> Dict[str, Any]:
    # Run optimizer for the selected build
    armor = armor_config.get("armor", {})
    slots = int(armor_config.get("slots_selected", 0))
    lead_slots = int(armor_config.get("lead_containers_selected", 0))

    build_type_clean = (build_type or "Balanced").strip()

    chosen = _choose_artifacts(
        armor=armor,
        artifacts=artifacts,
        slots=slots,
        lead_slots=lead_slots,
        build_type=build_type_clean,
    )

    final_resists = _final_resistances(armor, chosen)
    final_resist_bars = effective_resist_bars(
        armor,
        [item["artifact"] for item in chosen],
    )
    rad_balance = _radiation_balance_nonlead(chosen)

    return {
        "armor": armor,
        "slots": slots,
        "lead_containers": lead_slots,
        "build_type": build_type_clean,
        "chosen_artifacts": chosen,
        "final_resistances": final_resists,
        "final_resistance_bars": final_resist_bars,
        "radiation_balance": rad_balance,
    }
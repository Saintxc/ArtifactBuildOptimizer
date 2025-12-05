from typing import Any, Dict, List
from utils.stats import (ARTIFACT_BONUS, ARTIFACT_TO_ARMOR_STAT, armor_resistances, apply_artifact_resists,
    effective_resist_bars, compute_artifact_radiation_balance)

# Build mapping: armor resistance to artifact stat keys that boost it
PROTECTION_KEYS: Dict[str, List[str]] = {}

for art_key, armor_key in ARTIFACT_TO_ARMOR_STAT.items():
    if armor_key in ("thermal", "electrical", "chemical", "physical"):
        PROTECTION_KEYS.setdefault(armor_key, []).append(art_key)


def _level_value(level: Any) -> float:
    # Convert artifact level into numeric value
    try:
        lvl = int(level)
    except (TypeError, ValueError):
        return 0.0
    return float(ARTIFACT_BONUS.get(lvl, 0))


def _armor_resists(armor: Dict) -> Dict[str, float]:
    # Return armor resistances as floats
    base = armor_resistances(armor)
    return {k: float(v) for k, v in base.items()}


def _protection_score(stats: Dict[str, Any], armor_resists: Dict[str, float]) -> float:
    # Score protections, weighting weak armor resists
    score = 0.0

    for resist_type, art_keys in PROTECTION_KEYS.items():
        base = armor_resists.get(resist_type, 0.0)
        missing = max(0.0, 100.0 - base)
        # 1.0 to 2.0
        importance = 1.0 + (missing / 100.0)

        value = 0.0
        for k in art_keys:
            value = max(value, _level_value(stats.get(k, 0)))

        score += value * importance

    return score


def _endurance_score(stats: Dict[str, Any]) -> float:
    # Score endurance stat
    return _level_value(stats.get("endurance", 0))

def _durability_score(stats: Dict[str, Any]) -> float:
    # Score increased durability stat
    return _level_value(stats.get("increased_durability", 0))

def _bleed_score(stats: Dict[str, Any]) -> float:
    # Score bleeding resistance stat
    return _level_value(stats.get("bleeding_resistance", 0))

def _weight_score(stats: Dict[str, Any]) -> float:
    # Score weight stat
    return _level_value(stats.get("weight", 0))

def _radiation_penalty(stats: Dict[str, Any]) -> float:
    # Radiation penalty after radio protection (0 or negative is good)
    lvl_rad = int(stats.get("radiation", 0))
    lvl_radio = int(stats.get("radio_protection", 0))

    rad_val = ARTIFACT_BONUS.get(lvl_rad, 0)
    radio_val = ARTIFACT_BONUS.get(lvl_radio, 0)

    return max(0.0, float(rad_val - radio_val))

def _score_artifact_for_build(artifact: Dict, armor_resists: Dict[str, float], build_type: str,) -> Dict[str, float]:
    # Score artifact for given build type
    stats = artifact.get("stats", {}) or {}

    prot = _protection_score(stats, armor_resists)
    endur = _endurance_score(stats)
    dura = _durability_score(stats)
    bleed = _bleed_score(stats)
    weight = _weight_score(stats)
    rad_pen = _radiation_penalty(stats)

    bt = build_type.lower()

    if bt == "anomaly protections":
        score = (
            2.0 * prot
            + 0.5 * endur
            + 0.5 * dura
            + 0.5 * weight
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
        # Balanced
        score = (
            1.3 * prot
            + 1.2 * endur
            + 1.0 * dura
            + 1.0 * bleed
            + 1.0 * weight
            - 0.8 * rad_pen
        )

    return {
        "score": score,
        "protection_score": prot,
        "endurance_score": endur,
        "durability_score": dura,
        "bleed_score": bleed,
        "weight_score": weight,
        "radiation_penalty": rad_pen,
    }

def _choose_artifacts(
    armor: Dict,
    artifacts: List[Dict],
    slots: int,
    lead_slots: int,
    build_type: str,
) -> List[Dict]:
    # Choose artifacts for slots / lead containers
    armor_resists = _armor_resists(armor)

    if slots <= 0 or not artifacts:
        return []

    scored: List[Dict] = []

    for art in artifacts:
        scores = _score_artifact_for_build(art, armor_resists, build_type)
        scores["artifact"] = art
        scores["in_lead_container"] = False
        scored.append(scores)

    scored.sort(key=lambda x: x["score"], reverse=True)
    chosen = scored[: min(slots, len(scored))]

    if lead_slots > 0 and chosen:
        by_rad = sorted(chosen, key=lambda x: x["radiation_penalty"], reverse=True)
        for i, item in enumerate(by_rad):
            if i < lead_slots:
                item["in_lead_container"] = True

    return chosen

def _final_resistances(armor: Dict, chosen: List[Dict]) -> Dict[str, int]:
    # Compute final numeric resistances
    art_list = [item["artifact"] for item in chosen]
    return apply_artifact_resists(armor_resistances(armor), art_list)

def _radiation_balance_nonlead(chosen: List[Dict]) -> int:
    # Compute net radiation only for non-lead artifacts
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
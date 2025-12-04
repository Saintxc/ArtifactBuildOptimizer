from typing import Dict, List

# 5-bar armor UI - Each bar = 20
BAR_MAX = 5
BAR_STEP = 20

# Numeric value for artifact stats
ARTIFACT_BONUS: Dict[int, int] = {
    1: 10,
    2: 15,
    3: 20,
    4: 25,
    5: 40,
}

# Artifact stat name to armor resistance name
ARTIFACT_TO_ARMOR_STAT: Dict[str, str] = {
    "chemical_protection": "chemical",
    "psi": "psi",
    "physical_protection": "physical",
    "thermal_protection": "thermal",
    "electrical_protection": "electrical",
}


def value_to_bars(value: int) -> int:
    # Convert 0-100 resistance into 0–5 bars
    bars = value // BAR_STEP
    if bars < 0:
        bars = 0
    if bars > BAR_MAX:
        bars = BAR_MAX
    return bars


def armor_resistances(armor: Dict) -> Dict[str, int]:
    # Return armor resistances as ints
    res = armor.get("resistances", {})
    return {k: int(v) for k, v in res.items()}


def armor_resist_bars(armor: dict) -> dict:
    res = armor.get("resistances", {})
    bars = {}

    for key, value in res.items():
        full = value // 20
        leftover = value % 20
        half = 1 if leftover >= 10 else 0

        total_slots = 5
        empty = total_slots - full - half

        bars[key] = {
            "full": full,
            "half": half,
            "empty": empty,
        }

    return bars


def apply_artifact_resists(base_resists: Dict[str, int],
                           artifacts: List[Dict]) -> Dict[str, int]:
    # Return armor resistances after artifact bonuses
    result = dict(base_resists)

    for art in artifacts:
        stats = art.get("stats", {})
        for art_key, lvl in stats.items():
            armor_key = ARTIFACT_TO_ARMOR_STAT.get(art_key)
            if not armor_key:
                continue

            bonus = ARTIFACT_BONUS.get(int(lvl), 0)
            result[armor_key] = result.get(armor_key, 0) + bonus

    return result


def effective_resist_bars(armor: Dict, artifacts: List[Dict]) -> Dict[str, int]:
    # Return resistance bar counts with artifacts applied
    base = armor_resistances(armor)
    boosted = apply_artifact_resists(base, artifacts)
    return {name: value_to_bars(val) for name, val in boosted.items()}


def compute_artifact_radiation_balance(artifacts: List[Dict]) -> int:
    # Net artifact radiation after radio protection (positive = good / negative = bad)
    total_rad = 0
    total_radio_prot = 0

    for art in artifacts:
        stats = art.get("stats", {})

        lvl_rad = int(stats.get("radiation", 0))
        lvl_radio_prot = int(stats.get("radio_protection", 0))

        total_rad += ARTIFACT_BONUS.get(lvl_rad, 0)
        total_radio_prot += ARTIFACT_BONUS.get(lvl_radio_prot, 0)

    return total_radio_prot - total_rad
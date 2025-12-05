from pathlib import Path
from typing import List, Dict
import joblib
from sklearn.ensemble import RandomForestRegressor
from data.data_client import load_armor_data, load_artifact_data
from utils.abo_model import _score_artifact_for_build, _armor_resists  # reuse teacher
from utils.stats import ARTIFACT_BONUS

BUILD_TYPES = [
    "Balanced",
    "Anomaly Protections",
    "Endurance",
    "Bleed Resistance",
]

def _build_features(armor_resists: Dict[str, float],
                    art_stats: Dict,
                    build_type: str) -> List[float]:
    # armor base
    feats = [
        armor_resists.get("thermal", 0.0),
        armor_resists.get("electrical", 0.0),
        armor_resists.get("chemical", 0.0),
        armor_resists.get("radiation", 0.0),
        armor_resists.get("psi", 0.0),
        armor_resists.get("physical", 0.0),
    ]

    def lvl(name: str) -> float:
        lvl_val = int(art_stats.get(name, 0))
        return float(ARTIFACT_BONUS.get(lvl_val, 0))

    # artifact stats (converted to actual numeric bonuses)
    feats.extend([
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
    ])

    bt = build_type.lower()
    feats.extend([
        1.0 if bt == "balanced" else 0.0,
        1.0 if bt == "anomaly protections" else 0.0,
        1.0 if bt == "endurance" else 0.0,
        1.0 if bt == "bleed resistance" else 0.0,
    ])
    return feats


def main():
    armors = load_armor_data()
    artifacts = load_artifact_data()

    X, y = [], []

    for armor in armors:
        armor_resists = _armor_resists(armor)
        for art in artifacts:
            stats = art.get("stats", {}) or {}
            for bt in BUILD_TYPES:
                feats = _build_features(armor_resists, stats, bt)
                score_info = _score_artifact_for_build(art, armor_resists, bt)
                X.append(feats)
                y.append(score_info["score"])

    model = RandomForestRegressor(
        n_estimators=200,
        random_state=42,
    )
    model.fit(X, y)

    out_path = Path(__file__).resolve().parent / "abo_ml_model.joblib"
    joblib.dump(model, out_path)
    print("Saved model to", out_path)


if __name__ == "__main__":
    main()
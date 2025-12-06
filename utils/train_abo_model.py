from pathlib import Path
from typing import List, Dict
import joblib
from sklearn.ensemble import RandomForestRegressor
from data.data_client import load_armor_data, load_artifact_data
from utils.abo_model import _score_artifact_for_build, _armor_resists
from utils.stats import ARTIFACT_BONUS

BUILD_TYPES = [
    "Balanced",
    "Anomaly Protections",
    "Endurance",
    "Bleed Resistance",
]

def _build_features(armor_resists: Dict[str, float], art_stats: Dict, build_type: str) -> List[float]:
    """
    Feature Engineering:
    Convert the objects (Armor, Artifacts, Desired Build) into flat list of numbers
    that a random forest can understand.
    """

    # 1.) Context: What is the current armor resistances
    feats = [
        armor_resists.get("thermal", 0.0),
        armor_resists.get("electrical", 0.0),
        armor_resists.get("chemical", 0.0),
        armor_resists.get("radiation", 0.0),
        armor_resists.get("psi", 0.0),
        armor_resists.get("physical", 0.0),
    ]

    # Helper to convert 1 into 10.0 (Artifacts used 1-5)
    def lvl(name: str) -> float:
        lvl_val = int(art_stats.get(name, 0))
        return float(ARTIFACT_BONUS.get(lvl_val, 0))

    # 2.) Candidate: What stats does this artifact provide
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

    # Goal: What is the desired build type the user selected (one hot encoding)
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

    # Data generation loop
    # We don't have a dataset of user choices so we have to simulate them.
    # We calculate the right mathematical score for every combination and train the model to approximate that math.
    # In a real app, 'y' would come from user feedback
    for armor in armors:
        armor_resists = _armor_resists(armor)
        for art in artifacts:
            stats = art.get("stats", {}) or {}
            for bt in BUILD_TYPES:
                # X = the input (Armor, Artifacts, and Build choice
                feats = _build_features(armor_resists, stats, bt)
                # y = the target (The calculated heuristic score)
                score_info = _score_artifact_for_build(art, armor_resists, bt)
                X.append(feats)
                y.append(score_info["score"])

    # Model training
    model = RandomForestRegressor(
        # Number of trees
        n_estimators=200,
        # Fixed seed for reproducible results
        random_state=42,
    )
    model.fit(X, y)

    # Save the trained brain to a file so the main app can load it quickly.
    out_path = Path(__file__).resolve().parent / "abo_ml_model.joblib"
    joblib.dump(model, out_path)

if __name__ == "__main__":
    main()
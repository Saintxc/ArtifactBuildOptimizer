import requests


# GitHub Data URL
BASE_URL = "https://raw.githubusercontent.com/Saintxc/ArtifactBuildOptimizerData/main/"

ARMOR_JSON_URL = BASE_URL + "armor.json"
ARTIFACT_JSON_URL = BASE_URL + "artifact.json"
IMAGE_URL = BASE_URL + "images/"

def _fetch_json(url: str, root_key: str):
    # Fetch JSON safely
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        return data.get(root_key, [])
    except Exception as e:
        print(f"Failed to load JSON from {url}: {e}")
        return []

def load_armor_data():
    # Return list of armor with images
    armors = _fetch_json(ARMOR_JSON_URL, "armor")
    for armor in armors:
        rel_path = armor.get("image", "")
        if rel_path:
            armor["image_url"] = IMAGE_URL + rel_path
        else:
            armor["image_url"] = ""
    return armors

def load_artifact_data():
    # Return list of artifacts with images
    artifacts = _fetch_json(ARTIFACT_JSON_URL, "artifacts")
    for art in artifacts:
        rel_path = art.get("image", "")
        if rel_path:
            art["image_url"] = IMAGE_URL + rel_path
        else:
            art["image_url"] = ""
    return artifacts
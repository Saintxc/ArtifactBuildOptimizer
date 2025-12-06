import requests
from PyQt6.QtGui import QPixmap
from PyQt6.QtCore import Qt

def load_pixmap_from_url(url: str, size=(96, 96)) -> QPixmap:
    """
    Downloads an image from the web and converts it to a Qt Pixmap.
    """
    if not url:
        return QPixmap()

    try:
        # Network request
        # Always have a timeout, otherwise the app will hang forever if internet is down.
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()

        # Data conversion
        pixmap = QPixmap()
        pixmap.loadFromData(resp.content)

        # Scaling
        # Scale immediately to save memory and ensure UI consistency
        if size:
            return pixmap.scaled(
                size[0], size[1],
                # Prevent stretching/ distortion
                Qt.AspectRatioMode.KeepAspectRatio,
                # High quality scaling
                Qt.TransformationMode.SmoothTransformation
            )

        return pixmap

    except Exception:
        # Failing gracefully:
        # If image fails to load, just return an empty pixmap
        # Prevents the whole app from crashing just because an icon is missing.
        return QPixmap()
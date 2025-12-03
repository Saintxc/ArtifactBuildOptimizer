import requests
from PyQt6.QtGui import QPixmap
from PyQt6.QtCore import Qt

def load_pixmap_from_url(url: str, size=(96, 96)) -> QPixmap:
    if not url:
        return QPixmap()

    try:
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()

        pixmap = QPixmap()
        pixmap.loadFromData(resp.content)

        if size:
            return pixmap.scaled(
                size[0], size[1],
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )

        return pixmap

    except Exception:
        return QPixmap()
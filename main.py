import sys
from pathlib import Path
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QLabel, QListWidget, QVBoxLayout)
from PyQt6.QtGui import QPixmap
from PyQt6.QtCore import Qt
import requests

# Data paths
BASE_DIR = Path(__file__).resolve().parent
RES_DIR = BASE_DIR / "resources" / "images"
PDA_BACKGROUND = RES_DIR / "ABO_PDA.png"

# GitHub JSON URL
ARMOR_JSON_URL = "https://raw.githubusercontent.com/Saintxc/ArtifactBuildOptimizerData/main/armor.json"

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        # Window setup
        self.setWindowTitle("Artifact Build Optimizer - PoC")
        self.setFixedSize(1600, 900)

        # PDA background image
        self._setup_background()

        # Foreground UI (inside screen area)
        central = QWidget(self)
        central.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setCentralWidget(central)

        layout = QVBoxLayout(central)

        # Screen area
        layout.setContentsMargins(105, 105, 225, 110)

        title = QLabel("Armor Selection")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("color: white; font-size: 22px; font-weight: bold;")

        self.armor_list = QListWidget()
        self.armor_list.setStyleSheet(
            """
            QListWidget {
                background-color: rgba(0, 0, 0, 120);
                color: white;
                font-size: 16px;
            }
            QListWidget::item:selected {
                background-color: rgba(255, 255, 255, 60);
            }
            """
        )

        layout.addWidget(title)
        layout.addWidget(self.armor_list)

        # Load data from JSON
        self.load_armor_data()

    # Helper methods

    def _setup_background(self):
        # Create a window QLabel with the PDA image
        bg_label = QLabel(self)
        pixmap = QPixmap(str(PDA_BACKGROUND))

        # Set the image
        bg_label.setPixmap(pixmap)
        bg_label.setScaledContents(True)

        # Match window size
        bg_label.setGeometry(0, 0, 1600, 900)
        bg_label.lower()

    def load_armor_data(self):
        # Load JSON from the GitHub repo
        try:
            response = requests.get(ARMOR_JSON_URL, timeout=10)
            response.raise_for_status()
            data = response.json()
        except Exception as e:
            print(f"Failed to load armor data: {e}")
            self.armor_list.addItem("Error loading armor data")
            return

        for armor in data["armor"]:
            name = armor["name"]
            slots = armor["slots_base"]
            pos_slots = armor["slots_total"]
            containers = armor["lead_containers_total"]
            display_text = f"{name}  |  Base Slots: {slots} - Possible Slots: {pos_slots}  |  Possible Lead Containers: {containers}"
            self.armor_list.addItem(display_text)


def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
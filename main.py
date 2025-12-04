import sys
from pathlib import Path
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QLabel, QStackedWidget)
from data.data_client import load_armor_data, load_artifact_data
from views.armor_selection_view import ArmorSelectionView
from views.armor_config_view import ArmorConfigView
from views.artifact_selection_view import ArtifactSelectionView
from views.build_results_view import BuildResultsView


BASE_DIR = Path(__file__).resolve().parent
RES_DIR = BASE_DIR / "resources" / "images"
PDA_BACKGROUND = RES_DIR / "ABO_PDA.png"


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Artifact Build Optimizer")
        self.setFixedSize(1600, 900)

        self._setup_background()

        # App area set within the screen of the PDA image
        central = QWidget(self)
        central.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setCentralWidget(central)

        central_layout = QVBoxLayout(central)
        central_layout.setContentsMargins(105, 105, 225, 110)
        central_layout.setSpacing(0)

        self.stack = QStackedWidget()
        central_layout.addWidget(self.stack)

        # Load data
        armors = load_armor_data()
        artifacts = load_artifact_data()

        # Views we have from the start
        self.armor_selection_view = ArmorSelectionView(armors)
        self.armor_config_view: ArmorConfigView | None = None
        self.artifact_selection_view = ArtifactSelectionView(artifacts)
        self.build_results_view = BuildResultsView()

        # Add the views to the stack
        self.stack.addWidget(self.armor_selection_view)
        self.stack.addWidget(self.artifact_selection_view)
        self.stack.addWidget(self.build_results_view)

        # Start on armor selection
        self.stack.setCurrentWidget(self.armor_selection_view)

        # Wire signals
        self.armor_selection_view.next_requested.connect(self._on_armor_chosen)
        self.artifact_selection_view.back_requested.connect(self._show_armor_config)

    # Background
    def _setup_background(self):
        bg_label = QLabel(self)
        pixmap = QPixmap(str(PDA_BACKGROUND))
        if not pixmap.isNull():
            bg_label.setPixmap(pixmap)
            bg_label.setScaledContents(True)
            bg_label.setGeometry(0, 0, 1600, 900)
            bg_label.lower()

    # Navigation
    def _on_armor_chosen(self, armor_dict: dict):
        # If we already had a config view from a previous selection remove and delete it
        if self.armor_config_view is not None:
            self.stack.removeWidget(self.armor_config_view)
            self.armor_config_view.deleteLater()

        # Create a new config view for this armor
        self.armor_config_view = ArmorConfigView(armor_dict)
        self.armor_config_view.back_requested.connect(self._show_armor_selection)
        self.armor_config_view.next_requested.connect(self._on_armor_config_done)

        # Put it into the stack and switch to it
        self.stack.addWidget(self.armor_config_view)
        self.stack.setCurrentWidget(self.armor_config_view)

    def _show_armor_selection(self):
        # Back button on config sends you back to armor selection
        self.stack.setCurrentWidget(self.armor_selection_view)

    def _show_armor_config(self):
        # Back button on artifacts sends you back to config
        if self.armor_config_view is not None:
            self.stack.setCurrentWidget(self.armor_config_view)

    def _on_armor_config_done(self, armor_config: dict):
        armor = armor_config["armor"]
        slots = armor_config["slots_selected"]
        containers = armor_config["lead_containers_selected"]
        self.artifact_selection_view.set_context(armor, slots, containers)
        self.stack.setCurrentWidget(self.artifact_selection_view)


def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
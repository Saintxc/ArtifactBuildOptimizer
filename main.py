import sys
from pathlib import Path
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QLabel, QStackedWidget)
from data.data_client import load_armor_data, load_artifact_data
from views.armor_selection_view import ArmorSelectionView
from views.armor_config_view import ArmorConfigView
from views.artifact_selection_view import ArtifactSelectionView
from views.artifact_config_view import ArtifactConfigView
from views.build_results_view import BuildResultsView
from utils.abo_model import run_model


# Where our files live so image can load reliably
BASE_DIR = Path(__file__).resolve().parent
RES_DIR = BASE_DIR / "resources" / "images"
PDA_BACKGROUND = RES_DIR / "ABO_PDA.png"


class MainWindow(QMainWindow):
    """
    Main window class acts as the controller. It manages the data and
    decides which screen is currently visible to the user.
    """
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Artifact Build Optimizer")
        self.setFixedSize(1600, 900)

        # 1.) Set the background as the PDA Image
        self._setup_background()

        # 2.) Central container
        # Transparent so background image shows through giving PDA theme.
        central = QWidget(self)
        central.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setCentralWidget(central)

        # 3.) Layout configuration
        # Margins are the screen area of the image
        central_layout = QVBoxLayout(central)
        central_layout.setContentsMargins(105, 105, 225, 110)
        central_layout.setSpacing(0)

        # 4.) Stacked Widget
        # Only top card is visible, screens (views) are stacked here but only one is shown.
        self.stack = QStackedWidget()
        central_layout.addWidget(self.stack)

        # 5.) Load data (Armor and Artifacts)
        armors = load_armor_data()
        artifacts = load_artifact_data()

        # Saves users armor configuration while artifacts are selected
        self._armor_config: dict | None = None

        # 6.) Initialize views
        # Create instances of the screens and pass the data they need to function
        self.armor_selection_view = ArmorSelectionView(armors)
        self.armor_config_view: ArmorConfigView | None = None
        self.artifact_selection_view = ArtifactSelectionView(artifacts)
        self.artifact_config_view = ArtifactConfigView()
        self.build_results_view = BuildResultsView()

        # Add the views to the stack
        self.stack.addWidget(self.armor_selection_view)
        self.stack.addWidget(self.artifact_selection_view)
        self.stack.addWidget(self.artifact_config_view)
        self.stack.addWidget(self.build_results_view)

        # Start on armor selection
        self.stack.setCurrentWidget(self.armor_selection_view)

        # 7.) Signal wiring
        # This is how the screens talk to the main window
        # When view says next/ back_ requested, we run that function to change the screens
        self.armor_selection_view.next_requested.connect(self._on_armor_chosen)
        self.artifact_selection_view.back_requested.connect(self._show_armor_config)
        self.artifact_selection_view.next_requested.connect(self._on_artifact_selection_done)
        self.artifact_config_view.next_requested.connect(self._on_artifact_config_done)
        self.artifact_config_view.back_requested.connect(self._show_armor_config)
        self.build_results_view.back_requested.connect(self._show_artifact_config)

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
        # If a config view exists from a previous instance of the app, destroy it and reset the state
        if self.armor_config_view is not None:
            self.stack.removeWidget(self.armor_config_view)
            self.armor_config_view.deleteLater()

        # Create a new config view for the armor that was selected
        self.armor_config_view = ArmorConfigView(armor_dict)
        # Wire the new view's signals
        self.armor_config_view.back_requested.connect(self._show_armor_selection)
        self.armor_config_view.next_requested.connect(self._on_armor_config_done)

        # Add it to the stack and show it
        self.stack.addWidget(self.armor_config_view)
        self.stack.setCurrentWidget(self.armor_config_view)

    # Back button on Armor Config sends you back to Armor Selection
    def _show_armor_selection(self):
        self.stack.setCurrentWidget(self.armor_selection_view)

    # Back button on Artifact Selection sends you back to Armor Config
    def _show_armor_config(self):
        if self.armor_config_view is not None:
            self.stack.setCurrentWidget(self.armor_config_view)

    # Back button on Results sends you back to Artifact Configuration
    def _show_artifact_config(self):
        self.stack.setCurrentWidget(self.artifact_config_view)

    # Called when user finishes configuring their armor selection
    def _on_armor_config_done(self, armor_config: dict):
        self._armor_config = armor_config
        # Data that is extracted and used in the next screens
        armor = armor_config["armor"]
        slots = armor_config["slots_selected"]
        containers = armor_config["lead_containers_selected"]
        # Pass the extracted data to the artifact selection so it knows the limits
        self.artifact_selection_view.set_context(armor, slots, containers)
        self.stack.setCurrentWidget(self.artifact_selection_view)

    # Called when user finishes selecting their artifacts
    def _on_artifact_selection_done(self, selected_artifacts: list[dict]):
        if self._armor_config is None:
            return
        # Pass the data (armor and selected artifacts) on to the artifact configuration screen
        self.artifact_config_view.set_context(self._armor_config, selected_artifacts)
        self.stack.setCurrentWidget(self.artifact_config_view)

    # Run model and show build results
    def _on_artifact_config_done(self, payload: dict):
        result = run_model(
            armor_config=payload["armor_config"],
            artifacts=payload["artifacts"],
            build_type=payload["build_type"],
        )
        self.build_results_view.set_context(result)
        self.stack.setCurrentWidget(self.build_results_view)


def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
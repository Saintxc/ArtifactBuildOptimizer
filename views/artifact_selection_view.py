from typing import List, Dict, Optional
from PyQt6.QtCore import Qt, pyqtSignal, QSize
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QScrollArea, QGridLayout, QToolButton,)
from utils.image_loader import load_pixmap_from_url


class ArtifactSelectionView(QWidget):
    # Select artifacts
    back_requested = pyqtSignal()
    next_requested = pyqtSignal(list)

    def __init__(self, artifacts: List[Dict], parent: Optional[QWidget] = None):
        super().__init__(parent)
        self._artifacts = artifacts
        self._armor: Optional[Dict] = None
        self._slots: int = 0
        self._containers: int = 0
        self._buttons: List[QToolButton] = []

        self._build_ui()

    def set_context(self, armor: Dict, slots: int, containers: int):
        # Store armor configuration
        self._armor = armor
        self._slots = slots
        self._containers = containers

    def _build_ui(self):
        # Build main artifact selection layout
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(40, 40, 40, 40)
        root_layout.setSpacing(16)

        # Title
        title = QLabel("Artifact Selection")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("color: white; font-size: 22px; font-weight: bold;")
        root_layout.addWidget(title)

        # Scroll area with artifacts grid
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameStyle(0)
        scroll.setStyleSheet(
            """
            QScrollArea {
                background: transparent;
                border: none;
            }
            QScrollArea > QWidget > QWidget {
                background: transparent;
            }
            QScrollBar:vertical {
                background: transparent;
                width: 12px;
                margin: 2px;
            }
            """
        )

        container = QWidget()
        grid = QGridLayout(container)
        grid.setContentsMargins(0, 8, 0, 8)
        grid.setHorizontalSpacing(16)
        grid.setVerticalSpacing(16)

        columns = 6
        for index, art in enumerate(self._artifacts):
            row = index // columns
            col = index % columns

            btn = QToolButton()
            btn.setCheckable(True)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextUnderIcon)
            btn.setMinimumSize(140, 140)

            name = art.get("name", "Artifact")
            btn.setText(name)

            pixmap = load_pixmap_from_url(art.get("image_url", ""), size=(80, 80))
            if not pixmap.isNull():
                btn.setIcon(QIcon(pixmap))
                btn.setIconSize(QSize(80, 80))

            btn.setStyleSheet(self._button_stylesheet(False))
            btn.toggled.connect(self._on_artifact_toggled)

            btn.artifact_data = art
            self._buttons.append(btn)
            grid.addWidget(btn, row, col)

        scroll.setWidget(container)
        root_layout.addWidget(scroll, stretch=1)

        # Bottom bar with Back/ CA/ SA/ Next
        bottom_bar = QHBoxLayout()
        bottom_bar.setSpacing(16)

        # Back
        back_btn = QPushButton("Back")
        back_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        back_btn.clicked.connect(self._on_back_clicked)
        back_btn.setStyleSheet(
            """
            QPushButton {
                background-color: rgba(0, 0, 0, 160);
                color: white;
                padding: 8px 20px;
                border-radius: 6px;
                border: 1px solid rgba(255, 255, 255, 80);
                font-weight: bold;
            }
            QPushButton:hover { background-color: rgba(60, 60, 60, 200); }
            """
        )
        bottom_bar.addWidget(back_btn)

        bottom_bar.addStretch(1)

        # Center buttons: Selected count/ Clear All/ Select All
        self.selected_label = QLabel("Selected: 0")
        self.selected_label.setStyleSheet("color: white; font-size: 14px;")
        bottom_bar.addWidget(self.selected_label)

        clear_btn = QPushButton("Clear All")
        clear_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        clear_btn.clicked.connect(self._on_clear_all)
        clear_btn.setStyleSheet(
            """
            QPushButton {
                background-color: rgba(0, 0, 0, 160);
                color: white;
                padding: 6px 16px;
                border-radius: 6px;
                border: 1px solid rgba(255, 255, 255, 80);
                font-weight: bold;
            }
            QPushButton:hover { background-color: rgba(60, 60, 60, 200); }
            """
        )
        bottom_bar.addWidget(clear_btn)

        select_all_btn = QPushButton("Select All")
        select_all_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        select_all_btn.clicked.connect(self._on_select_all)
        select_all_btn.setStyleSheet(
            """
            QPushButton {
                background-color: #2e8b57;
                color: white;
                padding: 6px 16px;
                border-radius: 6px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #3aa96b; }
            """
        )
        bottom_bar.addWidget(select_all_btn)

        bottom_bar.addStretch(1)

        # Next
        next_btn = QPushButton("Next")
        next_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        next_btn.clicked.connect(self._on_next_clicked)
        next_btn.setStyleSheet(
            """
            QPushButton {
                background-color: #2e8b57;
                color: white;
                padding: 8px 24px;
                border-radius: 6px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #3aa96b; }
            """
        )
        bottom_bar.addWidget(next_btn)

        root_layout.addLayout(bottom_bar)

    @staticmethod
    def _button_stylesheet(selected: bool) -> str:
        bg = "rgba(0, 0, 0, 160)" if not selected else "#2ecc71"
        border = "1px solid #000000" if not selected else "2px solid #a5f7b8"
        text = "white" if not selected else "black"
        return f"""
            QToolButton {{
                text-align: center;
                color: {text};
                background-color: {bg};
                border: {border};
                border-radius: 6px;
                padding: 8px 6px 6px 6px;
                font-size: 13px;
            }}
        """

    def _update_selected_label(self):
        # Refresh selected amount value
        count = sum(1 for b in self._buttons if b.isChecked())
        self.selected_label.setText(f"Selected: {count}")

    def _on_artifact_toggled(self, checked: bool):
        # Update visuals and selected count
        btn = self.sender()
        if isinstance(btn, QToolButton):
            btn.setStyleSheet(self._button_stylesheet(checked))
        self._update_selected_label()

    def _on_clear_all(self):
        # Deselect all artifacts
        for btn in self._buttons:
            btn.setChecked(False)
        self._update_selected_label()

    def _on_select_all(self):
        # Select all artifacts
        for btn in self._buttons:
            btn.setChecked(True)
        self._update_selected_label()

    def _on_back_clicked(self):
        # Go back to armor config
        self.back_requested.emit()

    def _on_next_clicked(self):
        # Emit selected artifact list
        selected = [b.artifact_data for b in self._buttons if b.isChecked()]
        self.next_requested.emit(selected)
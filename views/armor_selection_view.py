from typing import List, Dict, Optional
from PyQt6.QtCore import Qt, pyqtSignal, QSize
from PyQt6.QtGui import QPixmap, QIcon
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QScrollArea,QGridLayout, QButtonGroup, QToolButton)
from utils.image_loader import load_pixmap_from_url


class ArmorSelectionView(QWidget):
    next_requested = pyqtSignal(dict)

    def __init__(self, armors: List[Dict], parent: Optional[QWidget] = None):
        super().__init__(parent)
        self._armors = armors
        self._selected_armor: Optional[Dict] = None

        self._build_ui()

    # UI setup
    def _build_ui(self):
        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(16)

        # 1.) Title label
        title = QLabel("Armor Selection")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("color: white; font-size: 22px; font-weight: bold;")
        root_layout.addWidget(title)

        # 2.) Scroll area with grid of armor buttons since there are too many to list within the small screen
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameStyle(0)

        # Make scroll area transparent so it blends with the PDA screen
        scroll.setStyleSheet("""
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
        """)

        # Container inside the scroll area that holds the armor grid
        scroll_container = QWidget()
        grid = QGridLayout(scroll_container)
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setHorizontalSpacing(16)
        grid.setVerticalSpacing(16)

        # Ensures only 1 armor can be selected at a time
        self._button_group = QButtonGroup(self)
        self._button_group.setExclusive(True)
        self._button_group.buttonClicked.connect(self._on_button_clicked)

        # Build grid
        columns = 4
        for index, armor in enumerate(self._armors):
            row = index // columns
            col = index % columns

            btn = QToolButton()
            btn.setCheckable(True)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)

            # Put text under armor
            btn.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextUnderIcon)
            btn.setMinimumSize(230, 220)

            # Set the data
            name = armor.get("name", "Unknown Armor")
            btn.setText(name)
            btn.setStyleSheet(self._button_stylesheet(selected=False))

            # Load the icon
            pixmap = load_pixmap_from_url(armor.get("image_url", ""), size=(150, 150))
            if not pixmap.isNull():
                icon = QIcon(pixmap)
                btn.setIcon(icon)
                btn.setIconSize(QSize(150, 150))

            # Keep a reference to the armor selected
            btn.armor_data = armor

            self._button_group.addButton(btn)
            grid.addWidget(btn, row, col)

        scroll.setWidget(scroll_container)
        root_layout.addWidget(scroll, stretch=1)

        # Bottom bar with navigation buttons
        bottom_bar = QHBoxLayout()
        bottom_bar.addStretch(1)

        self.next_button = QPushButton("Next")
        self.next_button.setEnabled(False)
        self.next_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.next_button.clicked.connect(self._on_next_clicked)
        self.next_button.setStyleSheet(
            """
            QPushButton {
                background-color: #2e8b57;
                color: white;
                padding: 8px 20px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:disabled {
                background-color: #555555;
                color: #aaaaaa;
            }
            QPushButton:hover:!disabled {
                background-color: #3aa96b;
            }
            """
        )

        bottom_bar.addWidget(self.next_button)
        root_layout.addLayout(bottom_bar)

    # Styling helpers
    @staticmethod
    def _button_stylesheet(selected: bool) -> str:
        base_border = "2px solid #ffffff" if selected else "1px solid #000000"
        bg_color = "rgba(0, 0, 0, 160)" if selected else "rgba(0, 0, 0, 110)"
        return f"""
            QToolButton {{
                text-align: center;
                color: white;
                background-color: {bg_color};
                border: {base_border};
                border-radius: 6px;
                padding: 8px 6px 6px 6px;
                font-size: 14px;
            }}
            QToolButton:checked {{
                background-color: #2ecc71;
                border: 2px solid #a5f7b8;
                color: black;
            }}
        """

    # Interation slots
    # Called when any armor is clicked
    def _on_button_clicked(self, button: QPushButton):
        # Retrieve the data we attached earlier
        self._selected_armor = getattr(button, "armor_data", None)
        # Enable the next button since an armor has been selected
        self.next_button.setEnabled(self._selected_armor is not None)

        # Force a style refresh so the green border appears correctly
        for btn in self._button_group.buttons():
            btn.setStyleSheet(self._button_stylesheet(selected=btn is button))

    # Broadcast the selected armor to the main window
    def _on_next_clicked(self):
        if self._selected_armor is None:
            return
        self.next_requested.emit(self._selected_armor)
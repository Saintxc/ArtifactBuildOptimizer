from typing import Dict, Optional
from PyQt6.QtCore import Qt, pyqtSignal, QSize
from PyQt6.QtWidgets import (QWidget,  QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QComboBox, QFrame)
from utils.image_loader import load_pixmap_from_url
from utils.stats import armor_resist_bars


class ArmorConfigView(QWidget):
    """
    This view handles the form part of the app.
    The user has picked an armor and needs to configure it to their armor in game
    Ex. How many artifact slots you have/ how many lead containers do you have?
    """
    back_requested = pyqtSignal()
    next_requested = pyqtSignal(dict)

    def __init__(self, armor: Dict, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self._armor = armor

        # Parse the data safely using .get
        self._slots_base = int(armor.get("slots_base", 0))
        self._slots_total = int(armor.get("slots_total", self._slots_base))

        self._lead_base = int(armor.get("lead_containers_base", 0))
        self._lead_total = int(armor.get("lead_containers_total", self._lead_base))

        # Pre-calculate the bar visuals for the resistances from the base stats
        self._base_bar_values = armor_resist_bars(armor)

        self._build_ui()

    def _build_ui(self):
        # Allow background PDA image to show through
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        # Root layout is the main vertical stack
        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(40, 40, 40, 40)
        root_layout.setSpacing(24)

        # Title
        title = QLabel("Armor Configuration")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("color: white; font-size: 22px; font-weight: bold;")
        root_layout.addWidget(title)

        # Main content row split horizontally
        # Left side: Armor Card
        # Right side: Configuration controls
        content_row = QHBoxLayout()
        content_row.setSpacing(80)
        root_layout.addLayout(content_row, stretch=1)

        # Left side: Armor card created using QFrame
        armor_card = QFrame()
        armor_card.setObjectName("armorCard")
        armor_card.setFixedSize(260, 320)
        armor_card.setStyleSheet(
            """
            QFrame#armorCard {
                background-color: rgba(0, 0, 0, 140);
                border-radius: 18px;
                border: 1px solid rgba(255, 255, 255, 60);
            }
        """
        )

        armor_card_layout = QVBoxLayout(armor_card)
        armor_card_layout.setContentsMargins(16, 16, 16, 16)
        armor_card_layout.setSpacing(12)
        armor_card_layout.setAlignment(
            Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignHCenter
        )

        # Image handling
        img_label = QLabel()
        img_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        pixmap = load_pixmap_from_url(self._armor.get("image_url", ""), size=(180, 180))
        if not pixmap.isNull():
            img_label.setPixmap(pixmap)
        armor_card_layout.addWidget(img_label)

        name_label = QLabel(self._armor.get("name", "Unknown Armor"))
        name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        name_label.setStyleSheet("color: white; font-size: 18px; font-weight: bold;")
        armor_card_layout.addWidget(name_label)

        content_row.addWidget(armor_card)

        # Right side: Configuration Controls
        controls_col = QVBoxLayout()
        controls_col.setSpacing(20)
        controls_col.addStretch(1)

        # Input 1: Artifact Slots
        slots_row = QHBoxLayout()
        slots_row.setSpacing(12)
        slots_row.setAlignment(Qt.AlignmentFlag.AlignLeft)

        slots_label = QLabel("Artifact Slots:")
        slots_label.setStyleSheet("color: white; font-size: 18px; font-weight: bold;")
        slots_row.addWidget(slots_label)

        self.slots_combo = QComboBox()
        self.slots_combo.setFixedWidth(140)
        self.slots_combo.setStyleSheet(
            """
            QComboBox {
                background-color: rgba(0, 0, 0, 160);
                color: white;
                border-radius: 8px;
                padding: 4px 8px;
                padding-right: 24px;
                border: 1px solid rgba(255, 255, 255, 80);
                font-size: 18px;
            }
            QComboBox::drop-down {
                width: 35px;
                border: 0px;
            }
            """
        )

        # Populate the dropdown options based on the range of valid slots
        # Start from base amount and go up to the maximum upgrades
        for val in range(self._slots_base, self._slots_total + 1):
            self.slots_combo.addItem(str(val), val)

        # Start at the base amount by default
        idx = self.slots_combo.findData(self._slots_base)
        if idx >= 0:
            self.slots_combo.setCurrentIndex(idx)

        slots_row.addWidget(self.slots_combo)
        slots_row.addStretch(1)
        controls_col.addLayout(slots_row)

        # Input 2: Lead Containers (same logic as the artifact slots above)
        lead_row = QHBoxLayout()
        lead_row.setSpacing(12)
        lead_row.setAlignment(Qt.AlignmentFlag.AlignLeft)

        lead_label = QLabel("Lead Containers:")
        lead_label.setStyleSheet("color: white; font-size: 18px; font-weight: bold;")
        lead_row.addWidget(lead_label)

        self.lead_combo = QComboBox()
        self.lead_combo.setFixedWidth(140)
        self.lead_combo.setStyleSheet(
            """
            QComboBox {
                background-color: rgba(0, 0, 0, 160);
                color: white;
                border-radius: 8px;
                padding: 4px 8px;
                padding-right: 24px;
                border: 1px solid rgba(255, 255, 255, 80);
                font-size: 18px;
            }
            QComboBox::drop-down {
                width: 35px;
                border: 0px;
            }
            """
        )

        for val in range(self._lead_base, self._lead_total + 1):
            self.lead_combo.addItem(str(val), val)

        idx = self.lead_combo.findData(self._lead_base)
        if idx >= 0:
            self.lead_combo.setCurrentIndex(idx)

        lead_row.addWidget(self.lead_combo)
        lead_row.addStretch(1)
        controls_col.addLayout(lead_row)

        # Shows the base resistances in form of bars so the user knows
        res_title = QLabel("Base Resistances (No Upgrades)")
        res_title.setStyleSheet("color: white; font-size: 24px; font-weight: bold; text-decoration: underline;")
        controls_col.addWidget(res_title)
        stat_order = [
            ("thermal", "Thermal"),
            ("electrical", "Electrical"),
            ("chemical", "Chemical"),
            ("radiation", "Radiation"),
            ("psi", "Psi"),
            ("physical", "Physical"),
        ]

        for key, label_text in stat_order:
            bars = self._base_bar_values.get(key, 0)

            row = QHBoxLayout()
            row.setSpacing(8)
            row.setAlignment(Qt.AlignmentFlag.AlignLeft)

            stat_label = QLabel(f"{label_text}:")
            stat_label.setStyleSheet("color: white; font-size: 16px; font-weight: bold;")
            row.addWidget(stat_label)

            # Generate the visual bar widgets
            row.addLayout(self._create_bar_row(bars))
            row.addStretch(1)

            controls_col.addLayout(row)

        controls_col.addStretch(2)
        content_row.addLayout(controls_col, stretch=1)

        # Bottom navigation buttons (Back/ Next)
        bottom_bar = QHBoxLayout()
        bottom_bar.setSpacing(16)

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

    # Helper to create the 5 resistance bars
    def _create_bar_row(self, bar_info: dict):
        layout = QHBoxLayout()
        layout.setSpacing(4)

        full = bar_info.get("full", 0)
        half = bar_info.get("half", 0)

        total_bars = 5
        bar_width = 30
        bar_height = 10

        # Loop 5 times to create the 5 bars
        for i in range(total_bars):
            # Outer empty bar
            container = QFrame()
            container.setFixedSize(bar_width, bar_height)
            container.setStyleSheet(
                "background-color: rgba(255, 255, 255, 40); border-radius: 3px;"
            )

            fill_width = 0
            if i < full:
                # Full bar
                fill_width = bar_width
            elif i == full and half:
                # Half bar
                fill_width = bar_width // 2
            # Inner green fill
            if fill_width > 0:
                filled = QFrame(container)
                filled.setGeometry(0, 0, fill_width, bar_height)
                filled.setStyleSheet(
                    "background-color: #2ecc71; border-radius: 3px;"
                )

            layout.addWidget(container)

        return layout

    # Takes user back to armor selection
    def _on_back_clicked(self):
        self.back_requested.emit()

    # Gathers all the data from the configuration into a dictionary
    # Passes on to the next step
    def _on_next_clicked(self):
        armor_config = {
            "armor": self._armor,
            "slots_selected": int(self.slots_combo.currentData()),
            "lead_containers_selected": int(self.lead_combo.currentData()),
        }
        self.next_requested.emit(armor_config)
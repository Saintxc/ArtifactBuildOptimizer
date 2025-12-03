from typing import Dict, Optional
from PyQt6.QtCore import Qt, pyqtSignal, QSize
from PyQt6.QtWidgets import (QWidget,  QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QComboBox, QFrame)
from utils.image_loader import load_pixmap_from_url
from utils.stats import armor_resist_bars


class ArmorConfigView(QWidget):
    # Configure artifact slots and lead containers
    back_requested = pyqtSignal()
    next_requested = pyqtSignal(dict)

    def __init__(self, armor: Dict, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self._armor = armor

        self._slots_base = int(armor.get("slots_base", 0))
        self._slots_total = int(armor.get("slots_total", self._slots_base))

        self._lead_base = int(armor.get("lead_containers_base", 0))
        self._lead_total = int(armor.get("lead_containers_total", self._lead_base))

        self._base_bar_values = armor_resist_bars(armor)

        self._build_ui()

    def _build_ui(self):
        # Build main config layout
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(40, 40, 40, 40)
        root_layout.setSpacing(24)

        # Title
        title = QLabel("Armor Configuration")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("color: white; font-size: 22px; font-weight: bold;")
        root_layout.addWidget(title)

        # Main content row (left armor card / right values)
        content_row = QHBoxLayout()
        content_row.setSpacing(80)
        root_layout.addLayout(content_row, stretch=1)

        # Armor card
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

        # Controls column
        controls_col = QVBoxLayout()
        controls_col.setSpacing(20)

        # Center controls vertically
        controls_col.addStretch(1)

        # Artifact Slots row
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

        for val in range(self._slots_base, self._slots_total + 1):
            self.slots_combo.addItem(str(val), val)

        idx = self.slots_combo.findData(self._slots_base)
        if idx >= 0:
            self.slots_combo.setCurrentIndex(idx)

        slots_row.addWidget(self.slots_combo)
        slots_row.addStretch(1)
        controls_col.addLayout(slots_row)

        # Lead Containers row
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

        # Base resistance bars
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

            row.addLayout(self._create_bar_row(bars))
            row.addStretch(1)

            controls_col.addLayout(row)

        # Centered vertically
        controls_col.addStretch(2)
        content_row.addLayout(controls_col, stretch=1)

        # Bottom buttons
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

    def _create_bar_row(self, filled_count: int):
        # Create one horizontal resistance bar row
        layout = QHBoxLayout()
        layout.setSpacing(4)

        for i in range(5):
            bar = QFrame()
            bar.setFixedSize(22, 10)
            color = "#2ecc71" if i < filled_count else "rgba(255, 255, 255, 40)"
            bar.setStyleSheet(
                f"background-color: {color}; border-radius: 3px;"
            )
            layout.addWidget(bar)

        return layout

    def _on_back_clicked(self):
        # Emit back navigation
        self.back_requested.emit()

    def _on_next_clicked(self):
        # Emit selected config values
        armor_config = {
            "armor": self._armor,
            "slots_selected": int(self.slots_combo.currentData()),
            "lead_containers_selected": int(self.lead_combo.currentData()),
        }
        self.next_requested.emit(armor_config)
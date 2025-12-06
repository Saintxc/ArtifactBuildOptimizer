from typing import Dict, List, Optional
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QComboBox, QFrame, QScrollArea, QGridLayout)
from utils.image_loader import load_pixmap_from_url
from utils.stats import armor_resist_bars


class ArtifactConfigView(QWidget):
    """
    Final Step:
    The user defines what their build goal is
    """
    back_requested = pyqtSignal()
    next_requested = pyqtSignal(dict)

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)

        self._armor: Optional[Dict] = None
        self._armor_config: Optional[Dict] = None
        self._selected_artifacts: List[Dict] = []
        self._base_bar_values: Dict[str, Dict[str, int]] = {}

        self._armor_image_label: QLabel | None = None
        self._armor_name_label: QLabel | None = None
        self._bars_container: QVBoxLayout | None = None
        self._artifacts_grid: QGridLayout | None = None
        self._build_type_combo: QComboBox | None = None

        self._build_ui()

    # Store armor config and artifacts
    def set_context(self, armor_config: Dict, artifacts: List[Dict]):
        self._armor_config = armor_config
        self._armor = armor_config["armor"]
        self._selected_artifacts = artifacts
        self._base_bar_values = armor_resist_bars(self._armor)

        self._refresh_armor_card()
        self._refresh_resistance_rows()
        self._refresh_artifacts()

    # Build main layout (similar to other screens)
    def _build_ui(self):
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        root = QVBoxLayout(self)
        root.setContentsMargins(40, 40, 40, 20)
        root.setSpacing(24)

        title = QLabel("Artifact Configuration")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("color: white; font-size: 22px; font-weight: bold;")
        root.addWidget(title)

        main_row = QHBoxLayout()
        main_row.setSpacing(80)
        root.addLayout(main_row, stretch=1)

        # Armor card
        armor_card = QFrame()
        armor_card.setObjectName("artifactArmorCard")
        armor_card.setFixedSize(260, 320)
        armor_card.setStyleSheet(
            """
            QFrame#artifactArmorCard {
                background-color: rgba(0, 0, 0, 140);
                border-radius: 18px;
                border: 1px solid rgba(255, 255, 255, 60);
            }
            """
        )

        armor_layout = QVBoxLayout(armor_card)
        armor_layout.setContentsMargins(16, 16, 16, 16)
        armor_layout.setSpacing(12)
        armor_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self._armor_image_label = QLabel()
        self._armor_image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        armor_layout.addWidget(self._armor_image_label)

        self._armor_name_label = QLabel("")
        self._armor_name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._armor_name_label.setStyleSheet(
            "color: white; font-size: 18px; font-weight: bold;"
        )
        armor_layout.addWidget(self._armor_name_label)

        main_row.addWidget(armor_card)

        # Right column (build request, resistances, artifacts)
        right_col = QVBoxLayout()
        right_col.setSpacing(20)
        main_row.addLayout(right_col, stretch=1)

        # Build request dropdown
        build_row = QHBoxLayout()
        build_row.setSpacing(12)

        build_label = QLabel("What kind of build do you want?")
        build_label.setStyleSheet("color: white; font-size: 16px; font-weight: bold;")
        build_row.addWidget(build_label)

        self._build_type_combo = QComboBox()
        self._build_type_combo.setFixedWidth(220)
        self._build_type_combo.addItems(
            ["Balanced", "Anomaly Protections", "Endurance", "Bleed Resistance"]
        )
        self._build_type_combo.setStyleSheet(
            """
            QComboBox {
                background-color: rgba(0, 0, 0, 160);
                color: white;
                border-radius: 8px;
                padding: 4px 8px;
                padding-right: 24px;
                border: 1px solid rgba(255, 255, 255, 80);
                font-size: 14px;
            }
            QComboBox::drop-down {
                width: 30px;
                border: 0px;
            }
            """
        )
        build_row.addWidget(self._build_type_combo)
        build_row.addStretch(1)
        right_col.addLayout(build_row)

        # Base resistances heading
        res_title = QLabel("Base Resistances (No Upgrades)")
        res_title.setStyleSheet(
            "color: white; font-size: 16px; font-weight: bold; text-decoration: underline;"
        )
        right_col.addWidget(res_title)

        # Container for resistance rows
        self._bars_container = QVBoxLayout()
        self._bars_container.setSpacing(6)
        right_col.addLayout(self._bars_container)

        right_col.addSpacing(10)

        # Selected artifacts list
        artifacts_title = QLabel("Selected Artifacts")
        artifacts_title.setStyleSheet("color: white; font-size: 16px; font-weight: bold;")
        right_col.addWidget(artifacts_title)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameStyle(0)
        # Make artifact list taller for visibility
        scroll.setMinimumHeight(220)
        scroll.setStyleSheet(
            """
            QScrollArea {
                background: transparent;
                border: none;
            }
            QScrollArea > QWidget > QWidget {
                background: transparent;
            }
            """
        )

        container = QWidget()
        self._artifacts_grid = QGridLayout(container)
        self._artifacts_grid.setContentsMargins(0, 0, 0, 0)
        self._artifacts_grid.setHorizontalSpacing(12)
        self._artifacts_grid.setVerticalSpacing(12)

        scroll.setWidget(container)
        right_col.addWidget(scroll, stretch=1)

        # Bottom buttons
        bottom = QHBoxLayout()
        bottom.setSpacing(16)

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
        bottom.addWidget(back_btn)

        bottom.addStretch(1)

        generate_btn = QPushButton("Generate")
        generate_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        generate_btn.clicked.connect(self._on_generate_clicked)
        generate_btn.setStyleSheet(
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
        bottom.addWidget(generate_btn)

        root.addLayout(bottom)

    # Update armor image and name
    def _refresh_armor_card(self):
        if not self._armor:
            return

        pixmap = load_pixmap_from_url(self._armor.get("image_url", ""), size=(180, 180))
        if not pixmap.isNull():
            self._armor_image_label.setPixmap(pixmap)
        else:
            self._armor_image_label.clear()

        self._armor_name_label.setText(self._armor.get("name", "Unknown Armor"))

    # Build base resistance rows
    def _refresh_resistance_rows(self):
        while self._bars_container.count():
            item = self._bars_container.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        if not self._armor or not self._base_bar_values:
            return

        labels = [
            ("thermal", "Thermal:"),
            ("electrical", "Electrical:"),
            ("chemical", "Chemical:"),
            ("radiation", "Radiation:"),
            ("psi", "Psi:"),
            ("physical", "Physical:"),
        ]

        for key, text in labels:
            row_layout = QHBoxLayout()
            row_layout.setSpacing(8)

            lbl = QLabel(text)
            lbl.setStyleSheet("color: white; font-size: 14px;")
            row_layout.addWidget(lbl)

            info = self._base_bar_values.get(key, {"full": 0, "half": 0})
            bars_layout = self._create_bar_row(info)
            row_layout.addLayout(bars_layout)
            row_layout.addStretch(1)

            self._bars_container.addLayout(row_layout)

    # Create 5 horizontal resistance bars
    def _create_bar_row(self, bar_info: dict):
        layout = QHBoxLayout()
        layout.setSpacing(4)

        full = bar_info.get("full", 0)
        half = bar_info.get("half", 0)

        total_bars = 5
        bar_width = 30
        bar_height = 10

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

    # Rebuild selected artifact cards
    def _refresh_artifacts(self):
        while self._artifacts_grid.count():
            item = self._artifacts_grid.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        if not self._selected_artifacts:
            return

        cols = 5
        for idx, art in enumerate(self._selected_artifacts):
            row = idx // cols
            col = idx % cols

            card = QFrame()
            card.setObjectName("artifactCardConfig")
            card.setStyleSheet(
                """
                QFrame#artifactCardConfig {
                    background-color: rgba(0, 0, 0, 120);
                    border-radius: 10px;
                    border: 1px solid rgba(255, 255, 255, 40);
                }
                """
            )

            v = QVBoxLayout(card)
            v.setContentsMargins(8, 8, 8, 8)
            v.setSpacing(6)

            img = QLabel()
            img.setAlignment(Qt.AlignmentFlag.AlignCenter)
            pix = load_pixmap_from_url(art.get("image_url", ""), size=(72, 72))
            if not pix.isNull():
                img.setPixmap(pix)
            v.addWidget(img)

            name_lbl = QLabel(art.get("name", "Unknown"))
            name_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            name_lbl.setStyleSheet("color: white; font-size: 12px;")
            v.addWidget(name_lbl)

            self._artifacts_grid.addWidget(card, row, col)

    # Go back to the artifact selection screen
    def _on_back_clicked(self):
        self.back_requested.emit()

    def _on_generate_clicked(self):
        """
        Packages all data collected across all steps into one payload
        and sends it to the main window to run the model
        """
        payload = {
            # 1.) Armor/ Artifact Slots/ Lead Containers
            "armor_config": self._armor_config,
            # 2.) The desired build type
            "build_type": self._build_type_combo.currentText()
            if self._build_type_combo
            else "Balanced",
            # 3.) The artifacts selected
            "artifacts": self._selected_artifacts,
        }
        self.next_requested.emit(payload)
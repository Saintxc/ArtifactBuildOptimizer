from typing import Dict, List, Optional
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame, QScrollArea, QGridLayout, QApplication)
from utils.image_loader import load_pixmap_from_url
from utils.stats import armor_resist_bars


class BuildResultsView(QWidget):
    """
    Final Results:
    It takes the results from the calculator and displays them in
    a user-friendly format and informs them if the build is safe or unsafe
    """
    back_requested = pyqtSignal()

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        # Placeholders for the data
        self._armor: Dict | None = None
        self._final_resists: Dict[str, int] = {}
        self._final_bars: Dict[str, Dict[str, int]] = {}
        self._chosen_artifacts: List[Dict] = []
        self._radiation_balance: int = 0

        # UI references for dynamic updates
        self._armor_image_label: QLabel | None = None
        self._armor_name_label: QLabel | None = None
        self._bars_container: QVBoxLayout | None = None
        self._artifacts_grid: QGridLayout | None = None
        self._radiation_label: QLabel | None = None

        self._build_ui()

    def set_context(self, result: Dict):
        """
        Populate the view with the results from the model.
        Called immediately before showing the view
        """
        self._armor = result.get("armor", {})
        self._final_resists = result.get("final_resistances", {}) or {}
        self._final_bars = armor_resist_bars({"resistances": self._final_resists})
        self._chosen_artifacts = result.get("chosen_artifacts", []) or []
        self._radiation_balance = int(result.get("radiation_balance", 0))

        # Refresh all the sub-components
        self._refresh_armor_card()
        self._refresh_resistance_rows()
        self._refresh_artifact_cards()
        self._update_radiation_status()

    # Build main layout (similar to all other views)
    def _build_ui(self):
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        root = QVBoxLayout(self)
        root.setContentsMargins(40, 40, 40, 20)
        root.setSpacing(24)

        title = QLabel("Build Results")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("color: white; font-size: 22px; font-weight: bold;")
        root.addWidget(title)

        main_row = QHBoxLayout()
        main_row.setSpacing(80)
        root.addLayout(main_row, stretch=1)

        # Armor card
        armor_card = QFrame()
        armor_card.setObjectName("resultsArmorCard")
        armor_card.setFixedSize(260, 320)
        armor_card.setStyleSheet(
            """
            QFrame#resultsArmorCard {
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

        # Status, resistances, and artifacts
        right_col = QVBoxLayout()
        right_col.setSpacing(16)
        main_row.addLayout(right_col, stretch=1)

        # Radiation SAFE or UNSAFE
        self._radiation_label = QLabel("RADIATION STATUS: SAFE")
        self._radiation_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self._radiation_label.setStyleSheet(
            "color: #2ecc71; font-size: 18px; font-weight: bold;"
        )
        right_col.addWidget(self._radiation_label)

        # Final resistances
        res_title = QLabel("Final Resistances (Base Armor + Artifacts)")
        res_title.setStyleSheet(
            "color: white; font-size: 16px; font-weight: bold; text-decoration: underline;"
        )
        right_col.addWidget(res_title)

        self._bars_container = QVBoxLayout()
        self._bars_container.setSpacing(6)
        right_col.addLayout(self._bars_container)

        right_col.addSpacing(10)

        # Selected artifacts
        artifacts_title = QLabel("Artifacts Used in Build")
        artifacts_title.setStyleSheet(
            "color: white; font-size: 16px; font-weight: bold;"
        )
        right_col.addWidget(artifacts_title)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameStyle(0)
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

        # Bottom bar
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

        exit_btn = QPushButton("Exit")
        exit_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        exit_btn.clicked.connect(self._on_exit_clicked)
        exit_btn.setStyleSheet(
            """
            QPushButton {
                background-color: #c0392b;
                color: white;
                padding: 8px 24px;
                border-radius: 6px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #e74c3c; }
            """
        )
        bottom.addWidget(exit_btn)

        root.addLayout(bottom)

    # Update armor card content
    def _refresh_armor_card(self):
        if not self._armor:
            self._armor_image_label.clear()
            self._armor_name_label.setText("")
            return

        pixmap = load_pixmap_from_url(self._armor.get("image_url", ""), size=(180, 180))
        if not pixmap.isNull():
            self._armor_image_label.setPixmap(pixmap)
        else:
            self._armor_image_label.clear()

        self._armor_name_label.setText(self._armor.get("name", "Unknown Armor"))

    # Recursively delete all widgets and sub-layouts
    def _clear_layout(self, layout):
        while layout.count():
            item = layout.takeAt(0)

            w = item.widget()
            if w is not None:
                w.deleteLater()

            child_layout = item.layout()
            if child_layout is not None:
                self._clear_layout(child_layout)

    # Rebuild resistance bar rows
    def _refresh_resistance_rows(self):
        """
        Dynamically clears and rebuilds the resistance bars.
        This is important because before the bars would keep stacking on top of one another
        and eventually became unreadable.
        """
        if self._bars_container is None:
            return

        # Clean up old widgets to prevent memory leaks or visual clutter
        self._clear_layout(self._bars_container)

        if not self._final_bars:
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
            bar_info = self._final_bars.get(key)
            if not bar_info:
                bar_info = {"full": 0, "half": 0, "empty": 5}

            row_layout = QHBoxLayout()
            row_layout.setSpacing(8)

            lbl = QLabel(text)
            lbl.setStyleSheet("color: white; font-size: 14px;")
            row_layout.addWidget(lbl)

            # Re-use the bar drawing logic
            bars_layout = self._create_bar_row(bar_info)
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

    # Rebuild artifact cards grid with chosen artifacts
    def _refresh_artifact_cards(self):
        while self._artifacts_grid.count():
            item = self._artifacts_grid.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        if not self._chosen_artifacts:
            return

        cols = 5
        for idx, item in enumerate(self._chosen_artifacts):
            art = item.get("artifact", {})
            in_lead = bool(item.get("in_lead_container", False))

            row = idx // cols
            col = idx % cols

            card = QFrame()
            card.setObjectName("resultsArtifactCard")

            desc = art.get("description")
            if desc:
                card.setToolTip(desc)

            # If the artifact is in a lead container, give it a thick white border to signify that
            if in_lead:
                border = "2px solid rgba(230, 230, 230, 230)"
            else:
                border = "1px solid rgba(255, 255, 255, 40)"

            card.setStyleSheet(
                f"""
                QFrame#resultsArtifactCard {{
                    background-color: rgba(0, 0, 0, 120);
                    border-radius: 10px;
                    border: {border};
                }}
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

    # Update SAFE / UNSAFE based on radiation
    def _update_radiation_status(self):
        """
        Changes the text color at the top of the app to indicate radiation status.
        Green means it's safe and displays SAFE
        Red means it's safe and displays UNSAFE
        """
        net_radiation = -self._radiation_balance

        if net_radiation > 0:
            text = "RADIATION STATUS: UNSAFE"
            color = "#ff5555"
        else:
            text = "RADIATION STATUS: SAFE"
            color = "#2ecc71"

        self._radiation_label.setText(text)
        self._radiation_label.setStyleSheet(
            f"color: {color}; font-size: 18px; font-weight: bold;"
        )

    def _on_back_clicked(self):
        # Emit back navigation
        self.back_requested.emit()

    def _on_exit_clicked(self):
        # Exit the application
        app = QApplication.instance()
        if app is not None:
            app.quit()
from pathlib import Path
from typing import Any, Dict, Optional
from PyQt6.QtCore import Qt, QRectF, QSize
from PyQt6.QtGui import QColor, QLinearGradient, QPainter, QPainterPath, QPen, QPixmap
from PyQt6.QtWidgets import (
    QDialog, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QFrame, QMessageBox
)
from src.database.db_manager import SupabaseHealthRepository
from src.ui.main_window import AsyncTaskWorker, GlassCardFrame, GlassLineEdit, ArcSpinner, svg_pixmap
from src.ui.theme import NOIR_ESPRESSO_CREAM_QSS


BACKGROUND_IMAGE_PATH = Path(__file__).resolve().parent.parent / "img" / "pamp.jpg"


class ClinicianLoginDialog(QDialog):
    """
    Glassmorphic login screen for VITA HEALTH clinicians.
    Authenticates against PostgreSQL (`vita_health.authenticate_clinician`)
    without blocking the PyQt6 UI thread.
    """

    def __init__(self, repo: SupabaseHealthRepository, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.repo = repo
        self.authenticated_clinician: Optional[Dict[str, Any]] = None
        self._workers: list[AsyncTaskWorker] = []
        self._bg_pixmap = QPixmap(str(BACKGROUND_IMAGE_PATH)) if BACKGROUND_IMAGE_PATH.exists() else QPixmap()

        self.setWindowTitle("VITA HEALTH · Clinician Sign In")
        self.setFixedSize(460, 540)
        self.setStyleSheet(NOIR_ESPRESSO_CREAM_QSS)
        self._build_ui()

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        rect = self.rect()

        if not self._bg_pixmap.isNull():
            scaled = self._bg_pixmap.scaled(
                rect.size(),
                Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                Qt.TransformationMode.SmoothTransformation,
            )
            x_off = (scaled.width() - rect.width()) // 2
            y_off = (scaled.height() - rect.height()) // 2
            painter.drawPixmap(0, 0, scaled, x_off, y_off, rect.width(), rect.height())
        else:
            painter.fillRect(rect, QColor("#140E0A"))

        overlay = QLinearGradient(0.0, 0.0, 0.0, float(rect.height()))
        overlay.setColorAt(0.0, QColor(14, 10, 7, 205))
        overlay.setColorAt(0.55, QColor(20, 14, 10, 195))
        overlay.setColorAt(1.0, QColor(12, 8, 6, 225))
        painter.fillRect(rect, overlay)

        super().paintEvent(event)

    def _build_ui(self) -> None:
        outer = QVBoxLayout(self)
        outer.setContentsMargins(28, 28, 28, 28)
        outer.setSpacing(14)

        # Top brand header
        top_row = QHBoxLayout()
        top_row.setSpacing(10)
        mark = QLabel()
        mark.setFixedSize(30, 30)
        mark.setPixmap(svg_pixmap("brand_mark", color="#FBF7F1", size=26))
        top_row.addWidget(mark)

        title_col = QVBoxLayout()
        title_col.setSpacing(2)
        title = QLabel("VITA HEALTH", objectName="BrandTitle")
        sub = QLabel("Clinical Triage & Care OS · Staff Authentication", objectName="BrandSub")
        title_col.addWidget(title)
        title_col.addWidget(sub)
        top_row.addLayout(title_col)
        top_row.addStretch()
        outer.addLayout(top_row)

        card = GlassCardFrame(radius=14.0)
        form_lay = QVBoxLayout(card)
        form_lay.setContentsMargins(22, 22, 22, 22)
        form_lay.setSpacing(12)

        heading = QLabel("Sign In to Workstation", objectName="SectionHeading")
        heading.setStyleSheet("color: #120E0B; font-size: 16px; font-weight: 800;")
        form_lay.addWidget(heading)

        hint = QLabel("Enter your Clinician Badge ID or registered clinical email.")
        hint.setStyleSheet("color: #2B1C13; font-size: 11.5px; font-weight: 500;")
        hint.setWordWrap(True)
        form_lay.addWidget(hint)

        id_lbl = QLabel("BADGE ID OR EMAIL")
        id_lbl.setStyleSheet("color: #2B1C13; font-size: 10px; font-weight: 700; letter-spacing: 0.7px;")
        self.id_input = GlassLineEdit()
        self.id_input.setPlaceholderText("e.g. VH-MD-01 or a.kamara@vitahealth.org")
        self.id_input.setMinimumHeight(38)
        self.id_input.returnPressed.connect(lambda: self.password_input.setFocus())
        form_lay.addWidget(id_lbl)
        form_lay.addWidget(self.id_input)

        pw_lbl = QLabel("PASSCODE / PASSWORD")
        pw_lbl.setStyleSheet("color: #2B1C13; font-size: 10px; font-weight: 700; letter-spacing: 0.7px;")
        pw_row = QHBoxLayout()
        pw_row.setSpacing(6)
        self.password_input = GlassLineEdit()
        self.password_input.setPlaceholderText("Enter password")
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.setMinimumHeight(38)
        self.password_input.returnPressed.connect(self._attempt_login)

        self.btn_toggle_pw = QPushButton("Show", objectName="SecondaryBtn")
        self.btn_toggle_pw.setFixedSize(58, 38)
        self.btn_toggle_pw.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_toggle_pw.clicked.connect(self._toggle_password_visibility)

        pw_row.addWidget(self.password_input, stretch=1)
        pw_row.addWidget(self.btn_toggle_pw)
        form_lay.addWidget(pw_lbl)
        form_lay.addLayout(pw_row)

        self.status_lbl = QLabel("")
        self.status_lbl.setWordWrap(True)
        self.status_lbl.setStyleSheet("color: #991B1B; font-weight: 700; font-size: 11.5px;")
        form_lay.addWidget(self.status_lbl)

        action_row = QHBoxLayout()
        action_row.setSpacing(10)
        self.spinner = ArcSpinner(22)
        self.btn_login = QPushButton("Sign In & Launch", objectName="PrimaryBtn")
        self.btn_login.setMinimumHeight(40)
        self.btn_login.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_login.clicked.connect(self._attempt_login)

        action_row.addWidget(self.spinner)
        action_row.addWidget(self.btn_login, stretch=1)
        form_lay.addLayout(action_row)

        # Quick helper for seeded sample account
        demo_row = QHBoxLayout()
        btn_demo = QPushButton("Fill Sample MD (VH-MD-01)", objectName="SecondaryBtn")
        btn_demo.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_demo.clicked.connect(self._fill_sample_clinician)
        demo_row.addWidget(btn_demo)
        form_lay.addLayout(demo_row)

        outer.addWidget(card)

        footer = QLabel("Schema: vita_health · Audited Clinical Session")
        footer.setAlignment(Qt.AlignmentFlag.AlignCenter)
        footer.setStyleSheet("color: #C5AE96; font-size: 11px; font-weight: 500;")
        outer.addWidget(footer)

    def _toggle_password_visibility(self) -> None:
        is_hidden = self.password_input.echoMode() == QLineEdit.EchoMode.Password
        self.password_input.setEchoMode(
            QLineEdit.EchoMode.Normal if is_hidden else QLineEdit.EchoMode.Password
        )
        self.btn_toggle_pw.setText("Hide" if is_hidden else "Show")

    def _fill_sample_clinician(self) -> None:
        self.id_input.setText("VH-MD-01")
        self.password_input.setText("VitaCare#2026")
        self.status_lbl.setText("")

    def _attempt_login(self) -> None:
        identifier = self.id_input.text().strip()
        password = self.password_input.text()

        if not identifier or not password:
            self.status_lbl.setText("Please enter both Badge ID/Email and password.")
            return

        self.status_lbl.setText("")
        self.btn_login.setEnabled(False)
        self.btn_login.setText("Verifying...")
        self.spinner.start()

        worker = AsyncTaskWorker(
            lambda: self.repo.authenticate_clinician(identifier, password),
            self,
        )
        self._workers.append(worker)

        def _cleanup() -> None:
            if worker in self._workers:
                self._workers.remove(worker)
            worker.deleteLater()
            self.spinner.stop()
            self.btn_login.setEnabled(True)
            self.btn_login.setText("Sign In & Launch")

        def _on_ok(user: Optional[Dict[str, Any]]) -> None:
            _cleanup()
            if not user:
                self.status_lbl.setText("Invalid credentials or inactive clinician account.")
                return
            self.authenticated_clinician = user
            self.accept()

        def _on_err(err: str) -> None:
            _cleanup()
            self.status_lbl.setText(f"Authentication error: {err}")
            QMessageBox.critical(self, "Database Auth Error", err)

        worker.succeeded.connect(_on_ok)
        worker.failed.connect(_on_err)
        worker.start()
import csv
import json
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple
from PyQt6.QtCore import (
    Qt, QByteArray, QDate, QPointF, QRectF, QSize, QTimer, QThread, pyqtSignal,
    QPropertyAnimation, QParallelAnimationGroup, QEasingCurve
)
from PyQt6.QtGui import (
    QColor, QFont, QIcon, QLinearGradient, QPainter, QPainterPath, QPen,
    QPixmap, QRegion, QShortcut, QKeySequence
)
from PyQt6.QtSvg import QSvgRenderer
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QTableWidget, QTableWidgetItem, QHeaderView, QFrame,
    QStackedWidget, QFormLayout, QComboBox, QSpinBox, QDoubleSpinBox,
    QDateEdit, QTextEdit, QMessageBox, QFileDialog,
    QAbstractItemView, QGraphicsOpacityEffect, QProgressBar, QTabWidget,
    QScrollArea
)
from src.database.db_manager import SupabaseHealthRepository
from src.models.registry import InMemoryTriageRegistry
from src.models.entities import ClinicalEncounter
from src.ui.theme import NOIR_ESPRESSO_CREAM_QSS


BACKGROUND_IMAGE_PATH = Path(__file__).resolve().parent.parent / "img" / "pamp.jpg"


SVG_ICONS: Dict[str, str] = {
    "brand_mark": (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" '
        'stroke="{color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">'
        '<circle cx="12" cy="12" r="9"/>'
        '<path d="M12 8v8"/><path d="M8 12h8"/>'
        '</svg>'
    ),
    "nav_triage": (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" '
        'stroke="{color}" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round">'
        '<path d="M3 12h3.5l2-5 3.5 10 2.5-5H21"/>'
        '</svg>'
    ),
    "nav_intake": (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" '
        'stroke="{color}" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round">'
        '<circle cx="9.5" cy="8" r="3.5"/>'
        '<path d="M3.5 19a6 6 0 0 1 12 0"/>'
        '<path d="M19 8v6"/><path d="M16 11h6"/>'
        '</svg>'
    ),
    "nav_facilities": (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" '
        'stroke="{color}" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round">'
        '<path d="M12 3l8 3.5v5.5c0 5-3.4 8.2-8 9.8-4.6-1.6-8-4.8-8-9.8V6.5L12 3z"/>'
        '<path d="M12 9v5"/><path d="M9.5 11.5h5"/>'
        '</svg>'
    ),
    "sync": (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" '
        'stroke="{color}" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round">'
        '<path d="M20 11a8.1 8.1 0 0 0-15.5-2m-.5-4v4h4"/>'
        '<path d="M4 13a8.1 8.1 0 0 0 15.5 2m.5 4v-4h-4"/>'
        '</svg>'
    ),
    "export": (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" '
        'stroke="{color}" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round">'
        '<path d="M12 15V3"/><path d="m7 8 5-5 5 5"/>'
        '<path d="M4 15v4a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-4"/>'
        '</svg>'
    ),
    "audit": (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" '
        'stroke="{color}" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round">'
        '<path d="M14 3H6a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V9z"/>'
        '<path d="M14 3v6h6"/><path d="M8 13h8"/><path d="M8 17h5"/>'
        '</svg>'
    ),
}


def svg_pixmap(icon_key: str, color: str = "#241810", size: int = 16) -> QPixmap:
    """Renders an inline SVG template into a crisp high-DPI QPixmap."""
    raw = SVG_ICONS[icon_key].format(color=color).encode("utf-8")
    renderer = QSvgRenderer(QByteArray(raw))
    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    renderer.render(painter)
    painter.end()
    return pixmap


def svg_icon(icon_key: str, color: str = "#241810", size: int = 16) -> QIcon:
    """Wraps a rendered SVG QPixmap in a QIcon."""
    return QIcon(svg_pixmap(icon_key, color=color, size=size))


def _draw_chevron(
    painter: QPainter,
    cx: float,
    cy: float,
    direction: str = "down",
    color: str = "#241810",
    half_w: float = 3.8,
    half_h: float = 2.0,
) -> None:
    """Paints a crisp stroke chevron without any box or fill."""
    painter.save()
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    pen = QPen(QColor(color), 1.7)
    pen.setCapStyle(Qt.PenCapStyle.RoundCap)
    pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
    painter.setPen(pen)

    if direction == "up":
        painter.drawLine(int(cx - half_w), int(cy + half_h), int(cx), int(cy - half_h))
        painter.drawLine(int(cx), int(cy - half_h), int(cx + half_w), int(cy + half_h))
    else:
        painter.drawLine(int(cx - half_w), int(cy - half_h), int(cx), int(cy + half_h))
        painter.drawLine(int(cx), int(cy + half_h), int(cx + half_w), int(cy - half_h))
    painter.restore()


class PillFilterButton(QWidget):
    """Custom full-capsule pill button with high-contrast selection styling."""

    clicked = pyqtSignal()

    def __init__(self, text: str, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._text = text
        self._selected = False
        self._hovered = False
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        fm = self.fontMetrics()
        w = fm.horizontalAdvance(text) + 34
        self.setFixedSize(max(w, 68), 32)

    def setSelected(self, selected: bool) -> None:
        self._selected = selected
        self.update()

    def isSelected(self) -> bool:
        return self._selected

    def enterEvent(self, event) -> None:
        self._hovered = True
        self.update()
        super().enterEvent(event)

    def leaveEvent(self, event) -> None:
        self._hovered = False
        self.update()
        super().leaveEvent(event)

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()
            event.accept()
            return
        super().mousePressEvent(event)

    def paintEvent(self, _event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        rect = QRectF(self.rect()).adjusted(0.8, 0.8, -0.8, -0.8)
        radius = rect.height() / 2.0

        path = QPainterPath()
        path.addRoundedRect(rect, radius, radius)
        painter.setClipPath(path)

        if self._selected:
            bg = QColor(251, 247, 241, 245)
            border = QColor(255, 255, 255, 255)
            fg = QColor("#120E0B")
        elif self._hovered:
            bg = QColor(255, 252, 247, 196)
            border = QColor(255, 255, 255, 190)
            fg = QColor("#120E0B")
        else:
            bg = QColor(251, 247, 241, 134)
            border = QColor(255, 252, 247, 122)
            fg = QColor("#120E0B")

        painter.fillPath(path, bg)
        painter.setClipping(False)
        painter.setPen(QPen(border, 1.2 if self._selected else 1.0))
        painter.drawRoundedRect(rect, radius, radius)

        font = QFont(self.font())
        font.setBold(self._selected or self._hovered)
        font.setPointSizeF(11.0)
        painter.setFont(font)
        painter.setPen(fg)
        painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, self._text)
        painter.end()


class ActiveCheckBox(QWidget):
    """Custom checkbox with a cream box and a crisp dark espresso checkmark."""

    stateChanged = pyqtSignal(int)

    def __init__(self, label: str = "Active Only", checked: bool = True, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._label = label
        self._checked = checked
        self._hovered = False
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        fm = self.fontMetrics()
        self.setFixedSize(26 + fm.horizontalAdvance(label) + 8, 28)

    def isChecked(self) -> bool:
        return self._checked

    def setChecked(self, checked: bool) -> None:
        if self._checked != checked:
            self._checked = checked
            self.update()
            self.stateChanged.emit(2 if checked else 0)

    def enterEvent(self, event) -> None:
        self._hovered = True
        self.update()
        super().enterEvent(event)

    def leaveEvent(self, event) -> None:
        self._hovered = False
        self.update()
        super().leaveEvent(event)

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self._checked = not self._checked
            self.update()
            self.stateChanged.emit(2 if self._checked else 0)
            event.accept()
            return
        super().mousePressEvent(event)

    def paintEvent(self, _event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        box_size = 17.0
        box_rect = QRectF(1.0, (self.height() - box_size) / 2.0, box_size, box_size)
        box_path = QPainterPath()
        box_path.addRoundedRect(box_rect, 5.0, 5.0)

        if self._checked:
            painter.fillPath(box_path, QColor("#FBF7F1"))
            painter.setPen(QPen(QColor("#FFFFFF"), 1.3))
            painter.drawPath(box_path)

            tick_pen = QPen(QColor("#140E0A"), 2.1)
            tick_pen.setCapStyle(Qt.PenCapStyle.RoundCap)
            tick_pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
            painter.setPen(tick_pen)
            x0, y0 = box_rect.left(), box_rect.top()
            painter.drawLine(QPointF(x0 + 4.0, y0 + 8.8), QPointF(x0 + 7.4, y0 + 12.2))
            painter.drawLine(QPointF(x0 + 7.4, y0 + 12.2), QPointF(x0 + 13.2, y0 + 5.2))
        else:
            painter.fillPath(box_path, QColor(20, 14, 10, 155))
            border = QColor("#FBF7F1") if self._hovered else QColor(251, 247, 241, 135)
            painter.setPen(QPen(border, 1.3))
            painter.drawPath(box_path)

        font = QFont(self.font())
        font.setBold(True)
        font.setPointSizeF(12.0)
        painter.setFont(font)
        painter.setPen(QColor("#FBF7F1"))
        text_rect = QRectF(box_rect.right() + 8.0, 0.0, self.width() - box_rect.right() - 8.0, self.height())
        painter.drawText(text_rect, Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft, self._label)
        painter.end()


class ClinicianProfileSwitcher(QWidget):
    """
    Distinct clinician profile switcher with initials medallion, live shift pulse indicator,
    profile counter badge, and click-to-cycle profile switching.
    """

    profileSelected = pyqtSignal(int)

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._profiles: List[Tuple[str, Any]] = []
        self._index = 0
        self._hovered = False
        self.setFixedHeight(74)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

    def setProfiles(self, items: List[Tuple[str, Any]], active_index: int = 0) -> None:
        self._profiles = list(items)
        if not self._profiles:
            self._index = 0
        else:
            self._index = max(0, min(active_index, len(self._profiles) - 1))
        self.update()

    def setCurrentIndex(self, idx: int) -> None:
        if 0 <= idx < len(self._profiles):
            self._index = idx
            self.update()

    def currentIndex(self) -> int:
        return self._index

    def currentData(self) -> Any:
        if not self._profiles:
            return None
        return self._profiles[self._index][1]

    def currentText(self) -> str:
        if not self._profiles:
            return "On-Duty Clinician"
        return self._profiles[self._index][0]

    def _initials(self, name: str) -> str:
        cleaned = [
            tok.strip(".,")
            for tok in name.split()
            if tok.strip(".,").lower() not in {"dr", "nurse", "rn", "md", "pa", "np", "mr", "ms", "mrs"}
        ]
        source = cleaned if cleaned else name.split()
        if not source:
            return "VH"
        if len(source) == 1:
            return source[0][:2].upper()
        return (source[0][0] + source[-1][0]).upper()

    def enterEvent(self, event) -> None:
        self._hovered = True
        self.update()
        super().enterEvent(event)

    def leaveEvent(self, event) -> None:
        self._hovered = False
        self.update()
        super().leaveEvent(event)

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton and len(self._profiles) > 1:
            self._index = (self._index + 1) % len(self._profiles)
            self.update()
            self.profileSelected.emit(self._index)
            event.accept()
            return
        super().mousePressEvent(event)

    def paintEvent(self, _event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        rect = QRectF(self.rect()).adjusted(0.8, 0.8, -0.8, -0.8)
        radius = 13.0
        path = QPainterPath()
        path.addRoundedRect(rect, radius, radius)
        painter.setClipPath(path)

        grad = QLinearGradient(0.0, rect.top(), rect.right(), rect.bottom())
        if self._hovered:
            grad.setColorAt(0.0, QColor(68, 46, 32, 242))
            grad.setColorAt(1.0, QColor(36, 23, 15, 248))
        else:
            grad.setColorAt(0.0, QColor(46, 31, 21, 232))
            grad.setColorAt(1.0, QColor(24, 16, 11, 242))
        painter.fillPath(path, grad)

        painter.setClipping(False)
        border = QColor(251, 247, 241, 145) if self._hovered else QColor(251, 247, 241, 64)
        painter.setPen(QPen(border, 1.15))
        painter.drawRoundedRect(rect, radius, radius)

        full_label = self.currentText()
        parts = [p.strip() for p in full_label.split("·", 1)]
        name_txt = parts[0] if parts else "On-Duty Clinician"
        role_txt = parts[1] if len(parts) > 1 else "ON SHIFT"

        # Initials medallion
        med_rect = QRectF(rect.left() + 11.0, rect.center().y() - 19.0, 38.0, 38.0)
        med_path = QPainterPath()
        med_path.addRoundedRect(med_rect, 11.0, 11.0)
        painter.fillPath(med_path, QColor("#FBF7F1"))

        med_font = QFont(self.font())
        med_font.setBold(True)
        med_font.setPointSizeF(12.0)
        painter.setFont(med_font)
        painter.setPen(QColor("#140E0A"))
        painter.drawText(med_rect, Qt.AlignmentFlag.AlignCenter, self._initials(name_txt))

        # Live shift indicator dot on medallion corner
        dot_center = QPointF(med_rect.right() - 2.0, med_rect.top() + 2.0)
        painter.setPen(QPen(QColor("#1E130D"), 2.0))
        painter.setBrush(QColor("#34D399"))
        painter.drawEllipse(dot_center, 4.5, 4.5)

        # Profile name + role/slot metadata
        tx = med_rect.right() + 11.0
        tw = rect.right() - tx - 34.0

        name_font = QFont(self.font())
        name_font.setBold(True)
        name_font.setPointSizeF(12.2)
        painter.setFont(name_font)
        painter.setPen(QColor("#FBF7F1"))
        elided_name = painter.fontMetrics().elidedText(name_txt, Qt.TextElideMode.ElideRight, int(tw))
        painter.drawText(
            QRectF(tx, rect.top() + 12.0, tw, 20.0),
            Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft,
            elided_name,
        )

        slot_suffix = f" · {self._index + 1}/{len(self._profiles)}" if len(self._profiles) > 1 else ""
        meta_str = f"{role_txt.upper()}{slot_suffix}"
        meta_font = QFont(self.font())
        meta_font.setBold(True)
        meta_font.setPointSizeF(9.0)
        painter.setFont(meta_font)
        painter.setPen(QColor("#D8C1A8"))
        elided_meta = painter.fontMetrics().elidedText(meta_str, Qt.TextElideMode.ElideRight, int(tw))
        painter.drawText(
            QRectF(tx, rect.top() + 34.0, tw, 18.0),
            Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft,
            elided_meta,
        )

        # Right cycle pill/chevrons
        cx = rect.right() - 15.0
        cy = rect.center().y()
        arrow_col = "#FFFFFF" if self._hovered else "#E3D1BE"
        _draw_chevron(painter, cx, cy - 5.0, "up", arrow_col, half_w=3.6, half_h=1.8)
        _draw_chevron(painter, cx, cy + 5.0, "down", arrow_col, half_w=3.6, half_h=1.8)

        painter.end()


class BackdropPageStack(QStackedWidget):
    """Paints src/img/pamp.jpg scaled to cover the main page area beneath a dark gradient."""

    def __init__(self, image_path: Path, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._bg_pixmap = QPixmap(str(image_path)) if image_path.exists() else QPixmap()

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
            painter.fillRect(rect, QColor("#1A110C"))

        gradient = QLinearGradient(0.0, 0.0, 0.0, float(rect.height()))
        gradient.setColorAt(0.0, QColor(14, 10, 7, 195))
        gradient.setColorAt(0.55, QColor(20, 14, 10, 182))
        gradient.setColorAt(1.0, QColor(12, 8, 6, 212))
        painter.fillRect(rect, gradient)

        super().paintEvent(event)


class GlassCardFrame(QFrame):
    """Glassmorphism card with rounded overflow clipping and soft frosted gradient."""

    def __init__(self, parent: Optional[QWidget] = None, radius: float = 11.0) -> None:
        super().__init__(parent)
        self.setObjectName("SurfaceCard")
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self._radius = radius

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        rect = QRectF(self.rect()).adjusted(0.8, 0.8, -0.8, -0.8)

        path = QPainterPath()
        path.addRoundedRect(rect, self._radius, self._radius)
        painter.setClipPath(path)

        glass = QLinearGradient(0.0, rect.top(), 0.0, rect.bottom())
        glass.setColorAt(0.0, QColor(255, 251, 245, 168))
        glass.setColorAt(1.0, QColor(246, 238, 226, 134))
        painter.fillPath(path, glass)

        painter.setClipping(False)
        painter.setPen(QPen(QColor(255, 252, 247, 118), 1.0))
        painter.drawRoundedRect(rect, self._radius, self._radius)

        super().paintEvent(event)


class GlassLineEdit(QLineEdit):
    """Translucent glass text input clipped cleanly to its rounded corners."""

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        rect = QRectF(self.rect()).adjusted(0.8, 0.8, -0.8, -0.8)
        radius = 8.0

        path = QPainterPath()
        path.addRoundedRect(rect, radius, radius)
        painter.setClipPath(path)

        fill_alpha = 212 if self.hasFocus() else 148
        painter.fillPath(path, QColor(255, 252, 247, fill_alpha))

        painter.setClipping(False)
        border_col = QColor(36, 24, 16, 210) if self.hasFocus() else QColor(255, 252, 247, 125)
        painter.setPen(QPen(border_col, 1.3 if self.hasFocus() else 1.0))
        painter.drawRoundedRect(rect, radius, radius)
        painter.end()
        super().paintEvent(event)


class GlassTextEdit(QTextEdit):
    """Translucent glass multi-line text area clipped cleanly to rounded corners."""

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.viewport().setAutoFillBackground(False)

    def paintEvent(self, event) -> None:
        painter = QPainter(self.viewport())
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        vrect = QRectF(self.viewport().rect())
        path = QPainterPath()
        path.addRoundedRect(vrect, 7.0, 7.0)
        painter.setClipPath(path)
        fill_alpha = 212 if self.hasFocus() else 148
        painter.fillPath(path, QColor(255, 252, 247, fill_alpha))
        painter.end()
        super().paintEvent(event)


class GlassTableWidget(QTableWidget):
    """Lineless glassmorphism table with clipped rounded corners and no border strokes."""

    def __init__(self, rows: int, cols: int, parent: Optional[QWidget] = None) -> None:
        super().__init__(rows, cols, parent)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFrameShape(QFrame.Shape.NoFrame)
        self.setShowGrid(False)
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.viewport().setAutoFillBackground(False)

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        rect = QRectF(self.rect())
        path = QPainterPath()
        path.addRoundedRect(rect, 11.0, 11.0)
        self.setMask(QRegion(path.toFillPolygon().toPolygon()))

    def paintEvent(self, event) -> None:
        painter = QPainter(self.viewport())
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        vrect = QRectF(self.viewport().rect())
        painter.fillRect(vrect, QColor(255, 251, 245, 136))
        painter.end()
        super().paintEvent(event)


class ChevronComboBox(QComboBox):
    """QComboBox with a clean painted down-chevron and no button box."""

    def __init__(self, arrow_color: str = "#241810", parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._arrow_color = arrow_color

    def paintEvent(self, event) -> None:
        super().paintEvent(event)
        painter = QPainter(self)
        _draw_chevron(painter, self.width() - 13.0, self.height() / 2.0, "down", self._arrow_color)


class ChevronDateEdit(QDateEdit):
    """QDateEdit with a clean painted down-chevron and no spinner/drop-down box."""

    def __init__(self, date: QDate, arrow_color: str = "#241810", parent: Optional[QWidget] = None) -> None:
        super().__init__(date, parent)
        self._arrow_color = arrow_color
        self.setButtonSymbols(QDateEdit.ButtonSymbols.NoButtons)

    def paintEvent(self, event) -> None:
        super().paintEvent(event)
        painter = QPainter(self)
        _draw_chevron(painter, self.width() - 13.0, self.height() / 2.0, "down", self._arrow_color)


class ChevronSpinBox(QSpinBox):
    """QSpinBox with box-free up/down chevrons that increment/decrement on click."""

    def __init__(self, arrow_color: str = "#241810", parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._arrow_color = arrow_color
        self.setButtonSymbols(QSpinBox.ButtonSymbols.NoButtons)
        self.setMouseTracking(True)

    def _hit_chevron(self, x: float, y: float) -> Optional[str]:
        if x < self.width() - 24:
            return None
        return "up" if y < self.height() / 2.0 else "down"

    def mouseMoveEvent(self, event) -> None:
        if self._hit_chevron(event.position().x(), event.position().y()):
            self.setCursor(Qt.CursorShape.PointingHandCursor)
        else:
            self.unsetCursor()
        super().mouseMoveEvent(event)

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            zone = self._hit_chevron(event.position().x(), event.position().y())
            if zone == "up":
                self.stepUp()
                event.accept()
                return
            if zone == "down":
                self.stepDown()
                event.accept()
                return
        super().mousePressEvent(event)

    def paintEvent(self, event) -> None:
        super().paintEvent(event)
        painter = QPainter(self)
        cx = self.width() - 13.0
        cy = self.height() / 2.0
        _draw_chevron(painter, cx, cy - 4.2, "up", self._arrow_color, half_w=3.4, half_h=1.7)
        _draw_chevron(painter, cx, cy + 4.2, "down", self._arrow_color, half_w=3.4, half_h=1.7)


class ChevronDoubleSpinBox(QDoubleSpinBox):
    """QDoubleSpinBox with box-free up/down chevrons that increment/decrement on click."""

    def __init__(self, arrow_color: str = "#241810", parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._arrow_color = arrow_color
        self.setButtonSymbols(QDoubleSpinBox.ButtonSymbols.NoButtons)
        self.setMouseTracking(True)

    def _hit_chevron(self, x: float, y: float) -> Optional[str]:
        if x < self.width() - 24:
            return None
        return "up" if y < self.height() / 2.0 else "down"

    def mouseMoveEvent(self, event) -> None:
        if self._hit_chevron(event.position().x(), event.position().y()):
            self.setCursor(Qt.CursorShape.PointingHandCursor)
        else:
            self.unsetCursor()
        super().mouseMoveEvent(event)

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            zone = self._hit_chevron(event.position().x(), event.position().y())
            if zone == "up":
                self.stepUp()
                event.accept()
                return
            if zone == "down":
                self.stepDown()
                event.accept()
                return
        super().mousePressEvent(event)

    def paintEvent(self, event) -> None:
        super().paintEvent(event)
        painter = QPainter(self)
        cx = self.width() - 13.0
        cy = self.height() / 2.0
        _draw_chevron(painter, cx, cy - 4.2, "up", self._arrow_color, half_w=3.4, half_h=1.7)
        _draw_chevron(painter, cx, cy + 4.2, "down", self._arrow_color, half_w=3.4, half_h=1.7)


class ArcSpinner(QWidget):
    """Smooth rotating arc indicator for async operations."""

    def __init__(self, size: int = 20, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setFixedSize(size, size)
        self._angle = 0
        self._timer = QTimer(self)
        self._timer.setInterval(20)
        self._timer.timeout.connect(self._tick)
        self.hide()

    def start(self) -> None:
        self.show()
        self._timer.start()

    def stop(self) -> None:
        self._timer.stop()
        self.hide()

    def _tick(self) -> None:
        self._angle = (self._angle + 12) % 360
        self.update()

    def paintEvent(self, _event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        pad = 3
        rect = self.rect().adjusted(pad, pad, -pad, -pad)

        painter.setPen(QPen(QColor("#DDD0BE"), 2.6))
        painter.drawEllipse(rect)

        active_pen = QPen(QColor("#FBF7F1"), 2.8)
        active_pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(active_pen)
        painter.drawArc(rect, -self._angle * 16, 110 * 16)


class AsyncTaskWorker(QThread):
    """Runs repository operations off the UI thread."""
    succeeded = pyqtSignal(object)
    failed = pyqtSignal(str)

    def __init__(self, fn: Callable[[], Any], parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._fn = fn

    def run(self) -> None:
        try:
            self.succeeded.emit(self._fn())
        except Exception as exc:
            self.failed.emit(str(exc))


class VitaHealthMainWindow(QMainWindow):
    """
    Zero-shift enterprise clinical workstation for VITA HEALTH with glassmorphism
    cards, inputs, and lineless tables over darkened pamp.jpg backdrops, targeted SVG icons,
    box-free chevrons, enhanced clinician profile switcher, keyboard pass-through
    navigation, async spinners, and audit log filtering.
    """

    def __init__(
        self,
        repo: SupabaseHealthRepository,
        current_clinician: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__()
        self.repo = repo
        self.current_clinician: Optional[Dict[str, Any]] = current_clinician
        self.registry = InMemoryTriageRegistry()
        self.selected_triage_filter = "ALL"
        self.selected_encounter: Optional[ClinicalEncounter] = None
        self.selected_patient_id: Optional[int] = None
        self._audit_logs_cache: List[Dict[str, Any]] = []
        self._workers: List[AsyncTaskWorker] = []

        self.setWindowTitle("VITA HEALTH · Enterprise Community Health & Triage Suite")
        self.resize(1480, 900)
        self.setMinimumSize(1180, 720)
        self.setStyleSheet(NOIR_ESPRESSO_CREAM_QSS)

        self._build_ui()
        self.set_active_clinician(self.current_clinician)
        self._bind_shortcuts()
        self._wire_live_acuity_preview()
        self._wire_form_pass_through()
        self.trigger_sync()

    @staticmethod
    def _format_clinician_label(clinician: Dict[str, Any]) -> str:
        if clinician.get("label"):
            return str(clinician["label"]).strip()
        name = str(clinician.get("full_name") or "On-Duty Clinician").strip()
        role = str(clinician.get("role_title") or "").strip()
        return f"{name} · {role}" if role else name

    def set_active_clinician(self, clinician: Optional[Dict[str, Any]]) -> None:
        """Ensures the signed-in clinician is displayed in the bottom profile switcher and synced."""
        if not clinician:
            return

        self.current_clinician = dict(clinician)
        staff_id = clinician.get("staff_id")
        label = self._format_clinician_label(clinician)

        profiles = list(getattr(self.duty_clinician_combo, "_profiles", []))
        match_idx = next(
            (
                i for i, (lbl, sid) in enumerate(profiles)
                if (staff_id is not None and sid == staff_id) or lbl == label
            ),
            None,
        )

        if match_idx is None:
            profiles.insert(0, (label, staff_id))
            match_idx = 0
        else:
            profiles[match_idx] = (label, staff_id if staff_id is not None else profiles[match_idx][1])

        self.duty_clinician_combo.setProfiles(profiles, active_index=match_idx)

        if staff_id is not None and hasattr(self, "in_clinician"):
            combo_idx = self.in_clinician.findData(staff_id)
            if combo_idx >= 0:
                self.in_clinician.setCurrentIndex(combo_idx)

    def _style_table(
        self,
        tbl: QTableWidget,
        stretch_cols: List[int],
        compact_cols: Optional[List[int]] = None,
    ) -> None:
        tbl.setAlternatingRowColors(True)
        tbl.setShowGrid(False)
        tbl.setFrameShape(QFrame.Shape.NoFrame)
        tbl.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        tbl.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        tbl.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        tbl.setWordWrap(False)
        tbl.verticalHeader().setVisible(False)
        tbl.verticalHeader().setDefaultSectionSize(42)
        hdr = tbl.horizontalHeader()
        hdr.setStretchLastSection(False)
        for c in range(tbl.columnCount()):
            if c in stretch_cols:
                hdr.setSectionResizeMode(c, QHeaderView.ResizeMode.Stretch)
            elif compact_cols and c in compact_cols:
                hdr.setSectionResizeMode(c, QHeaderView.ResizeMode.ResizeToContents)
            else:
                hdr.setSectionResizeMode(c, QHeaderView.ResizeMode.Interactive)

    def _build_ui(self) -> None:
        root = QWidget(objectName="RootCanvas")
        self.setCentralWidget(root)
        main_layout = QHBoxLayout(root)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # 1. Left Navigation Rail (Fixed Width)
        nav_rail = QFrame(objectName="NavRail")
        nav_rail.setFixedWidth(256)
        nav_layout = QVBoxLayout(nav_rail)
        nav_layout.setContentsMargins(18, 24, 18, 20)
        nav_layout.setSpacing(8)

        brand_row = QHBoxLayout()
        brand_row.setSpacing(10)
        brand_mark = QLabel()
        brand_mark.setFixedSize(26, 26)
        brand_mark.setAlignment(Qt.AlignmentFlag.AlignCenter)
        brand_mark.setPixmap(svg_pixmap("brand_mark", color="#FBF7F1", size=22))

        brand_text = QVBoxLayout()
        brand_text.setSpacing(1)
        brand = QLabel("VITA HEALTH", objectName="BrandTitle")
        sub = QLabel("Clinical Triage & Care OS", objectName="BrandSub")
        brand_text.addWidget(brand)
        brand_text.addWidget(sub)

        brand_row.addWidget(brand_mark)
        brand_row.addLayout(brand_text)
        nav_layout.addLayout(brand_row)
        nav_layout.addSpacing(18)

        self.btn_nav_triage = QPushButton("  Triage Command", objectName="NavBtn")
        self.btn_nav_intake = QPushButton("  Patient Intake", objectName="NavBtn")
        self.btn_nav_facilities = QPushButton("  Facilities & Audit", objectName="NavBtn")

        self._nav_buttons: List[Tuple[QPushButton, str]] = [
            (self.btn_nav_triage, "nav_triage"),
            (self.btn_nav_intake, "nav_intake"),
            (self.btn_nav_facilities, "nav_facilities"),
        ]

        for idx, (btn, icon_key) in enumerate(self._nav_buttons):
            btn.setIcon(svg_icon(icon_key, color="#E5D4C1", size=16))
            btn.setIconSize(QSize(16, 16))
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.clicked.connect(lambda _checked, i=idx: self._switch_page(i))
            nav_layout.addWidget(btn)

        nav_layout.addStretch()

        dpg_card = QLabel(
            "Clinical Care Standards\n"
            "• Open License: MIT\n"
            "• Formats: CSV & JSON\n"
            "• Privacy: PII Redaction + Audit"
        )
        dpg_card.setStyleSheet(
            "background-color: #20150E; color: #DFCBB5; border: 1px solid #36251A; "
            "padding: 12px; border-radius: 10px; font-size: 11px; line-height: 1.35;"
        )
        nav_layout.addWidget(dpg_card)
        nav_layout.addSpacing(10)

        duty_lbl = QLabel("ON-DUTY PROFILE")
        duty_lbl.setStyleSheet(
            "color: #C5AE96; font-size: 10px; font-weight: 700; letter-spacing: 0.7px;"
        )
        self.duty_clinician_combo = ClinicianProfileSwitcher()
        self.duty_clinician_combo.profileSelected.connect(self._on_duty_clinician_changed)
        nav_layout.addWidget(duty_lbl)
        nav_layout.addWidget(self.duty_clinician_combo)

        main_layout.addWidget(nav_rail)

        # 2. Center Stack + Fixed-Height Toast Slot
        center_container = QWidget()
        center_layout = QVBoxLayout(center_container)
        center_layout.setContentsMargins(0, 0, 0, 0)
        center_layout.setSpacing(0)

        self.pages = BackdropPageStack(BACKGROUND_IMAGE_PATH)
        self.pages.addWidget(self._build_triage_page())
        self.pages.addWidget(self._build_intake_page())
        self.pages.addWidget(self._build_facilities_audit_page())
        center_layout.addWidget(self.pages, stretch=1)

        self.toast_slot = QFrame(objectName="ToastBar")
        self.toast_slot.setFixedHeight(36)
        toast_row = QHBoxLayout(self.toast_slot)
        toast_row.setContentsMargins(24, 0, 24, 0)
        self.toast_label = QLabel("Ready · Connected to Supabase PostgreSQL")
        self.toast_label.setStyleSheet("color: #E3D1BE; font-weight: 600; font-size: 12px;")
        toast_row.addWidget(self.toast_label)
        toast_row.addStretch()
        center_layout.addWidget(self.toast_slot)

        self._toast_timer = QTimer(self)
        self._toast_timer.setSingleShot(True)
        self._toast_timer.timeout.connect(self._reset_toast)

        main_layout.addWidget(center_container, stretch=1)

        # 3. Slide-Over Clinical Inspector Drawer
        self.drawer = QFrame(objectName="InspectorDrawer")
        self.drawer.setMaximumWidth(0)
        self.drawer_opacity = QGraphicsOpacityEffect(self.drawer)
        self.drawer_opacity.setOpacity(0.0)
        self.drawer.setGraphicsEffect(self.drawer_opacity)
        self._build_inspector_drawer()
        main_layout.addWidget(self.drawer)

        self.drawer_width_anim = QPropertyAnimation(self.drawer, b"maximumWidth")
        self.drawer_width_anim.setDuration(220)
        self.drawer_width_anim.setEasingCurve(QEasingCurve.Type.OutCubic)

        self.drawer_fade_anim = QPropertyAnimation(self.drawer_opacity, b"opacity")
        self.drawer_fade_anim.setDuration(200)
        self.drawer_fade_anim.setEasingCurve(QEasingCurve.Type.OutCubic)

        self.drawer_group = QParallelAnimationGroup(self)
        self.drawer_group.addAnimation(self.drawer_width_anim)
        self.drawer_group.addAnimation(self.drawer_fade_anim)
        self.drawer_group.finished.connect(self._on_drawer_anim_finished)

        self._switch_page(0)

    def _on_duty_clinician_changed(self, _index: int) -> None:
        staff_id = self.duty_clinician_combo.currentData()
        label = self.duty_clinician_combo.currentText()
        if staff_id is not None and hasattr(self, "in_clinician"):
            idx = self.in_clinician.findData(staff_id)
            if idx >= 0 and self.in_clinician.currentIndex() != idx:
                self.in_clinician.setCurrentIndex(idx)
        self.current_clinician = {
            **(self.current_clinician or {}),
            "staff_id": staff_id,
            "label": label,
        }
        self._show_toast(f"Active profile: {label}")

    def _wire_form_pass_through(self) -> None:
        """Pressing Return/Enter in intake inputs advances focus cleanly to the next input."""
        ordered_fields: List[QWidget] = [
            self.in_health_id,
            self.in_first,
            self.in_last,
            self.in_dob,
            self.in_gender,
            self.in_phone,
            self.in_blood,
            self.in_allergies,
            self.in_emergency,
            self.in_facility,
            self.in_clinician,
            self.in_complaint,
            self.in_sys_bp,
            self.in_dia_bp,
            self.in_hr,
            self.in_temp,
            self.in_spo2,
        ]
        for i, field in enumerate(ordered_fields[:-1]):
            next_widget = ordered_fields[i + 1]
            if isinstance(field, QLineEdit):
                field.returnPressed.connect(lambda w=next_widget: w.setFocus())

    def _on_drawer_anim_finished(self) -> None:
        if self.drawer.maximumWidth() <= 0:
            self.drawer_opacity.setOpacity(0.0)
        else:
            self.drawer_opacity.setOpacity(1.0)

    def _show_toast(self, message: str, ms: int = 3200) -> None:
        self.toast_label.setText(message)
        self.toast_label.setStyleSheet("color: #FFFFFF; font-weight: 700; font-size: 12px;")
        self._toast_timer.start(ms)

    def _reset_toast(self) -> None:
        self.toast_label.setText("Ready · VITA HEALTH Clinical Workstation")
        self.toast_label.setStyleSheet("color: #C5AE96; font-weight: 600; font-size: 12px;")

    def _run_async(
        self,
        fn: Callable[[], Any],
        on_success: Callable[[Any], None],
        on_error: Optional[Callable[[str], None]] = None,
    ) -> None:
        worker = AsyncTaskWorker(fn, self)
        self._workers.append(worker)

        def _cleanup() -> None:
            if worker in self._workers:
                self._workers.remove(worker)
            worker.deleteLater()

        def _ok(val: Any) -> None:
            _cleanup()
            on_success(val)

        def _err(err: str) -> None:
            _cleanup()
            if on_error:
                on_error(err)
            else:
                QMessageBox.critical(self, "Operation Error", err)

        worker.succeeded.connect(_ok)
        worker.failed.connect(_err)
        worker.start()

    def trigger_sync(self) -> None:
        self.btn_sync.setEnabled(False)
        self.btn_sync.setText("Syncing...")
        self.sync_spinner.start()

        def _load_bundle() -> Dict[str, Any]:
            return {
                "encounters": self.repo.fetch_triage_board(),
                "facilities": self.repo.fetch_facilities(),
                "clinicians": self.repo.fetch_clinicians(),
            }

        def _done(bundle: Dict[str, Any]) -> None:
            self.registry.sync_all(bundle["encounters"])
            self._populate_dropdowns(bundle["facilities"], bundle["clinicians"])
            if self.current_clinician:
                self.set_active_clinician(self.current_clinician)
            self._apply_local_filters()
            self._update_kpis()
            self.sync_spinner.stop()
            self.btn_sync.setEnabled(True)
            self.btn_sync.setText("Sync Live Data")
            self._show_toast(f"Synced {len(bundle['encounters'])} encounters")

        def _fail(err: str) -> None:
            self.sync_spinner.stop()
            self.btn_sync.setEnabled(True)
            self.btn_sync.setText("Sync Live Data")
            QMessageBox.critical(self, "Supabase Sync Error", err)

        self._run_async(_load_bundle, _done, _fail)

    def _build_triage_page(self) -> QWidget:
        page = QWidget(objectName="PageCanvas")
        layout = QVBoxLayout(page)
        layout.setContentsMargins(24, 22, 24, 18)
        layout.setSpacing(16)

        top = QHBoxLayout()
        title_box = QVBoxLayout()
        title_box.setSpacing(3)
        h1 = QLabel("Live Clinical Triage Board", objectName="PageTitle")
        h_sub = QLabel(
            "Select an encounter to update vitals, view trend history, refer, prescribe, order labs, or log vaccines.",
            objectName="PageSubtitle",
        )
        title_box.addWidget(h1)
        title_box.addWidget(h_sub)
        top.addLayout(title_box)
        top.addStretch()

        self.sync_spinner = ArcSpinner(22)
        self.btn_csv = QPushButton("Export CSV", objectName="SecondaryBtn")
        self.btn_csv.setIcon(svg_icon("export", color="#120E0B", size=14))
        self.btn_csv.setIconSize(QSize(14, 14))
        self.btn_csv.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_csv.clicked.connect(lambda: self._export_dpg_data("csv"))

        self.btn_json = QPushButton("Export JSON", objectName="SecondaryBtn")
        self.btn_json.setIcon(svg_icon("export", color="#120E0B", size=14))
        self.btn_json.setIconSize(QSize(14, 14))
        self.btn_json.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_json.clicked.connect(lambda: self._export_dpg_data("json"))

        self.btn_sync = QPushButton("Sync Live Data", objectName="PrimaryBtn")
        self.btn_sync.setIcon(svg_icon("sync", color="#FBF7F1", size=14))
        self.btn_sync.setIconSize(QSize(14, 14))
        self.btn_sync.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_sync.clicked.connect(self.trigger_sync)

        top.addWidget(self.sync_spinner)
        top.addWidget(self.btn_csv)
        top.addWidget(self.btn_json)
        top.addWidget(self.btn_sync)
        layout.addLayout(top)

        kpi_row = QHBoxLayout()
        kpi_row.setSpacing(14)
        self.kpi_active = self._create_kpi_card("Active Encounters", "0", False)
        self.kpi_critical = self._create_kpi_card("Critical Acuity", "0", True)
        self.kpi_urgent = self._create_kpi_card("Urgent Queue", "0", False)
        self.kpi_spo2 = self._create_kpi_card("Cohort Mean SpO₂", "0%", False)
        for card in [self.kpi_active[0], self.kpi_critical[0], self.kpi_urgent[0], self.kpi_spo2[0]]:
            kpi_row.addWidget(card)
        layout.addLayout(kpi_row)

        filter_bar = QHBoxLayout()
        filter_bar.setSpacing(8)
        self.search_input = GlassLineEdit()
        self.search_input.setPlaceholderText("Search patient, Health ID, or complaint...  [Ctrl+K]")
        self.search_input.setFixedWidth(340)
        self.search_input.textChanged.connect(self._apply_local_filters)
        filter_bar.addWidget(self.search_input)

        self.filter_pills: Dict[str, PillFilterButton] = {}
        for tier in InMemoryTriageRegistry.TRIAGE_TIERS:
            pill = PillFilterButton(tier)
            pill.setSelected(tier == "ALL")
            pill.clicked.connect(lambda t=tier: self._set_triage_filter(t))
            self.filter_pills[tier] = pill
            filter_bar.addWidget(pill)

        filter_bar.addStretch()
        self.chk_active_only = ActiveCheckBox("Active Only", checked=True)
        self.chk_active_only.stateChanged.connect(self._apply_local_filters)
        filter_bar.addWidget(self.chk_active_only)
        layout.addLayout(filter_bar)

        self.table = GlassTableWidget(0, 10)
        self.table.setHorizontalHeaderLabels([
            "ID", "Acuity", "Status", "Patient", "Health ID", "Age/Sex",
            "Chief Complaint", "BP (mmHg)", "HR / Temp", "SpO₂"
        ])
        self._style_table(self.table, stretch_cols=[3, 6], compact_cols=[0, 1, 2, 5, 7, 8, 9])
        self.table.cellClicked.connect(self._on_row_selected)
        layout.addWidget(self.table, stretch=1)
        return page

    def _build_intake_page(self) -> QWidget:
        page = QWidget(objectName="PageCanvas")
        layout = QVBoxLayout(page)
        layout.setContentsMargins(24, 22, 24, 18)
        layout.setSpacing(16)

        top = QHBoxLayout()
        t_box = QVBoxLayout()
        t_box.setSpacing(3)
        title = QLabel("Patient Intake & Automated Triage", objectName="PageTitle")
        sub = QLabel(
            "Live physiological acuity preview + atomic PostgreSQL admission procedure.",
            objectName="PageSubtitle",
        )
        t_box.addWidget(title)
        t_box.addWidget(sub)
        top.addLayout(t_box)
        top.addStretch()

        self.acuity_preview_lbl = QLabel("Predicted Acuity: ROUTINE")
        self.acuity_preview_lbl.setMinimumWidth(195)
        self.acuity_preview_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.acuity_preview_lbl.setStyleSheet(
            "background-color: rgba(36, 24, 16, 0.82); color: #FBF7F1; "
            "border: 1px solid rgba(255, 252, 247, 0.36); padding: 8px 14px; "
            "border-radius: 16px; font-weight: 700; font-size: 11.5px; letter-spacing: 0.4px;"
        )
        top.addWidget(self.acuity_preview_lbl)
        layout.addLayout(top)

        card = GlassCardFrame(radius=11.0)
        wrap = QHBoxLayout(card)
        wrap.setContentsMargins(22, 20, 22, 20)
        wrap.setSpacing(28)

        left = QFormLayout()
        left.setVerticalSpacing(14)
        left.setHorizontalSpacing(14)
        left.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.ExpandingFieldsGrow)
        self.in_health_id = GlassLineEdit()
        self.in_health_id.setPlaceholderText("e.g. SL-PAT-9004")
        self.in_first = GlassLineEdit()
        self.in_last = GlassLineEdit()
        self.in_dob = ChevronDateEdit(QDate(1995, 1, 1))
        self.in_dob.setCalendarPopup(True)
        self.in_dob.setDisplayFormat("yyyy-MM-dd")
        self.in_gender = ChevronComboBox()
        self.in_gender.addItems(["Female", "Male", "Non-Binary", "Prefer Not to Say"])
        self.in_phone = GlassLineEdit()
        self.in_blood = ChevronComboBox()
        self.in_blood.addItems(["O+", "O-", "A+", "A-", "B+", "B-", "AB+", "AB-", "UNK"])
        self.in_allergies = GlassLineEdit()
        self.in_allergies.setText("None Recorded")
        self.in_emergency = GlassLineEdit()
        self.in_emergency.setPlaceholderText("Next of kin name & contact")

        left.addRow("National Health ID *:", self.in_health_id)
        left.addRow("First Name *:", self.in_first)
        left.addRow("Last Name *:", self.in_last)
        left.addRow("Date of Birth *:", self.in_dob)
        left.addRow("Gender:", self.in_gender)
        left.addRow("Phone:", self.in_phone)
        left.addRow("Blood Group:", self.in_blood)
        left.addRow("Allergies:", self.in_allergies)
        left.addRow("Emergency Contact *:", self.in_emergency)

        right = QFormLayout()
        right.setVerticalSpacing(14)
        right.setHorizontalSpacing(14)
        right.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.ExpandingFieldsGrow)
        self.in_facility = ChevronComboBox()
        self.in_clinician = ChevronComboBox()
        self.in_complaint = GlassLineEdit()
        self.in_complaint.setPlaceholderText("Presenting symptoms / chief complaint")

        self.in_sys_bp = ChevronSpinBox()
        self.in_sys_bp.setRange(40, 300)
        self.in_sys_bp.setValue(120)

        self.in_dia_bp = ChevronSpinBox()
        self.in_dia_bp.setRange(20, 200)
        self.in_dia_bp.setValue(80)

        self.in_hr = ChevronSpinBox()
        self.in_hr.setRange(20, 250)
        self.in_hr.setValue(78)

        self.in_temp = ChevronDoubleSpinBox()
        self.in_temp.setRange(30.0, 44.0)
        self.in_temp.setSingleStep(0.1)
        self.in_temp.setValue(36.9)

        self.in_spo2 = ChevronSpinBox()
        self.in_spo2.setRange(50, 100)
        self.in_spo2.setValue(98)

        self.in_notes = GlassTextEdit()
        self.in_notes.setFixedHeight(74)

        right.addRow("Facility:", self.in_facility)
        right.addRow("Clinician:", self.in_clinician)
        right.addRow("Chief Complaint *:", self.in_complaint)
        right.addRow("Systolic BP:", self.in_sys_bp)
        right.addRow("Diastolic BP:", self.in_dia_bp)
        right.addRow("Heart Rate (bpm):", self.in_hr)
        right.addRow("Temperature (°C):", self.in_temp)
        right.addRow("SpO₂ (%):", self.in_spo2)
        right.addRow("Clinical Notes:", self.in_notes)

        wrap.addLayout(left, 1)
        wrap.addLayout(right, 1)
        layout.addWidget(card)

        btn_row = QHBoxLayout()
        btn_row.addStretch()
        btn_submit = QPushButton("Admit Patient & Trigger Triage", objectName="PrimaryBtn")
        btn_submit.setIcon(svg_icon("nav_intake", color="#FBF7F1", size=15))
        btn_submit.setIconSize(QSize(15, 15))
        btn_submit.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_submit.clicked.connect(self._submit_new_admission)
        btn_row.addWidget(btn_submit)
        layout.addLayout(btn_row)
        layout.addStretch()
        return page

    def _build_facilities_audit_page(self) -> QWidget:
        page = QWidget(objectName="PageCanvas")
        layout = QVBoxLayout(page)
        layout.setContentsMargins(24, 22, 24, 18)
        layout.setSpacing(16)

        header_row = QHBoxLayout()
        h1 = QLabel("Facility Capacity & Audit Trail", objectName="PageTitle")
        header_row.addWidget(h1)
        header_row.addStretch()

        self.audit_spinner = ArcSpinner(22)
        self.audit_loading_lbl = QLabel("Loading facility metrics & audit logs...")
        self.audit_loading_lbl.setStyleSheet("color: #DFCBB5; font-weight: 600; font-size: 12px;")
        self.audit_loading_lbl.hide()

        self.btn_refresh_audit = QPushButton("Reload Telemetry", objectName="SecondaryBtn")
        self.btn_refresh_audit.setIcon(svg_icon("sync", color="#120E0B", size=14))
        self.btn_refresh_audit.setIconSize(QSize(14, 14))
        self.btn_refresh_audit.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_refresh_audit.clicked.connect(self._load_facilities_and_audit)

        header_row.addWidget(self.audit_spinner)
        header_row.addWidget(self.audit_loading_lbl)
        header_row.addWidget(self.btn_refresh_audit)
        layout.addLayout(header_row)

        self.fac_table = GlassTableWidget(0, 6)
        self.fac_table.setHorizontalHeaderLabels([
            "Facility", "District", "Beds", "Active", "Critical", "Occupancy %"
        ])
        self.fac_table.setFixedHeight(180)
        self._style_table(self.fac_table, stretch_cols=[0, 1, 5], compact_cols=[2, 3, 4])
        layout.addWidget(self.fac_table)

        audit_hdr_row = QHBoxLayout()
        audit_icon = QLabel()
        audit_icon.setPixmap(svg_pixmap("audit", color="#FBF7F1", size=16))
        audit_icon.setFixedSize(18, 18)

        lbl_audit = QLabel("Immutable Encounter Audit Log", objectName="SectionHeading")
        audit_hdr_row.addWidget(audit_icon)
        audit_hdr_row.addWidget(lbl_audit)
        audit_hdr_row.addStretch()

        self.audit_search_input = GlassLineEdit()
        self.audit_search_input.setPlaceholderText("Filter audit log by operation, record ID, or summary...")
        self.audit_search_input.setFixedWidth(340)
        self.audit_search_input.textChanged.connect(self._render_audit_table)
        audit_hdr_row.addWidget(self.audit_search_input)
        layout.addLayout(audit_hdr_row)

        self.audit_table = GlassTableWidget(0, 5)
        self.audit_table.setHorizontalHeaderLabels([
            "Audit ID", "Operation", "Record ID", "Event Summary", "Timestamp (UTC)"
        ])
        self._style_table(self.audit_table, stretch_cols=[3], compact_cols=[0, 1, 2, 4])
        layout.addWidget(self.audit_table, stretch=1)
        return page

    def _render_audit_table(self) -> None:
        query = (
            self.audit_search_input.text().strip().lower()
            if hasattr(self, "audit_search_input")
            else ""
        )
        if not query:
            filtered = self._audit_logs_cache
        else:
            filtered = [
                item for item in self._audit_logs_cache
                if query in str(item.get("audit_id", "")).lower()
                or query in str(item.get("operation", "")).lower()
                or query in str(item.get("record_id", "")).lower()
                or query in str(item.get("summary", "")).lower()
                or query in str(item.get("logged_at", "")).lower()
            ]

        self.audit_table.setRowCount(len(filtered))
        for r, item in enumerate(filtered):
            self.audit_table.setItem(r, 0, QTableWidgetItem(str(item["audit_id"])))
            self.audit_table.setItem(r, 1, QTableWidgetItem(str(item["operation"])))
            self.audit_table.setItem(r, 2, QTableWidgetItem(str(item["record_id"])))
            self.audit_table.setItem(r, 3, QTableWidgetItem(str(item["summary"])))
            self.audit_table.setItem(r, 4, QTableWidgetItem(str(item["logged_at"])))

    def _build_inspector_drawer(self) -> None:
        outer = QVBoxLayout(self.drawer)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        inner = QWidget()
        layout = QVBoxLayout(inner)
        layout.setContentsMargins(16, 18, 16, 18)
        layout.setSpacing(10)

        hdr = QHBoxLayout()
        self.lbl_drawer_title = QLabel("Encounter Inspector", objectName="SectionHeading")
        btn_close = QPushButton("✕", objectName="SecondaryBtn")
        btn_close.setFixedSize(28, 28)
        btn_close.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_close.clicked.connect(self._close_drawer)
        hdr.addWidget(self.lbl_drawer_title)
        hdr.addStretch()
        hdr.addWidget(btn_close)
        layout.addLayout(hdr)

        self.lbl_drawer_meta = QLabel("")
        self.lbl_drawer_meta.setWordWrap(True)
        self.lbl_drawer_meta.setStyleSheet(
            "color: #241810; background: rgba(251, 247, 241, 0.72); "
            "border: 1px solid rgba(217, 203, 183, 0.65); padding: 9px; "
            "border-radius: 9px; font-size: 12px;"
        )
        layout.addWidget(self.lbl_drawer_meta)

        self.inspector_tabs = QTabWidget()

        # Tab 1: Vitals, Referral, Discharge, Delete
        tab_vitals = QWidget()
        v_lay = QVBoxLayout(tab_vitals)
        v_lay.setSpacing(8)
        form = QFormLayout()
        form.setVerticalSpacing(10)
        self.ed_sys = ChevronSpinBox(); self.ed_sys.setRange(40, 300)
        self.ed_dia = ChevronSpinBox(); self.ed_dia.setRange(20, 200)
        self.ed_hr = ChevronSpinBox(); self.ed_hr.setRange(20, 250)
        self.ed_temp = ChevronDoubleSpinBox(); self.ed_temp.setRange(30.0, 44.0); self.ed_temp.setSingleStep(0.1)
        self.ed_spo2 = ChevronSpinBox(); self.ed_spo2.setRange(50, 100)
        self.ed_notes = GlassTextEdit(); self.ed_notes.setFixedHeight(62)

        form.addRow("Systolic BP:", self.ed_sys)
        form.addRow("Diastolic BP:", self.ed_dia)
        form.addRow("Heart Rate:", self.ed_hr)
        form.addRow("Temp (°C):", self.ed_temp)
        form.addRow("SpO₂ (%):", self.ed_spo2)
        form.addRow("Notes:", self.ed_notes)
        v_lay.addLayout(form)

        btn_save = QPushButton("Update Vitals & Snapshot", objectName="PrimaryBtn")
        btn_save.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_save.clicked.connect(self._save_drawer_updates)
        v_lay.addWidget(btn_save)

        ref_box = QFrame(objectName="SubPanel")
        ref_lay = QVBoxLayout(ref_box)
        ref_lay.setContentsMargins(8, 8, 8, 8)
        ref_lay.setSpacing(6)
        self.ref_facility_combo = ChevronComboBox()
        self.ref_reason_input = GlassLineEdit()
        self.ref_reason_input.setPlaceholderText("Referral reason...")
        btn_refer = QPushButton("Refer to Facility", objectName="SecondaryBtn")
        btn_refer.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_refer.clicked.connect(self._refer_selected)
        ref_lay.addWidget(QLabel("Inter-Facility Referral"))
        ref_lay.addWidget(self.ref_facility_combo)
        ref_lay.addWidget(self.ref_reason_input)
        ref_lay.addWidget(btn_refer)
        v_lay.addWidget(ref_box)

        act_row = QHBoxLayout()
        btn_discharge = QPushButton("Discharge", objectName="SecondaryBtn")
        btn_discharge.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_discharge.clicked.connect(self._discharge_selected)
        btn_delete = QPushButton("Delete", objectName="DangerBtn")
        btn_delete.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_delete.clicked.connect(self._delete_selected)
        act_row.addWidget(btn_discharge)
        act_row.addWidget(btn_delete)
        v_lay.addLayout(act_row)
        self.inspector_tabs.addTab(tab_vitals, "Vitals")

        # Tab 2: Prescriptions
        tab_rx = QWidget()
        rx_lay = QVBoxLayout(tab_rx)
        rx_lay.setSpacing(7)
        self.rx_med_input = GlassLineEdit(); self.rx_med_input.setPlaceholderText("Medication name")
        self.rx_dose_input = GlassLineEdit(); self.rx_dose_input.setPlaceholderText("Dosage (e.g. 500mg)")
        self.rx_freq_input = GlassLineEdit(); self.rx_freq_input.setPlaceholderText("Frequency (e.g. TID)")
        self.rx_days_spin = ChevronSpinBox(); self.rx_days_spin.setRange(1, 180); self.rx_days_spin.setValue(5)
        btn_add_rx = QPushButton("Issue Prescription", objectName="PrimaryBtn")
        btn_add_rx.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_add_rx.clicked.connect(self._add_prescription)

        self.rx_table = GlassTableWidget(0, 3)
        self.rx_table.setHorizontalHeaderLabels(["Med", "Regimen", "Dispensed"])
        self._style_table(self.rx_table, stretch_cols=[0, 1], compact_cols=[2])
        self.rx_table.cellClicked.connect(self._on_rx_cell_clicked)

        rx_lay.addWidget(self.rx_med_input)
        rx_lay.addWidget(self.rx_dose_input)
        rx_lay.addWidget(self.rx_freq_input)
        rx_lay.addWidget(self.rx_days_spin)
        rx_lay.addWidget(btn_add_rx)
        rx_lay.addWidget(self.rx_table, stretch=1)
        self.inspector_tabs.addTab(tab_rx, "Rx")

        # Tab 3: Labs
        tab_lab = QWidget()
        lab_lay = QVBoxLayout(tab_lab)
        lab_lay.setSpacing(7)
        self.lab_test_input = GlassLineEdit(); self.lab_test_input.setPlaceholderText("Test (e.g. Malaria RDT, CBC)")
        self.lab_specimen_combo = ChevronComboBox()
        self.lab_specimen_combo.addItems(["Blood", "Urine", "Sputum", "Swab"])
        btn_add_lab = QPushButton("Order Lab Test", objectName="PrimaryBtn")
        btn_add_lab.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_add_lab.clicked.connect(self._add_lab_order)

        self.lab_table = GlassTableWidget(0, 3)
        self.lab_table.setHorizontalHeaderLabels(["Test", "Spec", "Status"])
        self._style_table(self.lab_table, stretch_cols=[0, 2], compact_cols=[1])
        self.lab_table.cellClicked.connect(self._on_lab_cell_clicked)

        lab_lay.addWidget(self.lab_test_input)
        lab_lay.addWidget(self.lab_specimen_combo)
        lab_lay.addWidget(btn_add_lab)
        lab_lay.addWidget(self.lab_table, stretch=1)
        self.inspector_tabs.addTab(tab_lab, "Labs")

        # Tab 4: Vitals Trend History & Immunizations
        tab_hist = QWidget()
        h_lay = QVBoxLayout(tab_hist)
        h_lay.setSpacing(7)
        h_lay.addWidget(QLabel("Vitals Snapshot History"))
        self.vitals_hist_table = GlassTableWidget(0, 3)
        self.vitals_hist_table.setHorizontalHeaderLabels(["Time", "Acuity", "BP / SpO₂"])
        self.vitals_hist_table.setFixedHeight(130)
        self._style_table(self.vitals_hist_table, stretch_cols=[0, 2], compact_cols=[1])
        h_lay.addWidget(self.vitals_hist_table)

        h_lay.addWidget(QLabel("Log Immunization"))
        self.imm_vaccine_input = GlassLineEdit(); self.imm_vaccine_input.setPlaceholderText("Vaccine (e.g. Pentavalent, Measles)")
        self.imm_dose_spin = ChevronSpinBox(); self.imm_dose_spin.setRange(1, 10); self.imm_dose_spin.setValue(1)
        btn_add_imm = QPushButton("Record Vaccine Dose", objectName="SecondaryBtn")
        btn_add_imm.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_add_imm.clicked.connect(self._record_immunization)
        h_lay.addWidget(self.imm_vaccine_input)
        h_lay.addWidget(self.imm_dose_spin)
        h_lay.addWidget(btn_add_imm)

        self.imm_table = GlassTableWidget(0, 3)
        self.imm_table.setHorizontalHeaderLabels(["Vaccine", "Dose", "Date"])
        self._style_table(self.imm_table, stretch_cols=[0], compact_cols=[1, 2])
        h_lay.addWidget(self.imm_table, stretch=1)
        self.inspector_tabs.addTab(tab_hist, "Trend & Vax")

        layout.addWidget(self.inspector_tabs)
        scroll.setWidget(inner)
        outer.addWidget(scroll)

    def _create_kpi_card(self, title: str, initial: str, alert: bool) -> Tuple[QFrame, QLabel]:
        card = GlassCardFrame(radius=10.0)
        card.setMinimumHeight(92)
        box = QVBoxLayout(card)
        box.setContentsMargins(18, 18, 18, 18)
        box.setSpacing(6)
        lbl_t = QLabel(title, objectName="KpiLabel")
        lbl_v = QLabel(initial, objectName="KpiValueAlert" if alert else "KpiValue")
        box.addWidget(lbl_t)
        box.addWidget(lbl_v)
        return card, lbl_v

    def _wire_live_acuity_preview(self) -> None:
        for w in [self.in_sys_bp, self.in_hr, self.in_temp, self.in_spo2]:
            w.valueChanged.connect(self._update_acuity_preview)
        self._update_acuity_preview()

    def _update_acuity_preview(self) -> None:
        spo2 = self.in_spo2.value()
        sbp = self.in_sys_bp.value()
        hr = self.in_hr.value()
        temp = self.in_temp.value()

        if spo2 < 90 or sbp < 90 or sbp > 180 or hr > 130 or hr < 40 or temp >= 39.5:
            tier, style = "CRITICAL", "background-color: rgba(153, 27, 27, 0.86); color: #FFFFFF;"
        elif (90 <= spo2 <= 93) or temp >= 38.3 or (111 <= hr <= 130) or (160 <= sbp <= 180):
            tier, style = "URGENT", "background-color: rgba(146, 64, 14, 0.86); color: #FFFBEB;"
        elif temp >= 37.6 or (101 <= hr <= 110):
            tier, style = "PRIORITY", "background-color: rgba(62, 42, 30, 0.86); color: #FBF7F1;"
        else:
            tier, style = "ROUTINE", "background-color: rgba(36, 24, 16, 0.82); color: #FBF7F1;"

        self.acuity_preview_lbl.setText(f"Predicted Acuity: {tier}")
        self.acuity_preview_lbl.setStyleSheet(
            f"{style} border: 1px solid rgba(255, 252, 247, 0.36); padding: 8px 14px; "
            f"border-radius: 16px; font-weight: 700; font-size: 11.5px; letter-spacing: 0.4px;"
        )

    def _switch_page(self, index: int) -> None:
        self.pages.setCurrentIndex(index)
        for i, (btn, icon_key) in enumerate(self._nav_buttons):
            is_active = i == index
            btn.setProperty("active", is_active)
            btn.setIcon(svg_icon(icon_key, color="#120E0B" if is_active else "#E5D4C1", size=16))
            btn.style().unpolish(btn)
            btn.style().polish(btn)

        self.pages.repaint()
        current = self.pages.currentWidget()
        if current is not None:
            current.repaint()

        if index == 2:
            self._load_facilities_and_audit()

    def _bind_shortcuts(self) -> None:
        QShortcut(QKeySequence("Ctrl+K"), self, activated=self.search_input.setFocus)
        QShortcut(QKeySequence("Escape"), self, activated=self._close_drawer)

    def _populate_dropdowns(
        self, facilities: List[Dict[str, Any]], clinicians: List[Dict[str, Any]]
    ) -> None:
        if self.in_facility.count() == 0:
            for f in facilities:
                self.in_facility.addItem(f["facility_name"], f["facility_id"])
        if self.ref_facility_combo.count() == 0:
            for f in facilities:
                self.ref_facility_combo.addItem(f["facility_name"], f["facility_id"])
        if self.in_clinician.count() == 0:
            for c in clinicians:
                self.in_clinician.addItem(c["label"], c["staff_id"])
        if not getattr(self.duty_clinician_combo, "_profiles", None) and clinicians:
            self.duty_clinician_combo.setProfiles([(c["label"], c["staff_id"]) for c in clinicians])

    def _update_kpis(self) -> None:
        active, critical, urgent, avg_spo2 = self.registry.get_kpi_snapshot()
        self.kpi_active[1].setText(str(active))
        self.kpi_critical[1].setText(str(critical))
        self.kpi_urgent[1].setText(str(urgent))
        self.kpi_spo2[1].setText(f"{avg_spo2}%")

    def _set_triage_filter(self, tier: str) -> None:
        self.selected_triage_filter = tier
        for name, pill in self.filter_pills.items():
            pill.setSelected(name == tier)
        self._apply_local_filters()

    def _apply_local_filters(self) -> None:
        filtered = self.registry.filter_records(
            query=self.search_input.text(),
            triage_filter=self.selected_triage_filter,
            active_only=self.chk_active_only.isChecked(),
        )
        self._render_table(filtered)

    def _render_table(self, rows: List[ClinicalEncounter]) -> None:
        self.table.setRowCount(len(rows))
        acuity_palette = {
            "CRITICAL": ("#FEE2E2", "#991B1B"),
            "URGENT": ("#FEF3C7", "#92400E"),
            "PRIORITY": ("#EDE4D8", "#3E2A1E"),
            "ROUTINE": ("#F5F0E8", "#140E0A"),
        }
        bold = QFont()
        bold.setBold(True)

        for r_idx, enc in enumerate(rows):
            cells = [
                QTableWidgetItem(str(enc.encounter_id)),
                QTableWidgetItem(enc.triage_level),
                QTableWidgetItem(enc.status),
                QTableWidgetItem(enc.patient_name),
                QTableWidgetItem(enc.health_id),
                QTableWidgetItem(f"{enc.age_years}y / {enc.gender[0]}"),
                QTableWidgetItem(enc.chief_complaint),
                QTableWidgetItem(f"{enc.systolic_bp}/{enc.diastolic_bp}"),
                QTableWidgetItem(f"{enc.heart_rate_bpm} bpm · {enc.temperature_c}°C"),
                QTableWidgetItem(f"{enc.spo2_percent}%"),
            ]
            bg, fg = acuity_palette.get(enc.triage_level, ("#FBF7F1", "#120E0B"))
            cells[1].setBackground(QColor(bg))
            cells[1].setForeground(QColor(fg))
            cells[1].setFont(bold)

            for c_idx, item in enumerate(cells):
                item.setData(Qt.ItemDataRole.UserRole, enc.encounter_id)
                if c_idx in (0, 1, 2, 5, 7, 9):
                    item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                else:
                    item.setTextAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)
                self.table.setItem(r_idx, c_idx, item)

    def _on_row_selected(self, row: int, _col: int) -> None:
        enc_id = self.table.item(row, 0).data(Qt.ItemDataRole.UserRole)
        enc = self.registry.get_by_id(enc_id)
        if not enc:
            return
        self.selected_encounter = enc
        self.lbl_drawer_title.setText(f"Encounter #{enc.encounter_id} · {enc.triage_level}")
        self.lbl_drawer_meta.setText(
            f"Patient: {enc.patient_name} ({enc.health_id})\n"
            f"Blood: {enc.blood_group} | Allergies: {enc.allergies}\n"
            f"Facility: {enc.facility_name}"
        )
        self.ed_sys.setValue(enc.systolic_bp)
        self.ed_dia.setValue(enc.diastolic_bp)
        self.ed_hr.setValue(enc.heart_rate_bpm)
        self.ed_temp.setValue(enc.temperature_c)
        self.ed_spo2.setValue(enc.spo2_percent)
        self.ed_notes.setPlainText(enc.clinical_notes)
        self.ref_reason_input.clear()

        self._refresh_encounter_details(enc.encounter_id)

        self.drawer_opacity.setOpacity(1.0)
        self.drawer_group.stop()
        self.drawer_width_anim.setStartValue(self.drawer.maximumWidth())
        self.drawer_width_anim.setEndValue(420)
        self.drawer_fade_anim.setStartValue(1.0)
        self.drawer_fade_anim.setEndValue(1.0)
        self.drawer_group.start()

    def _close_drawer(self) -> None:
        self.drawer_group.stop()
        self.drawer_width_anim.setStartValue(self.drawer.maximumWidth())
        self.drawer_width_anim.setEndValue(0)
        self.drawer_fade_anim.setStartValue(self.drawer_opacity.opacity())
        self.drawer_fade_anim.setEndValue(0.0)
        self.drawer_group.start()

    def _refresh_encounter_details(self, encounter_id: int) -> None:
        def _fetch() -> Dict[str, Any]:
            pid = self.repo.fetch_patient_id_for_encounter(encounter_id)
            return {
                "rx": self.repo.fetch_prescriptions_for_encounter(encounter_id),
                "labs": self.repo.fetch_lab_orders_for_encounter(encounter_id),
                "history": self.repo.fetch_vitals_history(encounter_id),
                "patient_id": pid,
                "vax": self.repo.fetch_immunizations_for_patient(pid) if pid else [],
            }

        def _render(data: Dict[str, Any]) -> None:
            self.selected_patient_id = data["patient_id"]

            rxs = data["rx"]
            self.rx_table.setRowCount(len(rxs))
            for idx, r in enumerate(rxs):
                c0 = QTableWidgetItem(r["medication_name"])
                c0.setData(Qt.ItemDataRole.UserRole, (r["prescription_id"], r["dispensed"]))
                self.rx_table.setItem(idx, 0, c0)
                self.rx_table.setItem(idx, 1, QTableWidgetItem(f"{r['dosage']} · {r['frequency']}"))
                self.rx_table.setItem(idx, 2, QTableWidgetItem("YES" if r["dispensed"] else "NO"))

            labs = data["labs"]
            self.lab_table.setRowCount(len(labs))
            for idx, l in enumerate(labs):
                c0 = QTableWidgetItem(l["test_name"])
                c0.setData(Qt.ItemDataRole.UserRole, (l["lab_order_id"], l["status"], l["result_summary"]))
                self.lab_table.setItem(idx, 0, c0)
                self.lab_table.setItem(idx, 1, QTableWidgetItem(l["specimen_type"]))
                self.lab_table.setItem(idx, 2, QTableWidgetItem(f"{l['status']} · {l['result_summary']}"))

            hist = data["history"]
            self.vitals_hist_table.setRowCount(len(hist))
            for idx, h in enumerate(hist):
                self.vitals_hist_table.setItem(idx, 0, QTableWidgetItem(h["recorded_at"]))
                self.vitals_hist_table.setItem(idx, 1, QTableWidgetItem(h["triage_level"]))
                self.vitals_hist_table.setItem(
                    idx, 2, QTableWidgetItem(f"{h['systolic_bp']}/{h['diastolic_bp']} · {h['spo2_percent']}%")
                )

            vax = data["vax"]
            self.imm_table.setRowCount(len(vax))
            for idx, v in enumerate(vax):
                self.imm_table.setItem(idx, 0, QTableWidgetItem(v["vaccine_name"]))
                self.imm_table.setItem(idx, 1, QTableWidgetItem(f"Dose {v['dose_number']}"))
                self.imm_table.setItem(idx, 2, QTableWidgetItem(v["administered_on"]))

        self._run_async(_fetch, _render)

    def _add_prescription(self) -> None:
        if not self.selected_encounter or not self.rx_med_input.text().strip():
            return
        enc_id = self.selected_encounter.encounter_id
        med = self.rx_med_input.text().strip()
        dose = self.rx_dose_input.text().strip() or "Standard"
        freq = self.rx_freq_input.text().strip() or "As directed"
        days = self.rx_days_spin.value()

        def _run() -> None:
            self.repo.add_prescription_via_procedure(enc_id, med, dose, freq, days)

        def _ok(_res: Any) -> None:
            self.rx_med_input.clear()
            self.rx_dose_input.clear()
            self.rx_freq_input.clear()
            self._refresh_encounter_details(enc_id)
            self._show_toast(f"Issued '{med}' for Encounter #{enc_id}")

        self._run_async(_run, _ok)

    def _on_rx_cell_clicked(self, row: int, _col: int) -> None:
        if not self.selected_encounter:
            return
        meta = self.rx_table.item(row, 0).data(Qt.ItemDataRole.UserRole)
        if not meta:
            return
        rx_id, dispensed = meta
        enc_id = self.selected_encounter.encounter_id

        def _run() -> None:
            self.repo.toggle_prescription_dispensed(rx_id, not dispensed)

        def _ok(_res: Any) -> None:
            self._refresh_encounter_details(enc_id)
            self._show_toast("Prescription dispensing toggled")

        self._run_async(_run, _ok)

    def _add_lab_order(self) -> None:
        if not self.selected_encounter or not self.lab_test_input.text().strip():
            return
        enc_id = self.selected_encounter.encounter_id
        test = self.lab_test_input.text().strip()
        spec = self.lab_specimen_combo.currentText()

        def _run() -> None:
            self.repo.add_lab_order_via_procedure(enc_id, test, spec)

        def _ok(_res: Any) -> None:
            self.lab_test_input.clear()
            self._refresh_encounter_details(enc_id)
            self._show_toast(f"Lab order '{test}' queued")

        self._run_async(_run, _ok)

    def _on_lab_cell_clicked(self, row: int, _col: int) -> None:
        if not self.selected_encounter:
            return
        meta = self.lab_table.item(row, 0).data(Qt.ItemDataRole.UserRole)
        if not meta:
            return
        lab_id, cur_status, _summary = meta
        next_status = (
            "COMPLETED"
            if cur_status == "PENDING"
            else ("FLAGGED" if cur_status == "COMPLETED" else "PENDING")
        )
        enc_id = self.selected_encounter.encounter_id

        def _run() -> None:
            self.repo.update_lab_order_status(lab_id, next_status, f"Verified ({next_status})")

        def _ok(_res: Any) -> None:
            self._refresh_encounter_details(enc_id)
            self._show_toast(f"Lab marked {next_status}")

        self._run_async(_run, _ok)

    def _record_immunization(self) -> None:
        if (
            not self.selected_encounter
            or not self.selected_patient_id
            or not self.imm_vaccine_input.text().strip()
        ):
            return
        enc_id = self.selected_encounter.encounter_id
        pid = self.selected_patient_id
        vax = self.imm_vaccine_input.text().strip()
        dose = self.imm_dose_spin.value()
        clinician = self.duty_clinician_combo.currentText() or "On-Duty Clinician"

        def _run() -> None:
            self.repo.record_immunization_via_procedure(pid, vax, dose, clinician, None)

        def _ok(_res: Any) -> None:
            self.imm_vaccine_input.clear()
            self._refresh_encounter_details(enc_id)
            self._show_toast(f"Recorded {vax} (Dose {dose})")

        self._run_async(_run, _ok)

    def _submit_new_admission(self) -> None:
        if (
            not self.in_health_id.text().strip()
            or not self.in_first.text().strip()
            or not self.in_complaint.text().strip()
        ):
            QMessageBox.warning(
                self,
                "Missing Required Fields",
                "Health ID, First Name, and Chief Complaint are required.",
            )
            return
        staff_id = self.duty_clinician_combo.currentData() or self.in_clinician.currentData()
        payload = {
            "health_id": self.in_health_id.text().strip().upper(),
            "first_name": self.in_first.text().strip(),
            "last_name": self.in_last.text().strip() or "Unknown",
            "dob": self.in_dob.date().toString("yyyy-MM-dd"),
            "gender": self.in_gender.currentText(),
            "phone": self.in_phone.text().strip(),
            "blood_group": self.in_blood.currentText(),
            "allergies": self.in_allergies.text().strip(),
            "emergency_contact": self.in_emergency.text().strip() or "Not Provided",
            "staff_id": staff_id,
            "facility_id": self.in_facility.currentData(),
            "complaint": self.in_complaint.text().strip(),
            "sys_bp": self.in_sys_bp.value(),
            "dia_bp": self.in_dia_bp.value(),
            "hr": self.in_hr.value(),
            "temp": self.in_temp.value(),
            "spo2": self.in_spo2.value(),
            "notes": self.in_notes.toPlainText().strip(),
        }

        def _run() -> None:
            self.repo.admit_patient_via_procedure(payload)

        def _ok(_res: Any) -> None:
            self.in_health_id.clear()
            self.in_first.clear()
            self.in_last.clear()
            self.in_complaint.clear()
            self.in_notes.clear()
            self._switch_page(0)
            self.trigger_sync()
            self._show_toast("Patient admitted and triaged")

        self._run_async(_run, _ok)

    def _save_drawer_updates(self) -> None:
        if not self.selected_encounter:
            return
        enc_id = self.selected_encounter.encounter_id
        vals = (
            enc_id,
            self.ed_sys.value(),
            self.ed_dia.value(),
            self.ed_hr.value(),
            self.ed_temp.value(),
            self.ed_spo2.value(),
            self.ed_notes.toPlainText().strip(),
        )

        def _run() -> None:
            self.repo.update_vitals_via_procedure(*vals)

        def _ok(_res: Any) -> None:
            self._close_drawer()
            self.trigger_sync()
            self._show_toast(f"Updated vitals & snapshot for Encounter #{enc_id}")

        self._run_async(_run, _ok)

    def _refer_selected(self) -> None:
        if not self.selected_encounter:
            return
        enc_id = self.selected_encounter.encounter_id
        target_id = self.ref_facility_combo.currentData()
        reason = self.ref_reason_input.text().strip() or "Inter-facility transfer"

        def _run() -> None:
            self.repo.refer_encounter_via_procedure(enc_id, target_id, reason)

        def _ok(_res: Any) -> None:
            self._close_drawer()
            self.trigger_sync()
            self._show_toast(f"Referred Encounter #{enc_id}")

        self._run_async(_run, _ok)

    def _discharge_selected(self) -> None:
        if not self.selected_encounter:
            return
        enc_id = self.selected_encounter.encounter_id

        def _run() -> None:
            self.repo.discharge_via_procedure(enc_id, "DISCHARGED", "Stabilized and discharged.")

        def _ok(_res: Any) -> None:
            self._close_drawer()
            self.trigger_sync()
            self._show_toast(f"Discharged Encounter #{enc_id}")

        self._run_async(_run, _ok)

    def _delete_selected(self) -> None:
        if not self.selected_encounter:
            return
        enc_id = self.selected_encounter.encounter_id
        reply = QMessageBox.question(
            self,
            "Confirm Deletion",
            f"Delete Encounter #{enc_id}? This will be logged in the Audit Log.",
        )
        if reply != QMessageBox.StandardButton.Yes:
            return

        def _run() -> None:
            self.repo.delete_encounter(enc_id)

        def _ok(_res: Any) -> None:
            self._close_drawer()
            self.trigger_sync()
            self._show_toast(f"Deleted & audited Encounter #{enc_id}")

        self._run_async(_run, _ok)

    def _load_facilities_and_audit(self) -> None:
        self.btn_refresh_audit.setEnabled(False)
        self.audit_loading_lbl.show()
        self.audit_spinner.start()

        def _fetch() -> Dict[str, List[Dict[str, Any]]]:
            return {
                "facs": self.repo.fetch_facility_metrics(),
                "logs": self.repo.fetch_audit_logs(),
            }

        def _render(data: Dict[str, List[Dict[str, Any]]]) -> None:
            facs = data["facs"]
            self.fac_table.setRowCount(len(facs))
            for r, f in enumerate(facs):
                self.fac_table.setItem(r, 0, QTableWidgetItem(f["facility_name"]))
                self.fac_table.setItem(r, 1, QTableWidgetItem(f["district"]))
                self.fac_table.setItem(r, 2, QTableWidgetItem(str(f["bed_capacity"])))
                self.fac_table.setItem(r, 3, QTableWidgetItem(str(f["active_patients"])))
                self.fac_table.setItem(r, 4, QTableWidgetItem(str(f["critical_cases"])))

                cell_wrap = QWidget()
                cell_lay = QHBoxLayout(cell_wrap)
                cell_lay.setContentsMargins(8, 0, 8, 0)
                cell_lay.setAlignment(Qt.AlignmentFlag.AlignCenter)

                bar = QProgressBar()
                bar.setFixedSize(136, 18)
                pct = int(float(f["occupancy_pct"] or 0))
                bar.setValue(min(max(pct, 0), 100))
                bar.setFormat(f"{pct}%")
                cell_lay.addWidget(bar)
                self.fac_table.setCellWidget(r, 5, cell_wrap)

            self._audit_logs_cache = data["logs"]
            self._render_audit_table()

            self.audit_spinner.stop()
            self.audit_loading_lbl.hide()
            self.btn_refresh_audit.setEnabled(True)
            self._show_toast("Facility metrics & audit logs rendered")

        def _fail(err: str) -> None:
            self.audit_spinner.stop()
            self.audit_loading_lbl.hide()
            self.btn_refresh_audit.setEnabled(True)
            QMessageBox.critical(self, "Telemetry Load Error", err)

        self._run_async(_fetch, _render, _fail)

    def _export_dpg_data(self, fmt: str) -> None:
        records = self.registry.filter_records(
            query=self.search_input.text(),
            triage_filter=self.selected_triage_filter,
            active_only=self.chk_active_only.isChecked(),
        )
        if not records:
            self._show_toast("No matching encounters to export")
            return

        anon_reply = QMessageBox.question(
            self,
            "Privacy Protection",
            "Anonymize PII (Patient Names & National Health IDs) before exporting data?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        anonymize = anon_reply == QMessageBox.StandardButton.Yes
        rows = [r.to_open_dict(anonymize=anonymize) for r in records]

        ext = "csv" if fmt == "csv" else "json"
        path, _ = QFileDialog.getSaveFileName(self, f"Export {ext.upper()}", f"vita_health_export.{ext}")
        if not path:
            return

        if fmt == "csv":
            with open(path, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=rows[0].keys())
                writer.writeheader()
                writer.writerows(rows)
        else:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(rows, f, indent=2)

        self._show_toast(f"Exported {len(rows)} records to {path}")
NOIR_ESPRESSO_CREAM_QSS = """
QMainWindow, QWidget#RootCanvas {
    background-color: #140E0A;
    color: #FBF7F1;
    font-family: "Inter", -apple-system, BlinkMacSystemFont, "SF Pro Text", "Segoe UI", sans-serif;
    font-size: 13px;
}

/* Navigation Rail */
QFrame#NavRail {
    background-color: #140E0A;
    border-right: 1px solid rgba(255, 247, 237, 0.12);
}
QLabel#BrandTitle {
    color: #FBF7F1;
    font-size: 17px;
    font-weight: 800;
    letter-spacing: 1.6px;
}
QLabel#BrandSub {
    color: #BFA78E;
    font-size: 11px;
    font-weight: 500;
    letter-spacing: 0.2px;
}
QPushButton#NavBtn {
    background-color: transparent;
    color: #E5D4C1;
    text-align: left;
    padding: 10px 14px;
    border-radius: 10px;
    font-weight: 500;
    font-size: 13px;
    border: 1px solid transparent;
}
QPushButton#NavBtn:hover {
    background-color: rgba(255, 247, 237, 0.08);
    color: #FFFFFF;
    border-color: rgba(255, 247, 237, 0.14);
}
QPushButton#NavBtn:pressed {
    background-color: rgba(255, 247, 237, 0.14);
}
QPushButton#NavBtn[active="true"] {
    background-color: rgba(251, 247, 241, 0.92);
    color: #120E0B;
    font-weight: 700;
}

/* Main Page Canvas Over Darkened Image Backdrop */
QWidget#PageCanvas {
    background: transparent;
}
QLabel#PageTitle {
    font-size: 22px;
    font-weight: 800;
    letter-spacing: -0.35px;
    color: #FBF7F1;
}
QLabel#PageSubtitle {
    font-size: 12.5px;
    font-weight: 400;
    color: #E5D4C1;
}
QLabel#SectionHeading {
    font-size: 14.5px;
    font-weight: 700;
    letter-spacing: -0.15px;
    color: #FBF7F1;
}

/* Glassmorphism Cards & Panels */
QFrame#SurfaceCard {
    background-color: rgba(255, 250, 244, 0.56);
    border: 1px solid rgba(255, 252, 247, 0.44);
    border-radius: 10px;
}
QFrame#SubPanel {
    background-color: rgba(247, 242, 233, 0.65);
    border: 1px solid rgba(255, 252, 247, 0.42);
    border-radius: 10px;
}
QFrame#ToastBar {
    background-color: rgba(20, 14, 10, 0.92);
    border-top: 1px solid rgba(255, 247, 237, 0.14);
}
QLabel#KpiLabel {
    color: #2B1C13;
    font-size: 10.5px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.8px;
}
QLabel#KpiValue {
    color: #120E0B;
    font-size: 26px;
    font-weight: 800;
    letter-spacing: -0.5px;
}
QLabel#KpiValueAlert {
    color: #991B1B;
    font-size: 26px;
    font-weight: 800;
    letter-spacing: -0.5px;
}

/* Glassmorphism Form Inputs & Box-Free Chevrons */
QLineEdit, QTextEdit {
    background-color: transparent;
    border: 1px solid rgba(255, 252, 247, 0.46);
    border-radius: 8px;
    padding: 6px 10px;
    color: #120E0B;
    font-size: 13px;
    selection-background-color: #241810;
    selection-color: #FFFFFF;
}
QLineEdit:hover, QTextEdit:hover {
    border-color: rgba(255, 255, 255, 0.72);
}
QLineEdit:focus, QTextEdit:focus {
    border: 1.5px solid #241810;
}

QSpinBox, QDoubleSpinBox, QDateEdit {
    background-color: rgba(255, 252, 247, 0.58);
    border: 1px solid rgba(255, 252, 247, 0.46);
    border-radius: 8px;
    padding: 6px 26px 6px 10px;
    color: #120E0B;
    font-size: 13px;
    selection-background-color: #241810;
    selection-color: #FFFFFF;
}
QSpinBox:hover, QDoubleSpinBox:hover, QDateEdit:hover {
    background-color: rgba(255, 253, 250, 0.74);
    border-color: rgba(255, 255, 255, 0.72);
}
QSpinBox:focus, QDoubleSpinBox:focus, QDateEdit:focus {
    background-color: rgba(255, 254, 251, 0.88);
    border: 1.5px solid #241810;
}

QSpinBox::up-button, QSpinBox::down-button,
QDoubleSpinBox::up-button, QDoubleSpinBox::down-button,
QDateEdit::up-button, QDateEdit::down-button,
QDateEdit::drop-down {
    width: 0px;
    height: 0px;
    border: none;
    background: transparent;
    image: none;
}

QSpinBox::up-arrow, QSpinBox::down-arrow,
QDoubleSpinBox::up-arrow, QDoubleSpinBox::down-arrow,
QDateEdit::up-arrow, QDateEdit::down-arrow,
QDateEdit::drop-down:hover, QDateEdit::down-arrow:hover {
    image: none;
    width: 0px;
    height: 0px;
    border: none;
    background: transparent;
}

QComboBox {
    background-color: rgba(255, 252, 247, 0.58);
    color: #120E0B;
    border: 1px solid rgba(255, 252, 247, 0.46);
    border-radius: 8px;
    padding: 6px 26px 6px 10px;
    font-size: 13px;
    selection-background-color: #241810;
    selection-color: #FFFFFF;
}
QComboBox:hover {
    background-color: rgba(255, 253, 250, 0.74);
    border-color: rgba(255, 255, 255, 0.72);
}
QComboBox:focus {
    background-color: rgba(255, 254, 251, 0.88);
    border: 1.5px solid #241810;
}
QComboBox::drop-down {
    subcontrol-origin: content;
    subcontrol-position: center right;
    width: 18px;
    border: none;
    background: transparent;
}
QComboBox::down-arrow {
    image: none;
    width: 0px;
    height: 0px;
    border: none;
    background: transparent;
}
QComboBox QAbstractItemView {
    background-color: rgba(255, 252, 247, 0.96);
    color: #120E0B;
    border: 1px solid #D5C5B0;
    border-radius: 8px;
    selection-background-color: #241810;
    selection-color: #FBF7F1;
    padding: 4px;
}

/* Glass Action Buttons */
QPushButton#PrimaryBtn {
    background-color: rgba(36, 24, 16, 0.84);
    color: #FBF7F1;
    border: 1px solid rgba(255, 247, 237, 0.28);
    border-radius: 9px;
    padding: 8px 15px;
    font-weight: 700;
    font-size: 12.5px;
}
QPushButton#PrimaryBtn:hover {
    background-color: rgba(58, 39, 27, 0.92);
    border-color: rgba(255, 252, 247, 0.48);
}
QPushButton#PrimaryBtn:pressed {
    background-color: rgba(18, 14, 11, 0.96);
}
QPushButton#PrimaryBtn:disabled {
    background-color: rgba(154, 140, 126, 0.55);
    color: #F3EFEA;
}

QPushButton#SecondaryBtn {
    background-color: rgba(255, 252, 247, 0.62);
    color: #120E0B;
    border: 1px solid rgba(255, 252, 247, 0.48);
    border-radius: 9px;
    padding: 7px 13px;
    font-weight: 600;
    font-size: 12.5px;
}
QPushButton#SecondaryBtn:hover {
    background-color: rgba(255, 253, 250, 0.82);
    border-color: rgba(255, 255, 255, 0.75);
}
QPushButton#SecondaryBtn:pressed {
    background-color: rgba(231, 220, 203, 0.85);
}
QPushButton#SecondaryBtn:disabled {
    background-color: rgba(245, 242, 237, 0.45);
    color: #675344;
}

QPushButton#DangerBtn {
    background-color: rgba(254, 242, 242, 0.68);
    color: #991B1B;
    border: 1px solid rgba(229, 180, 180, 0.65);
    border-radius: 9px;
    padding: 7px 13px;
    font-weight: 600;
    font-size: 12.5px;
}
QPushButton#DangerBtn:hover {
    background-color: rgba(254, 242, 242, 0.88);
    border-color: #991B1B;
}
QPushButton#DangerBtn:pressed {
    background-color: rgba(254, 226, 226, 0.92);
}

/* Glassmorphism Tables */
QTableWidget {
    background-color: transparent;
    alternate-background-color: rgba(247, 240, 230, 0.42);
    border: 1px solid rgba(255, 252, 247, 0.44);
    border-radius: 11px;
    gridline-color: rgba(18, 14, 11, 0.08);
    selection-background-color: rgba(36, 24, 16, 0.22);
    selection-color: #120E0B;
    color: #120E0B;
    font-size: 12.5px;
}
QTableWidget::item:hover {
    background-color: rgba(255, 253, 250, 0.68);
}
QHeaderView::section {
    background-color: rgba(244, 237, 226, 0.76);
    color: #120E0B;
    font-weight: 700;
    font-size: 10.5px;
    text-transform: uppercase;
    letter-spacing: 0.65px;
    padding: 9px 8px;
    border: none;
    border-bottom: 1px solid rgba(255, 252, 247, 0.48);
}

/* Compact Occupancy Progress Bar */
QProgressBar {
    background-color: rgba(20, 14, 10, 0.16);
    border: 1px solid rgba(36, 24, 16, 0.24);
    border-radius: 8px;
    text-align: center;
    color: #120E0B;
    font-size: 10.5px;
    font-weight: 700;
}
QProgressBar::chunk {
    background-color: rgba(36, 24, 16, 0.78);
    border-radius: 7px;
}

/* Drawer & ScrollArea */
QFrame#InspectorDrawer {
    background-color: rgba(255, 251, 245, 0.92);
    border-left: 1px solid rgba(217, 203, 183, 0.75);
}
QFrame#InspectorDrawer QLabel#SectionHeading {
    color: #120E0B;
}
QFrame#InspectorDrawer QSpinBox,
QFrame#InspectorDrawer QDoubleSpinBox,
QFrame#InspectorDrawer QComboBox {
    background-color: rgba(255, 255, 255, 0.78);
    border: 1px solid rgba(180, 162, 138, 0.55);
}
QScrollArea {
    border: none;
    background: transparent;
}
QTabWidget::pane {
    border: 1px solid rgba(217, 203, 183, 0.65);
    border-radius: 10px;
    background: rgba(255, 252, 247, 0.68);
}
QTabBar::tab {
    background: rgba(244, 237, 226, 0.72);
    color: #3B291D;
    padding: 7px 11px;
    border-top-left-radius: 8px;
    border-top-right-radius: 8px;
    margin-right: 3px;
    font-weight: 600;
    font-size: 12px;
}
QTabBar::tab:hover {
    background: rgba(233, 222, 201, 0.88);
}
QTabBar::tab:selected {
    background: #241810;
    color: #FBF7F1;
}
"""
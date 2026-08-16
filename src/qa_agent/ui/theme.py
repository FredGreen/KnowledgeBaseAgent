"""Theme and QSS styles for the application."""

PRIMARY = "#4F6BFF"
SUCCESS = "#22A06B"
INFO = "#2E90FA"
WARNING = "#F5A623"
ERROR = "#E5484D"
NEUTRAL = "#6B7280"

BG_PRIMARY = "#FFFFFF"
BG_SECONDARY = "#F8F9FA"
BG_TERTIARY = "#F0F1F3"
TEXT_PRIMARY = "#1A1A2E"
TEXT_SECONDARY = "#6B7280"
BORDER = "#E5E7EB"

BUBBLE_USER_BG = "#EEF2FF"
BUBBLE_AI_BG = "#F8F9FA"


def get_stylesheet() -> str:
    return f"""
    QMainWindow, QWidget {{
        background-color: {BG_PRIMARY};
        color: {TEXT_PRIMARY};
        font-family: "PingFang SC", "Microsoft YaHei", "HarmonyOS Sans", sans-serif;
        font-size: 14px;
    }}

    /* Sidebar */
    #sidebar {{
        background-color: {BG_SECONDARY};
        border-right: 1px solid {BORDER};
    }}

    #sidebar QPushButton {{
        text-align: left;
        padding: 8px 16px;
        border: none;
        border-radius: 6px;
        background: transparent;
        color: {TEXT_PRIMARY};
    }}
    #sidebar QPushButton:hover {{
        background-color: {BG_TERTIARY};
    }}
    #sidebar QPushButton[active="true"] {{
        background-color: {PRIMARY};
        color: white;
    }}

    /* Top toolbar */
    #toolbar {{
        background-color: {BG_PRIMARY};
        border-bottom: 1px solid {BORDER};
        padding: 8px 16px;
    }}

    /* Buttons */
    QPushButton#primary-btn {{
        background-color: {PRIMARY};
        color: white;
        border: none;
        border-radius: 6px;
        padding: 8px 20px;
        font-weight: 600;
    }}
    QPushButton#primary-btn:hover {{
        background-color: #3D56E0;
    }}
    QPushButton#primary-btn:disabled {{
        background-color: {NEUTRAL};
    }}

    QPushButton#secondary-btn {{
        background-color: transparent;
        color: {PRIMARY};
        border: 1px solid {PRIMARY};
        border-radius: 6px;
        padding: 6px 16px;
    }}
    QPushButton#secondary-btn:hover {{
        background-color: {BUBBLE_USER_BG};
    }}

    QPushButton#icon-btn {{
        background: transparent;
        border: none;
        border-radius: 4px;
        padding: 4px 8px;
        font-size: 16px;
    }}
    QPushButton#icon-btn:hover {{
        background-color: {BG_TERTIARY};
    }}

    /* Message bubbles */
    QWidget#bubble-user {{
        background-color: {BUBBLE_USER_BG};
        border-radius: 10px;
        padding: 12px 16px;
    }}
    QWidget#bubble-ai {{
        background-color: {BUBBLE_AI_BG};
        border-radius: 10px;
        padding: 12px 16px;
        border: 1px solid {BORDER};
    }}

    /* Route badge */
    QLabel#route-badge {{
        font-size: 12px;
        color: {TEXT_SECONDARY};
        padding: 2px 8px;
        border-radius: 4px;
        background-color: {BG_TERTIARY};
    }}

    /* Status indicators */
    QLabel#status-done {{
        color: {SUCCESS};
    }}
    QLabel#status-parsing {{
        color: {INFO};
    }}
    QLabel#status-failed {{
        color: {ERROR};
    }}
    QLabel#status-queued {{
        color: {WARNING};
    }}

    /* Input area */
    QTextEdit#chat-input {{
        border: 1px solid {BORDER};
        border-radius: 8px;
        padding: 10px;
        background-color: {BG_PRIMARY};
        font-size: 14px;
    }}
    QTextEdit#chat-input:focus {{
        border-color: {PRIMARY};
    }}

    /* Scrollbar */
    QScrollBar:vertical {{
        width: 6px;
        background: transparent;
    }}
    QScrollBar::handle:vertical {{
        background: {NEUTRAL};
        border-radius: 3px;
        min-height: 30px;
    }}
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
        height: 0px;
    }}

    /* Tab widget */
    QTabWidget::pane {{
        border: 1px solid {BORDER};
        border-radius: 6px;
        padding: 8px;
    }}
    QTabBar::tab {{
        padding: 8px 16px;
        border: none;
        border-bottom: 2px solid transparent;
    }}
    QTabBar::tab:selected {{
        border-bottom-color: {PRIMARY};
        color: {PRIMARY};
        font-weight: 600;
    }}

    /* Table */
    QTableWidget {{
        border: none;
        gridline-color: {BORDER};
        alternate-background-color: {BG_SECONDARY};
    }}
    QTableWidget::item {{
        padding: 8px;
    }}
    QHeaderView::section {{
        background-color: {BG_SECONDARY};
        padding: 8px;
        border: none;
        border-bottom: 1px solid {BORDER};
        font-weight: 600;
    }}

    /* Slider */
    QSlider::groove:horizontal {{
        height: 4px;
        background: {BG_TERTIARY};
        border-radius: 2px;
    }}
    QSlider::handle:horizontal {{
        width: 16px;
        height: 16px;
        margin: -6px 0;
        background: {PRIMARY};
        border-radius: 8px;
    }}

    /* Combo box */
    QComboBox {{
        border: 1px solid {BORDER};
        border-radius: 6px;
        padding: 6px 12px;
        background: {BG_PRIMARY};
    }}
    QComboBox:hover {{
        border-color: {PRIMARY};
    }}

    /* Progress bar */
    QProgressBar {{
        border: none;
        border-radius: 4px;
        background-color: {BG_TERTIARY};
        height: 8px;
        text-align: center;
    }}
    QProgressBar::chunk {{
        background-color: {PRIMARY};
        border-radius: 4px;
    }}

    /* Line edit */
    QLineEdit {{
        border: 1px solid {BORDER};
        border-radius: 6px;
        padding: 6px 12px;
        background: {BG_PRIMARY};
    }}
    QLineEdit:focus {{
        border-color: {PRIMARY};
    }}

    /* Group box */
    QGroupBox {{
        border: 1px solid {BORDER};
        border-radius: 8px;
        margin-top: 12px;
        padding-top: 16px;
        font-weight: 600;
    }}
    QGroupBox::title {{
        subcontrol-origin: margin;
        left: 12px;
        padding: 0 6px;
    }}

    /* Status bar */
    QStatusBar {{
        background-color: {BG_SECONDARY};
        border-top: 1px solid {BORDER};
        font-size: 12px;
        color: {TEXT_SECONDARY};
    }}

    /* Tooltip */
    QToolTip {{
        background-color: {TEXT_PRIMARY};
        color: {BG_PRIMARY};
        border: none;
        border-radius: 4px;
        padding: 4px 8px;
    }}
    """

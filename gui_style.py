style = """
    QWidget {
        background-color: #1e1e2d;
        color: #ffffff;
        font-family: 'Segoe UI', Arial, sans-serif;
    }
    #leftContainer {
        background-color: #25253d;
        border-right: 1px solid #3a3a5a;
    }
    #header {
        font-size: 26px;
        font-weight: bold;
        color: #ffffff;
        padding-bottom: 8px;
        border-bottom: 2px solid #4facfe;
    }
    #subtitle {
        font-size: 14px;
        color: #a6c1ee;
        padding-bottom: 15px;
    }
    #graphTitle {
        font-size: 20px;
        font-weight: bold;
        color: #a6c1ee;
    }
    #inputLabel {
        font-size: 13px;
        font-weight: bold;
        color: #a6c1ee;
        margin-bottom: 3px;
    }
    QTextEdit {
        background-color: #2a2a45;
        border: 1px solid #3a3a5a;
        border-radius: 6px;
        color: #ffffff;
        padding: 10px;
        font-size: 14px;
    }
    QTextEdit:focus {
        border: 1px solid #4facfe;
    }
    QComboBox {
        background-color: #2a2a45;
        border: 1px solid #3a3a5a;
        border-radius: 6px;
        padding: 8px;
        font-size: 14px;
        color: #ffffff;
    }
    QComboBox:hover {
        border: 1px solid #4facfe;
    }
    QComboBox::drop-down {
        border: none;
    }
    QComboBox QAbstractItemView {
        background-color: #2a2a45;
        color: #ffffff;
        selection-background-color: #4facfe;
        border: 1px solid #3a3a5a;
        outline: none;
    }
    #actionButton {
        background-color: #4facfe;
        color: #ffffff;
        border: none;
        padding: 12px 20px;
        border-radius: 8px;
        font-weight: bold;
        font-size: 14px;
    }
    #actionButton:hover {
        background-color: #3b99e6;
    }
    #actionButton:disabled {
        background-color: #3a3a5a;
        color: #888888;
    }
    QMessageBox {
        background-color: #25253d;
    }
    QMessageBox QLabel {
        color: #ffffff;
        font-size: 14px;
    }
    QMessageBox QPushButton {
        background-color: #4facfe;
        color: white;
        border-radius: 4px;
        padding: 8px 16px;
        min-width: 80px;
    }
    QSplitter::handle:horizontal {
        background-color: #3a3a5a;
        width: 2px;
    }
    #infoLabel {
        font-size: 13px;
        color: #a6c1ee;
        font-style: italic;
    }
    #statsLabel {
        font-size: 12px;
        color: #ffffff;
        background-color: #2a2a45;
        padding: 8px 12px;
        border-radius: 6px;
        border: 1px solid #3a3a5a;
    }
    QToolTip {
        background-color: #f0f0f0; /* Светлый фон для контраста */
        color: #1e1e2d; /* Темный текст */
        border: 1px solid #4facfe; /* Яркая рамка */
        padding: 5px;
        border-radius: 4px;
        font-size: 13px;
        opacity: 230; /* Небольшая прозрачность */
    }
"""
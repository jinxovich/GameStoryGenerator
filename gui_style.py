style="""
            QWidget {
                background-color: #1e1e2d;
                color: #ffffff;
                font-family: 'Segoe UI', Arial, sans-serif;
            }
            #leftContainer {
                background-color: #25253d;
                border-right: 1px solid #3a3a5a;
                min-width: 350px;
            }
            #rightContainer {
                background-color: #1e1e2d;
            }
            #header {
                font-size: 28px;
                font-weight: bold;
                color: #ffffff;
                padding-bottom: 10px;
                border-bottom: 2px solid #4facfe;
            }
            #subtitle {
                font-size: 14px;
                color: #a6c1ee;
                font-style: italic;
                padding-bottom: 10px;
            }
            #graphTitle {
                font-size: 20px;
                font-weight: bold;
                color: #a6c1ee;
                padding: 15px;
            }
            #infoTitle {
                font-size: 16px;
                font-weight: bold;
                color: #a6c1ee;
                padding-bottom: 10px;
                border-bottom: 1px solid #3a3a5a;
                margin-bottom: 10px;
            }
            #storyInfo {
                font-size: 14px;
                color: #ffffff;
                line-height: 1.5;
            }
            #statsInfo {
                font-size: 14px;
                color: #ffffff;
                line-height: 1.5;
                font-family: 'Consolas', 'Monaco', monospace;
            }
            #inputLabel {
                font-size: 14px;
                font-weight: bold;
                color: #a6c1ee;
                margin-bottom: 5px;
            }
            #textEdit {
                background-color: #2a2a45;
                border: 2px solid #3a3a5a;
                border-radius: 8px;
                color: #ffffff;
                padding: 12px;
                font-size: 14px;
                selection-background-color: #4facfe;
                min-width: 300px;
            }
            #textEdit:focus {
                border: 2px solid #4facfe;
            }
            #comboBox {
                background-color: #2a2a45;
                border: 2px solid #3a3a5a;
                border-radius: 8px;
                color: #ffffff;
                padding: 8px;
                font-size: 14px;
                min-height: 40px;
                min-width: 300px;
            }
            #comboBox:hover {
                border: 2px solid #4facfe;
            }
            #comboBox::drop-down {
                border: none;
                width: 30px;
                padding-right: 5px;
            }
            #comboBox QAbstractItemView {
                background-color: #2a2a45;
                color: #ffffff;
                selection-background-color: #4facfe;
                selection-color: #ffffff;
                border: 2px solid #3a3a5a;
                font-size: 14px;
                padding: 8px;
                outline: none;
                min-width: 200px;
            }
            #graphFrame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #25253d, stop:1 #1e1e2d);
                border-radius: 12px;
                border: 1px solid #3a3a5a;
                min-width: 700px;
                min-height: 500px;
            }
            #infoFrame {
                background-color: #25253d;
                border-radius: 8px;
                border: 1px solid #3a3a5a;
                min-height: 150px;
            }
            #actionButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #667eea, stop:1 #764ba2);
                color: #ffffff;
                border: none;
                padding: 12px 20px;
                border-radius: 8px;
                font-weight: bold;
                font-size: 14px;
                min-width: 150px;
            }
            #actionButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #5a6fd8, stop:1 #6a4190);
            }
            #actionButton:pressed {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #4e5bc7, stop:1 #5d3980);
            }
            #actionButton:disabled {
                background-color: #3a3a5a;
                color: #888888;
            }
            QCheckBox {
                spacing: 10px;
                font-size: 14px;
                color: #a6c1ee;
                padding: 5px;
            }
            QCheckBox::indicator {
                width: 20px;
                height: 20px;
                border: 2px solid #3a3a5a;
                border-radius: 5px;
                background-color: #2a2a45;
            }
            QCheckBox::indicator:hover {
                border: 2px solid #4facfe;
            }
            QCheckBox::indicator:checked {
                background-color: #4facfe;
                border: 2px solid #4facfe;
            }
            QMessageBox {
                background-color: #25253d;
                color: #ffffff;
            }
            QMessageBox QLabel {
                color: #ffffff;
                font-size: 14px;
            }
            QMessageBox QPushButton {
                background-color: #4facfe;
                color: #ffffff;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
                min-width: 80px;
            }
            QMessageBox QPushButton:hover {
                background-color: #3a7bd5;
            }
            QSplitter::handle:horizontal {
                background-color: #3a3a5a;
                width: 2px;
            }
            QSplitter::handle:horizontal:hover {
                background-color: #4facfe;
            }
            QToolTip {
                background-color: #ffffff;
                color: #1e1e2d;
                border: 2px solid #4facfe;
                border-radius: 8px;
                padding: 8px 12px;
                font-size: 12px;
                font-family: 'Segoe UI', Arial, sans-serif;
                font-weight: normal;
                opacity: 240;
            }
            #infoLabel {
                font-size: 14px;
                color: #a6c1ee;
                font-style: italic;
                padding: 5px;
            }
            #statsLabel {
                font-size: 12px;
                color: #ffffff;
                background-color: #2a2a45;
                padding: 8px 12px;
                border-radius: 6px;
                border: 1px solid #3a3a5a;
                font-family: 'Consolas', 'Monaco', monospace;
            }
        """
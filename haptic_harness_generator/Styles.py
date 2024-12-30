class Styles:
    def __init__(self):
        self.colors = {
            "gray": "#333333",
            "lightGray": "#777777",
            "secondaryGray": "#444444",
            "borderGray": "#999999",
            "secondaryGreen": "#254f32",
            "green": "#339955",
        }
        self.styleSheet = """
        * {
            background-color: @gray;
            color: white;
            border: none;
            border: none;
            font-size: 16px;
        }
        
        #totalBackground {
            background-color: @secondaryGray;
        }


        QLabel {
            font-size: 16px; 
            padding-bottom: 3px; 
            padding-top: 3px;
        } 

        QRadioButton::indicator {
            width: 18px;
            height: 18px;
            border-radius: 9px;
            border: 1px solid @borderGray;
            background: @gray;
        }

        QRadioButton::indicator:hover {
            background: @lightGray;
        }

        QRadioButton::indicator:checked {
            background: @secondaryGreen;
        }

        QPushButton {
            border-radius: 10px; 
            border: 1px solid @lightGray;
            width: 200px;
            height: 50px;
            background-color: @gray;
        }

        QPushButton:hover {
            background-color: @lightGray;
        }

        QLineEdit{
            padding: 5px;
            border: 1px solid @borderGray;
            border-radius: 5px;
            width: 200px;
        }
        QTabWidget::pane { /* The tab widget frame */
            border-top: 1px solid @borderGray;
        }

        QTabBar {
            background-color: @secondaryGray;
        }

        QTabBar::tab {
            background-color: @gray;
            border-top-left-radius: 4px;
            border-top-right-radius: 4px;
            min-width: 8ex;
            padding: 4px;
            margin-right: 5px;
        }

        QTabBar::tab:selected, QTabBar::tab:hover {
            background: @lightGray;
        }

        QTabBar::tab:selected {
            border-color: @borderGray; 
        }

        #sectionHeader{
            font-size: 20px;
        }

        QScrollBar {
            background : @gray;
        }

        QScrollBar::handle {
            background : @gray;
            border: 1px solid @borderGray;
        }
        
        QScrollBar::handle::pressed {
            background : @lightGray;
        }

        #sectionFrame {
            border-radius: 4px;
            padding: 2px;
        }

        """

        self.genStyles()

    def genStyles(self):
        for key, val in self.colors.items():
            self.styleSheet = self.styleSheet.replace(f"@{key}", val)

    def getStyles(self):
        return self.styleSheet

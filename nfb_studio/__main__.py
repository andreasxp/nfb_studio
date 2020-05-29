import sys

from PySide2.QtWidgets import QApplication

from .main_window import MainWindow

def main():
    app = QApplication(sys.argv)

    main_window = MainWindow()
    main_window.show()

    return app.exec_()

if __name__ == "__main__":
    sys.exit(main())

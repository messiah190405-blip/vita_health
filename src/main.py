import sys
from PyQt6.QtWidgets import QApplication, QMessageBox
from src.database.db_manager import SupabaseHealthRepository
from src.ui.main_window import VitaHealthMainWindow


def main() -> None:
    app = QApplication(sys.argv)
    try:
        repo = SupabaseHealthRepository()
    except Exception as exc:
        QMessageBox.critical(None, "Configuration Error", str(exc))
        sys.exit(1)

    window = VitaHealthMainWindow(repo)
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
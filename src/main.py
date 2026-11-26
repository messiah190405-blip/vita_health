import sys
from PyQt6.QtWidgets import QApplication, QDialog
from src.database.db_manager import SupabaseHealthRepository
from src.ui.login_dialog import ClinicianLoginDialog
from src.ui.main_window import VitaHealthMainWindow


def main() -> int:
    app = QApplication(sys.argv)
    repo = SupabaseHealthRepository()

    login = ClinicianLoginDialog(repo)
    if login.exec() != QDialog.DialogCode.Accepted or not login.authenticated_clinician:
        return 0

    window = VitaHealthMainWindow(
        repo,
        current_clinician=login.authenticated_clinician,
    )
    window.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
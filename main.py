from app.database.db import initialize_database
from app.ui.main_window import SafeSendApp
from app.utils.logger import configure_logging


def main() -> None:
    configure_logging()
    initialize_database()
    app = SafeSendApp()
    app.run()


if __name__ == "__main__":
    main()

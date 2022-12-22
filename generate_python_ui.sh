poetry run python -m PyQt6.uic.pyuic -o ./gui_server/main_window.py -x ./gui_server/server_gui.ui
poetry run python -m PyQt6.uic.pyuic -o ./gui_server/history_window.py -x ./gui_server/server_gui_history.ui
poetry run python -m PyQt6.uic.pyuic -o ./gui_server/clients_window.py -x ./gui_server/server_gui_clients.ui

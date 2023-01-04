poetry run python -m PyQt6.uic.pyuic -o ./server/gui/main_window.py -x ./server/gui/server_gui.ui
poetry run python -m PyQt6.uic.pyuic -o ./server/gui/history_window.py -x ./server/gui/server_gui_history.ui
poetry run python -m PyQt6.uic.pyuic -o ./server/gui/clients_window.py -x ./server/gui/server_gui_clients.ui
poetry run python -m PyQt6.uic.pyuic -o ./client/gui/main_window.py -x ./client/gui/client_gui.ui

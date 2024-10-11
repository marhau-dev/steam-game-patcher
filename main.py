import os
import sys
import requests
import zipfile
import shutil  # Importing shutil for directory operations
from PyQt5 import QtWidgets, QtGui, QtCore

class GameSelector(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("steam-game-patcher")
        self.setGeometry(100, 100, 800, 600)

        # Layouts
        self.layout = QtWidgets.QVBoxLayout()
        self.setLayout(self.layout)

        # Widgets
        self.folder_button = QtWidgets.QPushButton("Select Folder")
        self.folder_button.clicked.connect(self.select_folder)
        self.layout.addWidget(self.folder_button)

        self.exe_list_widget = QtWidgets.QListWidget()
        self.layout.addWidget(self.exe_list_widget)

        self.select_exe_button = QtWidgets.QPushButton("Select Game Executable")
        self.select_exe_button.clicked.connect(self.select_exe)
        self.layout.addWidget(self.select_exe_button)

        self.game_list_widget = QtWidgets.QListWidget()
        self.layout.addWidget(self.game_list_widget)

        self.select_game_button = QtWidgets.QPushButton("Select Game")
        self.select_game_button.clicked.connect(self.select_game)
        self.layout.addWidget(self.select_game_button)

        # Label to display messages
        self.message_label = QtWidgets.QLabel("")
        self.layout.addWidget(self.message_label)

        self.setStyleSheet("""
            QWidget {
                background-color: #f0f0f0;
            }
            QPushButton {
                font-size: 15px;
                font-family: Arial;
                width: 140px;
                height: 50px;
                border-width: 1px;
                color: rgba(126, 125, 125, 1);
                border-color: rgba(194, 195, 197, 1);
                border-radius: 17px;  /* Applies to all corners */
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1, 
                                            stop: 0 rgba(173, 173, 175, 1), 
                                            stop: 1 rgba(255, 255, 255, 1));
            }

            QPushButton:hover {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1, 
                                            stop: 0 rgba(255, 255, 255, 1), 
                                            stop: 1 rgba(173, 173, 175, 1));
            }
            QListWidget {
                background-color: white;
                border: 1px solid #ccc;
                border-radius: 5px;
            }
        """)

        self.selected_folder = None  # Store the selected folder

    def select_folder(self):
        folder_path = QtWidgets.QFileDialog.getExistingDirectory(self, "Select Folder")
        if folder_path:
            self.selected_folder = folder_path
            self.find_exe(folder_path)

    def find_exe(self, folder_path):
        exe_files = [file for file in os.listdir(folder_path) if file.endswith(".exe")]
        self.exe_list_widget.clear()  # Clear previous entries
        self.game_list_widget.clear()  # Clear previous game list

        for exe in exe_files:
            item = QtWidgets.QListWidgetItem(exe)
            item.setData(QtCore.Qt.UserRole, exe)  # Store exe name in the item
            self.exe_list_widget.addItem(item)

    def select_exe(self):
        selected_item = self.exe_list_widget.currentItem()
        if selected_item:
            selected_exe = selected_item.data(QtCore.Qt.UserRole)
            matching_games = self.search_id(selected_exe)
            self.populate_game_list(matching_games)

    def search_id(self, game_exe):
        game_exe = game_exe.replace(".exe", "")
        apps = self.get_app_list()
        
        matching_games = [app for app in apps if game_exe.lower() in app['name'].lower()]
        return matching_games

    def populate_game_list(self, matching_games):
        self.game_list_widget.clear()  # Clear previous game list

        if matching_games:
            for game in matching_games:
                app_id = game['appid']
                game_name = game['name']
                # Constructing icon URL
                icon_url = f"http://media.steampowered.com/steamcommunity/public/images/apps/{app_id}/07385eb55b5ba974aebbe74d3c99626bda7920b8.jpg"  # Placeholder hash

                item = QtWidgets.QListWidgetItem(f"{game_name} (App ID: {app_id})")
                # Load icon asynchronously
                self.load_icon(icon_url, item)
                self.game_list_widget.addItem(item)

    def load_icon(self, url, item):
        # Download the image
        def set_icon():
            try:
                image_data = requests.get(url).content
                pixmap = QtGui.QPixmap()
                pixmap.loadFromData(image_data)
                item.setIcon(QtGui.QIcon(pixmap))
            except Exception as e:
                print(f"Error loading icon: {e}")

        # Start a new thread to load the icon
        QtCore.QTimer.singleShot(0, set_icon)

    def get_app_list(self):
        api_url = "https://api.steampowered.com/ISteamApps/GetAppList/v0002/"
        response = requests.get(api_url)
        
        if response.status_code == 200:
            data = response.json()
            return data['applist']['apps']
        else:
            print(f"Failed to retrieve data: {response.status_code}")
            return []

    def select_game(self):
        selected_item = self.game_list_widget.currentItem()
        if selected_item:
            game_info = selected_item.text()
            app_id = game_info.split("(")[-1].split(":")[1].strip()  # Extract App ID without trailing parenthesis
            selected_exe = self.exe_list_widget.currentItem().data(QtCore.Qt.UserRole)  # Get the selected EXE name
            print(f"You selected the game with info: {game_info}")

            # Download files from GitHub and save the config
            self.message_label.setText("Please wait, resources downloading...")
            self.download_files(selected_exe, app_id)

    def download_files(self, selected_exe, app_id):
        # Define the GitHub repository and download URL
        repo_url = "https://github.com/marhau-dev/steam-game-patcher/archive/refs/heads/main.zip"
        target_folder = self.selected_folder  # Save directly to the selected game folder

        # Download the ZIP file
        zip_path = os.path.join(target_folder, "steam-game-patcher.zip")
        print(f"Downloading from {repo_url}...")

        try:
            response = requests.get(repo_url)
            with open(zip_path, 'wb') as f:
                f.write(response.content)
            print("Download complete.")

            # Extract the ZIP file directly into the selected folder
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(target_folder)  # Extract files into the game folder
            print("Files extracted.")

            # Remove the ZIP file after extraction
            os.remove(zip_path)

            # Get the extracted folder name
            extracted_folder = os.path.join(target_folder, "steam-game-patcher-main")

            # Copy files from the extracted folder to the game folder
            self.copy_files(extracted_folder, target_folder)

            # Create the config file
            self.create_config_file(selected_exe, app_id, target_folder)

            # Reset the message after completion
            self.message_label.setText("Resources downloaded successfully.")
        except Exception as e:
            self.message_label.setText("Error downloading resources.")
            print(f"Error downloading or extracting files: {e}")

    def copy_files(self, source_folder, target_folder):
        # Copy all files from the source folder to the target folder
        for item in os.listdir(source_folder):
            source_path = os.path.join(source_folder, item)
            target_path = os.path.join(target_folder, item)

            if os.path.isdir(source_path):
                shutil.copytree(source_path, target_path, dirs_exist_ok=True)
            else:
                shutil.copy2(source_path, target_path)

        # Delete the extracted folder after copying
        shutil.rmtree(source_folder)
        print(f"Copied files from {source_folder} to {target_folder} and deleted the source folder.")

    def create_config_file(self, selected_exe, app_id, folder):
        app_id = app_id.rstrip(")")  # Remove any trailing parentheses from App ID
        config_content = f"""
[SteamClient]
Exe = {selected_exe}
ExeRunDir = .
ExeCommandLine = 
AppId = {app_id}
SteamClientDll = steamclient.dll
SteamClient64Dll = steamclient64.dll
"""
        config_file_path = os.path.join(folder, "ColdClientLoader.ini")
        with open(config_file_path, 'w') as config_file:
            config_file.write(config_content)
        print(f"Config file created: {config_file_path}")

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    window = GameSelector()
    window.show()
    sys.exit(app.exec_())

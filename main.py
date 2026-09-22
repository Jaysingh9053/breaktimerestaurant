import sys
from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QIcon
from database import get_database
from dashboard import DashboardWindow
from login import LoginWindow
from paths import resource_path

get_database()

app = QApplication(sys.argv)
app.setWindowIcon(QIcon(str(resource_path("app_icon.png"))))

loginwindow = LoginWindow()
remembered_user = loginwindow.get_remembered_user()
if remembered_user:
	loginwindow.hide()
	loginwindow.dashboard = DashboardWindow(loginwindow, remembered_user)
	loginwindow.dashboard.showMaximized()
else:
	loginwindow.show()

app.exec()

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QLineEdit, QPushButton, QLabel, QFrame, QCheckBox,
    QGraphicsDropShadowEffect, QStackedWidget, QDateEdit
)
from database import get_database
from dashboard import DashboardWindow
from PyQt6.QtGui import QPixmap, QPalette, QBrush, QIcon
from PyQt6.QtCore import QDate, QPropertyAnimation, QSettings, QRect, Qt
from paths import resource_path


class LoginWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.database = get_database()
        self.reset_user = None
        self.generated_otp = None
        self.login_settings = QSettings("BreaktimeRestaurant", "BreaktimeRestaurant")

        self.setWindowTitle("Breaktime Restaurant")
        self.setWindowIcon(QIcon(str(resource_path("app_icon.png"))))
        self.resize(1200, 700)

        main_layout = QVBoxLayout()

        self.setStyleSheet(self.styleSheet() + """
        QToolTip {
            background-color: rgba(54, 28, 20, 235);
            color: #fff4ea;
            border: 1px solid rgba(255, 255, 255, 0.16);
            border-radius: 12px;
            padding: 10px 12px;
            font-size: 12px;
        }
        """)

        nav = QHBoxLayout()
        nav.setContentsMargins(20, 14, 20, 6)

        left = QLabel("Contact Us")
        left.setStyleSheet("color: white; font-size: 14px; font-weight: 600;")
        left.setToolTip("Reservations & Contact\nPhone: +91 98765 43210\nEmail: breaktime@support.com")

        right = QLabel("Need Help?")
        right.setStyleSheet("color: white; font-size: 14px; font-weight: 600;")
        right.setToolTip("Need Help Logging In?\nUse Forgot Password to reset access.\nFor account issues, contact the manager desk.")

        nav.addWidget(left)
        nav.addStretch()
        nav.addWidget(right)

        main_layout.addLayout(nav)

        #  LOGO (FIXED SIZE + POSITION)
        logo = QLabel()
        logo_pix = QPixmap(str(resource_path("logo.png"))).scaled(
            420, 220,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )
        logo.setPixmap(logo_pix)
        logo.setAlignment(Qt.AlignmentFlag.AlignCenter)

        main_layout.addSpacing(10)
        main_layout.addWidget(logo)



        card = QFrame()
        card.setMaximumWidth(700)


        card.setStyleSheet("""
        QFrame {
            background-color: #f4e3cf;
            border-radius: 30px;
        }
        
        """)

        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(25)
        shadow.setYOffset(5)

        card.setGraphicsEffect(shadow)

        card_layout = QVBoxLayout()
        card_layout.setSpacing(15)
        card_layout.setContentsMargins(35, 30, 35, 30)


        title = QLabel("Welcome Back")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("""
        font-size: 30px;
        font-weight: bold;
        color: #5a3b1c;
        """)

        subtitle = QLabel("Please login to your account")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle.setStyleSheet("color: #8b5e3c; font-size: 13px;")

        #  INPUTS
        self.user = QLineEdit()
        self.user.setPlaceholderText("User ID")
        self.user.addAction(QIcon(str(resource_path("user.png"))), QLineEdit.ActionPosition.LeadingPosition)
        self.user.setMinimumHeight(45)

        self.password = QLineEdit()
        self.password.setPlaceholderText("Password")
        self.password.setEchoMode(QLineEdit.EchoMode.Password)
        self.password.addAction(QIcon(str(resource_path("lock.png"))), QLineEdit.ActionPosition.LeadingPosition)
        self.password.setMinimumHeight(45)

        input_style = """
        QLineEdit {
            padding: 12px;
            border-radius: 12px;
            background-color: #efe1cf;
            border: 1px solid #d2b48c;
            color: #5a3b1c;
        }
        QLineEdit::placeholder {
            color: #a67c52;
        }
        """

        self.user.setStyleSheet(input_style)
        self.password.setStyleSheet(input_style)
        self.user.returnPressed.connect(self.login)
        self.password.returnPressed.connect(self.login)
        self.user.textChanged.connect(lambda: self.login_message.hide())
        self.password.textChanged.connect(lambda: self.login_message.hide())

        #  OPTIONS
        options = QHBoxLayout()
        remember = QCheckBox("Remember Me")
        self.remember_checkbox = remember
        remember.setToolTip("Remember your user ID on this device. Your password is never saved.")
        remember.setStyleSheet("""
        QCheckBox {
            color: #5a3b1c;
            spacing: 8px;
        }

        QCheckBox::indicator {
            width: 14px;
            height: 14px;
            border-radius: 3px;
            border: 2px solid #d2b48c;
            background-color: #efe1cf;
        }

        QCheckBox::indicator:unchecked {
            background-color: #efe1cf;
        }

        QCheckBox::indicator:checked {
            background-color: #e6954a;
            border: 2px solid #e6954a;
            image: url("%s");
        }
        """ % resource_path("check.png").as_posix())

        forgot = ClickableLabel("Forgot Password?")
        forgot.setStyleSheet("color:#5a3b1c;")
        forgot.mousePressEvent = self.show_forgot

        options.addWidget(remember)
        options.addStretch()
        options.addWidget(forgot)

        self.login_message = QLabel("")
        self.login_message.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.login_message.setStyleSheet("color: #9b2c2c; font-size: 13px; font-weight: bold;")
        self.login_message.hide()

        #  BUTTON
        btn = QPushButton("Login")
        btn.setStyleSheet("""
        QPushButton {
            background-color: #e6954a;
            color: white;
            padding: 12px;
           border-radius: 12px;
            font-weight: bold;
        }
        QPushButton:hover {
            background-color: #cf7f36;
        }
        """)


        self.stack = QStackedWidget()
        card_layout.addWidget(self.stack)


        #  CENTER FIX (NO EXTRA GAP)
        main_layout.addSpacing(10)
        main_layout.addWidget(card, alignment=Qt.AlignmentFlag.AlignCenter)
        main_layout.addStretch()

        self.setLayout(main_layout)

        saved_user = self.login_settings.value("login/username", "", type=str).strip()
        if saved_user:
            self.user.setText(saved_user)
            remember.setChecked(True)

        btn.clicked.connect(self.login)


        card.setLayout(card_layout)
        login_page = QWidget()
        login_layout = QVBoxLayout()

        login_layout.addWidget(title)
        login_layout.addWidget(subtitle)
        login_layout.addSpacing(10)

        login_layout.addWidget(self.user)
        login_layout.addWidget(self.password)
        login_layout.addLayout(options)
        login_layout.addWidget(self.login_message)

        login_layout.addSpacing(10)
        login_layout.addWidget(btn)

        login_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        login_page.setLayout(login_layout)
        self.stack.addWidget(login_page)

        forgot_page = QWidget()
        forgot_layout = QVBoxLayout()

        forgot_layout.setSpacing(15)
        forgot_layout.setContentsMargins(25, 20, 25, 20)

        # TITLE
        f_title = QLabel("Forgot Password")
        f_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        f_title.setStyleSheet("""
        font-size: 30px;
        font-weight: bold;
        color: #5a3b1c;
        """)



        # SUBTITLE
        f_sub = QLabel("Enter your details to reset password")
        f_sub.setAlignment(Qt.AlignmentFlag.AlignCenter)
        f_sub.setStyleSheet("color: #8b5e3c; font-size: 13px;")

        # INPUTS
        self.mobile = QLineEdit()
        self.mobile.setPlaceholderText("Enter Mobile Number")
        self.mobile.addAction(QIcon(str(resource_path("phone.png"))), QLineEdit.ActionPosition.LeadingPosition)
        self.mobile.setMinimumHeight(45)
        self.mobile.setStyleSheet("""
        QLineEdit {
            padding: 12px 12px 12px 35px;  /* left padding badhaya */
            border-radius: 12px;
            background-color: #efe1cf;
            border: 1px solid #d2b48c;
            color: #5a3b1c;
        }
        """)

        self.dob = QDateEdit()
        self.dob.setCalendarPopup(True)
        self.dob.setDate(QDate.currentDate())
        self.dob.setDisplayFormat("dd/MM/yyyy")
        self.dob.setFixedHeight(45)
        self.dob.setStyleSheet("""
        QDateEdit {
            padding: 10px 36px 10px 12px;
            border-radius: 12px;
            background-color: #efe1cf;
            border: 1px solid #d2b48c;
            color: #5a3b1c;
            selection-background-color: #e6954a;
            selection-color: white;
        }

        QDateEdit:focus {
            border: 1px solid #e6954a;
            background-color: #f7ebdd;
        }

        QDateEdit::drop-down {
            subcontrol-origin: padding;
            subcontrol-position: center right;
            width: 30px;
            border: none;
            image: url("%s");
            background-position: center;
            background-repeat: no-repeat;
        }
        QDateEdit::down-arrow {
            image: none;
            width: 0px;
            height: 0px;
        }
        QCalendarWidget {
            background-color: #f4e3cf;
            border-radius: 10px;
        }
        QCalendarWidget QWidget#qt_calendar_navigationbar {
            background-color: #e6954a;
        }
        QCalendarWidget QToolButton {
            color: white;
            font-weight: bold;
            background: transparent;
        }
        QCalendarWidget QToolButton:hover {
            background-color: #cf7f36;
            border-radius: 5px;
        }
        QCalendarWidget QTableView {
            background-color: #f4e3cf;
            selection-background-color: #e6954a;
            selection-color: white;
            gridline-color: #d2b48c;
        }
        QCalendarWidget QTableView::item {
            color: #5a3b1c;
        }
        QCalendarWidget QTableView::item:selected {
            background-color: #e6954a;
            color: white;
            border-radius: 5px;
        }
        QCalendarWidget QToolButton {
            color: white;
            font-weight: bold;
            background-color: transparent;
            border: none;
            padding: 6px;
        }

        QCalendarWidget QToolButton:hover {
            background-color: #cf7f36;
            border-radius: 5px;
        }

        """ % resource_path("calendar.png").as_posix())

        self.mobile.setStyleSheet(input_style)


        # BUTTON
        self.send_btn = QPushButton("Send OTP")
        self.otp_input = QLineEdit()
        self.otp_input.setPlaceholderText("Enter OTP")
        self.otp_input.setStyleSheet(input_style)

        self.otp_input.hide()

        self.verify_btn = QPushButton("Verify")
        self.verify_btn.clicked.connect(self.verify_otp)
        self.verify_btn.hide()

        self.send_btn.clicked.connect(self.show_otp)
        self.send_btn.setStyleSheet("""
        QPushButton {
            background-color: #e6954a;
            color: white;
            padding: 12px;
            border-radius: 12px;
            font-weight: bold;
        }
        QPushButton:hover {
            background-color: #cf7f36;
        }
        """)

        self.verify_btn.setStyleSheet(self.send_btn.styleSheet())

        self.new_pass = QLineEdit()
        self.new_pass.setPlaceholderText("New Password")
        self.new_pass.setEchoMode(QLineEdit.EchoMode.Password)
        self.new_pass.setStyleSheet(input_style)
        self.new_pass.setMinimumHeight(45)
        self.new_pass.hide()

        self.confirm_pass = QLineEdit()
        self.confirm_pass.setPlaceholderText("Confirm Password")
        self.confirm_pass.setEchoMode(QLineEdit.EchoMode.Password)
        self.confirm_pass.setStyleSheet(input_style)
        self.confirm_pass.setMinimumHeight(45)
        self.confirm_pass.hide()

        self.submit_btn = QPushButton("Confirm")
        self.submit_btn.setStyleSheet(self.send_btn.styleSheet())
        self.submit_btn.hide()
        self.submit_btn.clicked.connect(self.reset_password)

        self.message_label = QLabel("")
        self.message_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.message_label.setStyleSheet("color: #5a3b1c; font-size: 14px; font-weight: bold;")
        self.message_label.hide()
        self.mobile.textChanged.connect(lambda: self.message_label.hide())
        self.otp_input.textChanged.connect(lambda: self.message_label.hide())
        self.new_pass.textChanged.connect(lambda: self.message_label.hide())
        self.confirm_pass.textChanged.connect(lambda: self.message_label.hide())

        # BACK BUTTON
        back_btn = QLabel("← Back to Login")
        back_btn.setAlignment(Qt.AlignmentFlag.AlignCenter)
        back_btn.setStyleSheet("""
        color:#5a3b1c;
        """)
        back_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        back_btn.mousePressEvent = self.back_to_login


        forgot_layout.addWidget(f_title)
        forgot_layout.addWidget(f_sub)
        forgot_layout.addSpacing(10)

        forgot_layout.addWidget(self.mobile)
        forgot_layout.addWidget(self.dob)

        forgot_layout.addSpacing(10)
        forgot_layout.addWidget(self.send_btn)

        forgot_layout.addWidget(self.otp_input)
        forgot_layout.addWidget(self.verify_btn)

        forgot_layout.addWidget(self.new_pass)
        forgot_layout.addWidget(self.confirm_pass)
        forgot_layout.addWidget(self.submit_btn)
        forgot_layout.addWidget(self.message_label)

        forgot_layout.addSpacing(5)
        forgot_layout.addWidget(back_btn)

        forgot_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        forgot_page.setLayout(forgot_layout)
        



        self.stack.addWidget(forgot_page)

    def show_otp(self):
        mobile = self.mobile.text().strip()
        dob = self.dob.date().toString("yyyy-MM-dd")

        if not mobile:
            self.message_label.setText("Enter your mobile number")
            self.message_label.show()
            return

        user = self.database.find_user_for_password_reset(mobile, dob)
        if not user:
            self.message_label.setText("No account matches this mobile number and date of birth")
            self.message_label.show()
            return

        self.reset_user = user
        self.generated_otp = "1234"
        self.message_label.setText(f"OTP sent successfully. Demo OTP: {self.generated_otp}")
        self.message_label.show()

        self.otp_input.show()
        self.verify_btn.show()
        self.dob.hide()
        self.send_btn.hide()
    def show_forgot(self, event):
        self.stack.setCurrentIndex(1)



    #  BACKGROUND
    def resizeEvent(self, event):
        pixmap = QPixmap(str(resource_path("background.jpg"))).scaled(
            self.size(),
            Qt.AspectRatioMode.KeepAspectRatioByExpanding,
            Qt.TransformationMode.SmoothTransformation
        )

        palette = QPalette()
        palette.setBrush(QPalette.ColorRole.Window, QBrush(pixmap))
        self.setPalette(palette)

        super().resizeEvent(event)

    def login(self):
        user = self.user.text().strip()
        password = self.password.text()
        self.login_message.hide()

        authenticated_user = self.database.authenticate_user(user, password)
        if authenticated_user:
            if self.remember_checkbox.isChecked():
                self.login_settings.setValue("login/username", user)
                self.login_settings.setValue("session/user_id", int(authenticated_user["id"]))
            else:
                self.login_settings.remove("login/username")
                self.login_settings.remove("session/user_id")
            self.user.clear()
            self.password.clear()
            self.hide()
            self.dashboard = DashboardWindow(self, authenticated_user)
            self.dashboard.showMaximized()
        else:
            self.login_message.setText("Invalid user ID or password")
            self.login_message.show()

    def reset_login_form(self):
        self.login_settings.remove("login/username")
        self.login_settings.remove("session/user_id")
        self.user.clear()
        self.password.clear()
        self.remember_checkbox.setChecked(False)
        self.login_message.hide()
        self.user.setFocus()

    def get_remembered_user(self):
        saved_id = self.login_settings.value("session/user_id", "", type=str).strip()
        if not saved_id:
            return None
        try:
            user_id = int(saved_id)
        except ValueError:
            self.login_settings.remove("session/user_id")
            return None

        remembered_user = next(
            (user for user in self.database.get_all_users() if int(user["id"]) == user_id),
            None,
        )
        if remembered_user is None:
            self.login_settings.remove("session/user_id")
            self.login_settings.remove("login/username")
        return remembered_user

    def reset_password(self):
        p1 = self.new_pass.text()
        p2 = self.confirm_pass.text()

        if p1 == "" or p2 == "":
            self.message_label.setText("Fill all fields")
            self.message_label.show()

        elif p1 != p2:
            self.message_label.setText("Password mismatch")
            self.message_label.show()

        elif not self.reset_user:
            self.message_label.setText("Restart the password reset flow")
            self.message_label.show()

        else:
            self.database.update_password(self.reset_user["id"], p1)
            self.message_label.setText("Password changed successfully!")
            self.message_label.show()
            self.new_pass.hide()
            self.confirm_pass.hide()
            self.submit_btn.hide()

            # Auto-return to login after 2 seconds
            from PyQt6.QtCore import QTimer
            QTimer.singleShot(2000, self.back_to_login)

    def verify_otp(self):
        otp = self.otp_input.text()

        if otp == self.generated_otp:
            print("OTP Verified")
            self.message_label.hide()

            self.otp_input.hide()
            self.verify_btn.hide()
            self.new_pass.show()
            self.confirm_pass.show()
            self.submit_btn.show()

        else:
            self.message_label.setText("Invalid OTP")
            self.message_label.show()

    def back_to_login(self, event=None):
        # Reset forgot page
        self.mobile.setEnabled(True)
        self.dob.setEnabled(True)
        self.mobile.clear()
        self.dob.setDate(QDate.currentDate())
        self.otp_input.hide()
        self.otp_input.clear()
        self.verify_btn.hide()
        self.new_pass.hide()
        self.new_pass.clear()
        self.confirm_pass.hide()
        self.confirm_pass.clear()
        self.submit_btn.hide()
        self.message_label.hide()
        self.message_label.clear()
        self.dob.show()
        self.send_btn.show()
        self.stack.setCurrentIndex(0)
        self.reset_user = None
        self.generated_otp = None

class ClickableLabel(QLabel):
    def __init__(self, text, parent=None):
        super().__init__(text, parent)

        self.setCursor(Qt.CursorShape.PointingHandCursor)

        self.anim = QPropertyAnimation(self, b"geometry")
        self.anim.setDuration(150)

    def enterEvent(self, event):
        self.setStyleSheet("color:#e6954a; text-decoration: underline;")

        rect = self.geometry()
        self.anim.stop()
        self.anim.setStartValue(rect)
        self.anim.setEndValue(QRect(rect.x(), rect.y() - 2, rect.width(), rect.height() + 4))
        self.anim.start()

    def leaveEvent(self, event):
        self.setStyleSheet("color:#5a3b1c;")

        rect = self.geometry()
        self.anim.stop()
        self.anim.setStartValue(rect)
        self.anim.setEndValue(QRect(rect.x(), rect.y() + 2, rect.width(), rect.height() - 4))

        self.anim.start()

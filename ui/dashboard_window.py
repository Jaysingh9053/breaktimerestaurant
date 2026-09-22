from html import escape
from datetime import datetime
from PyQt6.QtWidgets import QListView

from PyQt6.QtCore import Qt, QTimer, QDate
from PyQt6.QtGui import QColor, QGuiApplication, QIcon, QLinearGradient, QPainter, QPixmap
from PyQt6.QtPrintSupport import QPrintDialog, QPrinter
from PyQt6.QtWidgets import (
    QAbstractItemView,
    QComboBox,
    QCheckBox,
    QDialog,
    QDialogButtonBox,
    QDateEdit,
    QDoubleSpinBox,
    QFormLayout,
    QFrame,
    QGraphicsDropShadowEffect,
    QGridLayout,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QSpinBox,
    QStackedWidget,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from database import GST_RATE, get_database
from paths import resource_path


NAVIGATION_ITEMS = ["Dashboard", "Orders", "Menu Items", "Billing", "Customers", "Users", "Reports", "Settings", "Logout"]

ROLE_PAGE_ACCESS = {
    "receptionist": {"Orders", "Billing", "Menu Items", "Customers", "Logout"},
}

ROLE_ACTION_ACCESS = {
    "receptionist": {
        "create_order",
        "apply_offer",
        "record_payment",
        "add_customer",
        "view_stock",
    },
}

TABLE_SEQUENCE = [f"T-{number:02d}" for number in range(1, 21)]
ORDER_SOURCE_OPTIONS = [(f"Table {table_name}", table_name, "Dine In") for table_name in TABLE_SEQUENCE] + [
    ("Takeaway", "Takeaway", "Takeaway"),
    ("Delivery", "Delivery", "Delivery"),
]


def add_shadow(widget, blur=24, x_offset=0, y_offset=6, color=QColor(60, 30, 10, 90)):
    shadow = QGraphicsDropShadowEffect(widget)
    shadow.setBlurRadius(blur)
    shadow.setOffset(x_offset, y_offset)
    shadow.setColor(color)
    widget.setGraphicsEffect(shadow)


def format_currency(amount):
    return f"Rs.{float(amount):,.2f}"


def format_percent(value):
    numeric = float(value)
    return f"{int(numeric)}%" if numeric.is_integer() else f"{numeric:.2f}%"


def status_color(status):
    colors = {
        "Completed": "#4f8c2f",
        "Pending": "#b8611a",
        "Preparing": "#d9881f",
        "Ready": "#2b58a9",
        "Served": "#7aaa1e",
        "Cancelled": "#c7462d",
    }
    return colors.get(status, "#6b473b")


def payment_color(status):
    return "#2b58a9" if status == "Paid" else "#b8611a"


def format_datetime(value):
    return datetime.fromisoformat(value).strftime("%d %b %Y, %I:%M %p")


def button_stylesheet(kind="primary"):
    palettes = {
        "primary": ("#2b58a9", "#23498d", "#ffffff", "none"),
        "secondary": ("#5a3a2f", "#714c3b", "#ffffff", "none"),
        "danger": ("#b42318", "#d92d20", "#ffffff", "none"),
        "soft": ("#f4e4d2", "#ebd5bf", "#6a4630", "1px solid #d6b089"),
    }
    background, hover, text_color, border = palettes.get(kind, palettes["primary"])
    return f"""
        QPushButton {{
            background-color: {background};
            color: {text_color};
            border: {border};
            border-radius: 10px;
            padding: 10px 16px;
            font-size: 13px;
            font-weight: 700;
        }}
        QPushButton:hover {{
            background-color: {hover};
        }}
    """


def style_button(button, kind="primary", min_width=132, min_height=42):
    button.setCursor(Qt.CursorShape.PointingHandCursor)
    button.setMinimumWidth(min_width)
    button.setMinimumHeight(min_height)
    button.setStyleSheet(button_stylesheet(kind))


def configure_combo_box(combo_box, min_chars=20, popup_width=360):
    combo_box.setSizeAdjustPolicy(QComboBox.SizeAdjustPolicy.AdjustToMinimumContentsLengthWithIcon)
    combo_box.setMinimumContentsLength(min_chars)
    # Use QListView for better rendering and set minimum height for popup
    list_view = QListView()
    list_view.setMinimumHeight(120)
    list_view.setStyleSheet(
        """
        QListView {
            background: #fff;
            color: #222;
            border: 1px solid #bfbfbf;
            selection-background-color: #0078d7;
            selection-color: #fff;
        }
        """
    )
    combo_box.setView(list_view)
    combo_box.view().setMinimumWidth(popup_width)
    combo_box.currentTextChanged.connect(combo_box.setToolTip)
    combo_box.setToolTip(combo_box.currentText())

    # Add hover effect for better UI
    combo_box.setStyleSheet(
        """
        QComboBox {
            border: 1px solid #bfbfbf;
            border-radius: 4px;
            padding: 5px;
            background-color: #f9f9f9;
        }
        QComboBox:hover {
            border: 1px solid #0078d7;
            background-color: #e6f7ff;
        }
        QComboBox::drop-down {
            border-left: 1px solid #bfbfbf;
        }
        """
    )


def configure_date_edit(date_edit):
    date_edit.setCalendarPopup(True)
    date_edit.setDisplayFormat("dd/MM/yyyy")
    date_edit.setMinimumHeight(46)
    date_edit.setStyleSheet(
        """
        QDateEdit {
            background-color: #fffdf9;
            border: 1px solid #d6b089;
            border-radius: 10px;
            padding: 9px 36px 9px 12px;
            color: #4d392d;
            selection-background-color: #2b58a9;
            selection-color: #ffffff;
        }
        QDateEdit:focus {
            border: 1px solid #2b58a9;
            background-color: #ffffff;
        }
        QDateEdit::drop-down {
            subcontrol-origin: padding;
            subcontrol-position: center right;
            width: 28px;
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
        """ % resource_path("calendar.png").as_posix()
    )
    calendar = date_edit.calendarWidget()
    if calendar:
        calendar.setStyleSheet(
            """
            QWidget {
                background-color: #fff8f0;
                color: #5a3b1c;
            }
            QToolButton {
                color: #5a3b1c;
                font-weight: 700;
                background: transparent;
                border: none;
                padding: 6px;
            }
            QToolButton:hover {
                background-color: #efe1cf;
                border-radius: 8px;
            }
            QTableView {
                selection-background-color: #2b58a9;
                selection-color: #ffffff;
                alternate-background-color: #f7ede1;
                background-color: #fffdf9;
                gridline-color: #eadbcf;
            }
            """
        )


def configure_table_widget(table, stretch_last=False):
    header = table.horizontalHeader()
    header.setMinimumSectionSize(120)
    for column in range(table.columnCount()):
        header.setSectionResizeMode(column, QHeaderView.ResizeMode.ResizeToContents)
    if stretch_last and table.columnCount() > 0:
        header.setSectionResizeMode(table.columnCount() - 1, QHeaderView.ResizeMode.Stretch)
    table.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
    table.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
    table.setHorizontalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)
    table.setVerticalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)
    table.setWordWrap(False)
    table.setTextElideMode(Qt.TextElideMode.ElideNone)


class WarmBackgroundWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.background = QPixmap()
        for image_name in ("background.png", "bg.png", "background.jpg"):
            pixmap = QPixmap(str(resource_path(image_name)))
            if not pixmap.isNull():
                self.background = pixmap
                break

    def paintEvent(self, event):
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        if not self.background.isNull():
            scaled = self.background.scaled(
                self.size(),
                Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                Qt.TransformationMode.SmoothTransformation,
            )
            painter.drawPixmap((self.width() - scaled.width()) // 2, (self.height() - scaled.height()) // 2, scaled)

        overlay = QLinearGradient(0, 0, 0, self.height())
        overlay.setColorAt(0.0, QColor(67, 31, 13, 125))
        overlay.setColorAt(0.55, QColor(150, 81, 26, 75))
        overlay.setColorAt(1.0, QColor(248, 211, 146, 55))
        painter.fillRect(self.rect(), overlay)


class StatCard(QFrame):
    def __init__(self, title, value, color):
        super().__init__()
        self.setStyleSheet(f"background-color: {color}; border-radius: 10px;")
        self.setMinimumHeight(104)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        add_shadow(self)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 14, 18, 14)
        title_label = QLabel(title)
        title_label.setStyleSheet("color: white; font-size: 15px;")
        value_label = QLabel(value)
        value_label.setStyleSheet("color: white; font-size: 24px; font-weight: 700;")
        layout.addWidget(title_label)
        layout.addStretch()
        layout.addWidget(value_label)


class BadgeLabel(QLabel):
    def __init__(self, text, color="#2b58a9"):
        super().__init__(text)
        self.setStyleSheet(
            f"background-color: {color}; color: white; border-radius: 12px; padding: 4px 10px; font-size: 12px; font-weight: 700;"
        )


class NavButton(QPushButton):
    def __init__(self, text, active=False, danger=False):
        super().__init__(text)
        self.danger = danger
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setMinimumHeight(54)
        self.set_active(active)

    def set_active(self, active):
        if self.danger:
            self.setStyleSheet(
                """
                QPushButton {
                    color: white;
                    background-color: #b42318;
                    border: 1px solid #d92d20;
                    border-radius: 8px;
                    text-align: left;
                    padding-left: 22px;
                    font-size: 16px;
                    font-weight: 700;
                }
                QPushButton:hover {
                    background-color: #d92d20;
                    border-color: #f04438;
                    padding-left: 26px;
                }
                """
            )
            return

        if active:
            self.setStyleSheet(
                "color: white; background-color: #2b58a9; border: none; border-radius: 8px; text-align: left; padding-left: 22px; font-size: 16px; font-weight: 700;"
            )
        else:
            self.setStyleSheet(
                "color: #efe3dc; background-color: transparent; border: none; text-align: left; padding-left: 22px; font-size: 16px; font-weight: 600;"
            )


class SectionPanel(QFrame):
    def __init__(self, title):
        super().__init__()
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Maximum)
        self.setStyleSheet("background-color: rgba(255, 250, 244, 245); border: 1px solid rgba(160, 112, 62, 0.35); border-radius: 10px;")
        add_shadow(self)
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 18)
        root.setSpacing(0)

        heading = QLabel(title)
        heading.setStyleSheet("font-size: 22px; font-weight: 700; color: #6a5547; padding: 18px 24px 14px 24px;")
        root.addWidget(heading)

        divider = QFrame()
        divider.setFrameShape(QFrame.Shape.HLine)
        divider.setStyleSheet("color: rgba(170, 140, 110, 0.45);")
        root.addWidget(divider)

        self.content = QVBoxLayout()
        self.content.setContentsMargins(20, 18, 20, 0)
        self.content.setSpacing(14)
        root.addLayout(self.content)


class CurrentPageStackedWidget(QStackedWidget):
    def sizeHint(self):
        current = self.currentWidget()
        return current.sizeHint() if current else super().sizeHint()

    def minimumSizeHint(self):
        current = self.currentWidget()
        return current.minimumSizeHint() if current else super().minimumSizeHint()


class ThemedDialog(QDialog):
    def __init__(self, title, subtitle="", width=560, parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setModal(True)
        self.setMinimumSize(700, 600)
        self.resize(700, 600)
        self.setStyleSheet(
            """
            QDialog {
                background-color: #fff8f0;
                border: 1px solid #e0c3a4;
                border-radius: 18px;
            }
            QLabel {
                color: #5a3b1c;
                font-size: 14px;
            }
            QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox, QDateEdit {
                background-color: #fffdf9;
                border: 1px solid #d6b089;
                border-radius: 10px;
                padding: 9px 12px;
                color: #4d392d;
                min-height: 20px;
            }
            QLineEdit:focus, QComboBox:focus, QSpinBox:focus, QDoubleSpinBox:focus, QDateEdit:focus {
                border: 1px solid #2b58a9;
            }
            QComboBox::drop-down, QDateEdit::drop-down {
                border: none;
                width: 26px;
            }
            QDateEdit {
                padding-right: 36px;
            }
            QTableWidget {
                background-color: rgba(255,255,255,0.96);
                alternate-background-color: #f7ede1;
                color: #4d392d;
                border-radius: 10px;
                border: 1px solid rgba(166, 120, 72, 0.28);
                gridline-color: #eadbcf;
            }
            QTableWidget::item {
                padding: 6px;
            }
            QHeaderView::section {
                background-color: #efe1cf;
                color: #5a3b1c;
                font-weight: 700;
                padding: 8px;
                border: none;
            }
            QDialogButtonBox {
                margin-top: 6px;
            }
            QMessageBox {
                background-color: #fff8f0;
            }
            QMessageBox QLabel {
                color: #5a3b1c;
            }
            """
        )

        root = QVBoxLayout(self)
        root.setContentsMargins(24, 24, 24, 24)
        root.setSpacing(18)

        header = QVBoxLayout()
        header.setSpacing(4)
        heading = QLabel(title)
        heading.setStyleSheet("font-size: 24px; font-weight: 700; color: #5a3b1c;")
        header.addWidget(heading)

        if subtitle:
            subheading = QLabel(subtitle)
            subheading.setWordWrap(True)
            subheading.setStyleSheet("font-size: 13px; color: #8a674d;")
            header.addWidget(subheading)

        root.addLayout(header)
        self.body_scroll = QScrollArea()
        self.body_scroll.setWidgetResizable(True)
        self.body_scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.body_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.body_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.body_scroll.setStyleSheet("background: transparent; border: none;")
        body = QWidget()
        self.body_scroll.setWidget(body)
        self.content_layout = QVBoxLayout(body)
        self.content_layout.setSpacing(18)
        self.content_layout.setContentsMargins(0, 0, 0, 0)
        root.addWidget(self.body_scroll, 1)

    def create_button_box(self, primary_text):
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        ok_button = buttons.button(QDialogButtonBox.StandardButton.Ok)
        cancel_button = buttons.button(QDialogButtonBox.StandardButton.Cancel)
        if ok_button:
            ok_button.setText(primary_text)
            style_button(ok_button, "primary", min_width=144)
        if cancel_button:
            cancel_button.setText("Cancel")
            style_button(cancel_button, "soft", min_width=120)
        return buttons

    def create_section_card(self, title, description=""):
        card = QFrame()
        card.setStyleSheet(
            """
            QFrame {
                background-color: rgba(244, 228, 210, 0.72);
                border: 1px solid rgba(214, 176, 137, 0.85);
                border-radius: 16px;
            }
            """
        )
        layout = QVBoxLayout(card)
        layout.setContentsMargins(18, 16, 18, 16)
        layout.setSpacing(10)
        heading = QLabel(title)
        heading.setStyleSheet("font-size: 16px; font-weight: 700; color: #5a3b1c;")
        layout.addWidget(heading)
        if description:
            subheading = QLabel(description)
            subheading.setWordWrap(True)
            subheading.setStyleSheet("font-size: 12px; color: #8a674d;")
            layout.addWidget(subheading)
        return card, layout


class UserDialog(ThemedDialog):
    def __init__(self, user=None, parent=None):
        is_edit = user is not None
        super().__init__(
            "Edit User" if is_edit else "Add User",
            "Update staff account details, access level, and contact information." if is_edit else "Create a new staff account with login credentials and role assignment.",
            width=760,
            parent=parent,
        )

        self.user = user or {}
        self.username_input = QLineEdit(self.user.get("username", ""))
        self.full_name_input = QLineEdit(self.user.get("full_name", ""))
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.setPlaceholderText("Enter a password" if not is_edit else "Leave blank to keep current password")
        self.role_input = QComboBox()
        self.role_input.addItems(["Waiter", "Receptionist", "Manager"])
        configure_combo_box(self.role_input, min_chars=12, popup_width=220)
        role_index = self.role_input.findText(self.user.get("role", ""))
        self.role_input.setCurrentIndex(role_index if role_index >= 0 else 0)
        self.mobile_input = QLineEdit(self.user.get("mobile", ""))
        self.mobile_input.setPlaceholderText("Enter mobile number")
        self.dob_input = QDateEdit()
        configure_date_edit(self.dob_input)
        dob_text = self.user.get("dob", "")
        dob = QDate.fromString(dob_text, "yyyy-MM-dd") if dob_text else QDate.currentDate()
        self.dob_input.setDate(dob if dob.isValid() else QDate.currentDate())

        for widget in (
            self.username_input,
            self.full_name_input,
            self.password_input,
            self.role_input,
            self.mobile_input,
            self.dob_input,
        ):
            widget.setMinimumHeight(46)
        self.username_input.setPlaceholderText("Choose a login username")
        self.full_name_input.setPlaceholderText("Enter staff full name")
        self.mobile_input.setPlaceholderText("Enter mobile number")
        self.dob_input.setToolTip("Select date of birth")

        info_strip = QLabel(
            "Create operational staff accounts here. Administrator accounts are reserved and cannot be created from this form."
        )
        info_strip.setWordWrap(True)
        info_strip.setStyleSheet(
            "background-color: rgba(43, 88, 169, 0.10); color: #274b86; border: 1px solid rgba(43, 88, 169, 0.18);"
            "border-radius: 12px; padding: 12px 14px; font-size: 13px; font-weight: 600;"
        )
        self.content_layout.addWidget(info_strip)

        form = QFormLayout()
        form.setSpacing(14)
        form.setLabelAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        form.setFormAlignment(Qt.AlignmentFlag.AlignTop)
        form.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.AllNonFixedFieldsGrow)
        form.addRow("Username", self.username_input)
        form.addRow("Full Name", self.full_name_input)
        form.addRow("Password", self.password_input)
        form.addRow("Role", self.role_input)
        form.addRow("Mobile", self.mobile_input)
        form.addRow("Date of Birth", self.dob_input)
        self.content_layout.addLayout(form)

        note = QLabel("Password is required for new users. When editing, leave it empty to keep the current password.")
        note.setWordWrap(True)
        note.setStyleSheet("color: #8a674d; font-size: 13px;")
        self.content_layout.addWidget(note)

        buttons = self.create_button_box("Save User" if is_edit else "Create User")
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        self.content_layout.addWidget(buttons)

    def get_data(self):
        return {
            "username": self.username_input.text().strip(),
            "full_name": self.full_name_input.text().strip(),
            "password": self.password_input.text().strip(),
            "role": self.role_input.currentText(),
            "mobile": self.mobile_input.text().strip(),
            "dob": self.dob_input.date().toString("yyyy-MM-dd"),
        }


class MenuItemDialog(ThemedDialog):
    def __init__(self, item=None, parent=None):
        super().__init__("Menu Item", "Add a new menu entry or update stock and pricing details.", width=700, parent=parent)

        intro = QLabel("Enter the menu details below. Price, stock, and reorder level control what appears during order creation.")
        intro.setWordWrap(True)
        intro.setStyleSheet(
            "background-color: rgba(43, 88, 169, 0.10); color: #274b86; border: 1px solid rgba(43, 88, 169, 0.18);"
            "border-radius: 12px; padding: 12px 14px; font-size: 13px; font-weight: 600;"
        )
        self.content_layout.addWidget(intro)

        form = QFormLayout()
        form.setSpacing(14)
        form.setLabelAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        form.setFormAlignment(Qt.AlignmentFlag.AlignTop)
        form.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.AllNonFixedFieldsGrow)
        self.name_input = QLineEdit(item["name"] if item else "")
        self.category_input = QLineEdit(item["category"] if item else "")
        self.name_input.setPlaceholderText("Enter item name")
        self.category_input.setPlaceholderText("Enter category")
        self.price_input = QDoubleSpinBox()
        self.price_input.setMaximum(100000)
        self.price_input.setDecimals(2)
        self.price_input.setValue(float(item["price"]) if item else 0.0)
        self.stock_input = QSpinBox()
        self.stock_input.setMaximum(100000)
        self.stock_input.setValue(int(item["stock_qty"]) if item else 0)
        self.reorder_input = QSpinBox()
        self.reorder_input.setMaximum(100000)
        self.reorder_input.setValue(int(item["reorder_level"]) if item else 5)
        self.stock_tracked_input = QCheckBox("Track stock for this item")
        self.stock_tracked_input.setChecked(bool(int(item["is_stock_tracked"])) if item else True)
        self.stock_tracked_input.setStyleSheet("color: #5a3b1c; font-size: 13px; font-weight: 600;")
        for widget in (self.name_input, self.category_input, self.price_input, self.stock_input, self.reorder_input):
            widget.setMinimumHeight(46)
        self.stock_tracked_input.toggled.connect(self._toggle_stock_fields)

        form.addRow("Name", self.name_input)
        form.addRow("Category", self.category_input)
        form.addRow("Price", self.price_input)
        form.addRow("Stock Tracking", self.stock_tracked_input)
        form.addRow("Stock", self.stock_input)
        form.addRow("Reorder Level", self.reorder_input)
        self.content_layout.addLayout(form)
        self._toggle_stock_fields(self.stock_tracked_input.isChecked())

        buttons = self.create_button_box("Save Item")
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        self.content_layout.addWidget(buttons)

    def get_data(self):
        return {
            "name": self.name_input.text().strip(),
            "category": self.category_input.text().strip(),
            "price": float(self.price_input.value()),
            "stock_qty": int(self.stock_input.value()),
            "reorder_level": int(self.reorder_input.value()),
            "is_stock_tracked": bool(self.stock_tracked_input.isChecked()),
        }

    def _toggle_stock_fields(self, enabled):
        self.stock_input.setEnabled(enabled)
        self.reorder_input.setEnabled(enabled)
        if not enabled:
            self.stock_input.setValue(0)
            self.reorder_input.setValue(0)
            self.stock_input.setToolTip("Prepared dishes do not use direct stock tracking.")
            self.reorder_input.setToolTip("Prepared dishes do not use reorder levels.")
        else:
            self.stock_input.setToolTip("Packaged or pre-made items use stock control.")
            self.reorder_input.setToolTip("Alert threshold for tracked stock items.")


class OfferDialog(ThemedDialog):
    def __init__(self, offer=None, parent=None):
        super().__init__("Offer", "Create or update discount rules for billing.", width=700, parent=parent)

        intro = QLabel("Define the offer name, type, value, and minimum order amount.")
        intro.setWordWrap(True)
        intro.setStyleSheet(
            "background-color: rgba(43, 88, 169, 0.10); color: #274b86; border: 1px solid rgba(43, 88, 169, 0.18);"
            "border-radius: 12px; padding: 12px 14px; font-size: 13px; font-weight: 600;"
        )
        self.content_layout.addWidget(intro)

        form = QFormLayout()
        form.setSpacing(14)
        form.setLabelAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        form.setFormAlignment(Qt.AlignmentFlag.AlignTop)
        form.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.AllNonFixedFieldsGrow)
        self.name_input = QLineEdit(offer["name"] if offer else "")
        self.name_input.setPlaceholderText("Enter offer name")
        self.type_input = QComboBox()
        self.type_input.addItem("Percent", "percent")
        self.type_input.addItem("Flat", "flat")
        configure_combo_box(self.type_input, min_chars=12, popup_width=220)
        if offer:
            index = self.type_input.findData(offer["discount_type"])
            if index >= 0:
                self.type_input.setCurrentIndex(index)
        self.value_input = QDoubleSpinBox()
        self.value_input.setMaximum(100000)
        self.value_input.setDecimals(2)
        self.value_input.setValue(float(offer["discount_value"]) if offer else 0.0)
        self.minimum_input = QDoubleSpinBox()
        self.minimum_input.setMaximum(100000)
        self.minimum_input.setDecimals(2)
        self.minimum_input.setValue(float(offer["min_order_amount"]) if offer else 0.0)
        for widget in (self.name_input, self.type_input, self.value_input, self.minimum_input):
            widget.setMinimumHeight(46)

        form.addRow("Name", self.name_input)
        form.addRow("Type", self.type_input)
        form.addRow("Value", self.value_input)
        form.addRow("Minimum Order", self.minimum_input)
        self.content_layout.addLayout(form)

        buttons = self.create_button_box("Save Offer")
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        self.content_layout.addWidget(buttons)

    def get_data(self):
        return {
            "name": self.name_input.text().strip(),
            "discount_type": self.type_input.currentData(),
            "discount_value": float(self.value_input.value()),
            "min_order_amount": float(self.minimum_input.value()),
        }


class CustomerDialog(ThemedDialog):
    def __init__(self, parent=None):
        super().__init__("Add Customer", "Capture guest details once so billing and repeat visits stay easy to track.", width=700, parent=parent)

        self.name_input = QLineEdit()
        self.mobile_input = QLineEdit()
        self.email_input = QLineEdit()
        self.address_input = QLineEdit()
        self.name_input.setPlaceholderText("Enter customer name")
        self.mobile_input.setPlaceholderText("Enter mobile number")
        self.email_input.setPlaceholderText("Enter email address")
        self.address_input.setPlaceholderText("Enter address")

        for widget in (self.name_input, self.mobile_input, self.email_input, self.address_input):
            widget.setMinimumHeight(46)

        intro = QLabel("Capture guest details in a simple form so billing, delivery, and repeat visits stay organized.")
        intro.setWordWrap(True)
        intro.setStyleSheet(
            "background-color: rgba(43, 88, 169, 0.10); color: #274b86; border: 1px solid rgba(43, 88, 169, 0.18);"
            "border-radius: 12px; padding: 12px 14px; font-size: 13px; font-weight: 600;"
        )
        self.content_layout.addWidget(intro)

        form = QFormLayout()
        form.setSpacing(14)
        form.setLabelAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        form.setFormAlignment(Qt.AlignmentFlag.AlignTop)
        form.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.AllNonFixedFieldsGrow)
        form.addRow("Full Name", self.name_input)
        form.addRow("Mobile", self.mobile_input)
        form.addRow("Email", self.email_input)
        form.addRow("Address", self.address_input)
        self.content_layout.addLayout(form)

        buttons = self.create_button_box("Save Customer")
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        self.content_layout.addWidget(buttons)

    def get_data(self):
        return {
            "full_name": self.name_input.text().strip(),
            "mobile": self.mobile_input.text().strip(),
            "email": self.email_input.text().strip(),
            "address": self.address_input.text().strip(),
        }


class StockUpdateDialog(ThemedDialog):
    def __init__(self, current_value=0, parent=None):
        super().__init__("Update Stock", "Set the latest available quantity for the selected menu item.", width=700, parent=parent)
        intro = QLabel("Update the stock count for the selected menu item.")
        intro.setWordWrap(True)
        intro.setStyleSheet(
            "background-color: rgba(43, 88, 169, 0.10); color: #274b86; border: 1px solid rgba(43, 88, 169, 0.18);"
            "border-radius: 12px; padding: 12px 14px; font-size: 13px; font-weight: 600;"
        )
        self.content_layout.addWidget(intro)
        form = QFormLayout()
        form.setSpacing(14)
        form.setLabelAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        form.setFormAlignment(Qt.AlignmentFlag.AlignTop)
        form.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.AllNonFixedFieldsGrow)
        self.stock_input = QSpinBox()
        self.stock_input.setMaximum(100000)
        self.stock_input.setValue(int(current_value))
        self.stock_input.setMinimumHeight(46)
        form.addRow("Stock Quantity", self.stock_input)
        self.content_layout.addLayout(form)

        buttons = self.create_button_box("Update Stock")
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        self.content_layout.addWidget(buttons)


class OrderDialog(ThemedDialog):
    def __init__(self, menu_items, offers, users, customers, current_user=None, restrict_to_current_user=False, parent=None):
        super().__init__("Create Order", "Choose where the order belongs, add items, and assign the responsible staff member.", width=700, parent=parent)
        self.menu_items = [
            item
            for item in menu_items
            if int(item["is_active"]) == 1 and (int(item["is_stock_tracked"]) == 0 or int(item["stock_qty"]) > 0)
        ]
        self.offers = [offer for offer in offers if int(offer["is_active"]) == 1]
        self.offer_map = {int(offer["id"]): dict(offer) for offer in self.offers}
        self.customers = sorted(customers, key=lambda customer: (customer["full_name"].lower(), customer["mobile"]))
        self.current_user = current_user or {}
        self.users = users
        if restrict_to_current_user and self.current_user.get("id") is not None:
            allowed_id = int(self.current_user["id"])
            self.users = [user for user in users if int(user["id"]) == allowed_id]
            if not self.users:
                self.users = [
                    {
                        "id": allowed_id,
                        "full_name": self.current_user.get("full_name", self.current_user.get("username", "Current User")),
                        "role": self.current_user.get("role", "Staff"),
                    }
                ]
        self.selected_items = []

        self.customer_mode_input = QComboBox()
        self.customer_mode_input.addItems(["Walk-in", "Existing Customer", "New Customer"])
        self.customer_select_input = QComboBox()
        self.customer_select_input.addItem("Select a customer", None)
        for customer in self.customers:
            label = f"{customer['full_name']} | {customer['mobile']}"
            self.customer_select_input.addItem(label, dict(customer))
        configure_combo_box(self.customer_mode_input, min_chars=14, popup_width=240)
        configure_combo_box(self.customer_select_input, min_chars=20, popup_width=420)
        self.customer_name_input = QLineEdit()
        self.customer_mobile_input = QLineEdit()
        self.customer_email_input = QLineEdit()
        self.customer_address_input = QLineEdit()
        self.customer_name_input.setPlaceholderText("Customer name")
        self.customer_mobile_input.setPlaceholderText("Mobile number")
        self.customer_email_input.setPlaceholderText("Email address")
        self.customer_address_input.setPlaceholderText("Address")
        self.source_input = QComboBox()
        self.source_input.setMaxVisibleItems(12)
        for label, table_name, order_type in ORDER_SOURCE_OPTIONS:
            self.source_input.addItem(label, {"table_name": table_name, "order_type": order_type})
        configure_combo_box(self.source_input, min_chars=14, popup_width=260)
        self.order_type_input = QComboBox()
        self.order_type_input.addItems(["Dine In", "Take Away", "Delivery"])
        self.order_type_input.setCurrentIndex(0)
        configure_combo_box(self.order_type_input, min_chars=14, popup_width=260)
        self.staff_input = QComboBox()
        # Only show users with role 'Waiter' in the staff dropdown
        self.waiter_users = [user for user in self.users if str(user.get('role', '')).strip().lower() == 'waiter']
        for user in self.waiter_users:
            self.staff_input.addItem(f"{user['full_name']} ({user['role']})", user["id"])
        configure_combo_box(self.staff_input, min_chars=18, popup_width=360)
        if restrict_to_current_user:
            self.staff_input.setEnabled(False)
        self.offer_input = QComboBox()
        self.offer_input.addItem("No Offer", None)
        for offer in self.offers:
            label = f"{offer['name']} ({offer['discount_type']} {offer['discount_value']})"
            self.offer_input.addItem(label, offer["id"])
        configure_combo_box(self.offer_input, min_chars=18, popup_width=420)
        # Apply consistent styling to input fields
        input_style = (
            "QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox {"
            "    border: 1px solid #bfbfbf;"
            "    border-radius: 4px;"
            "    padding: 6px;"
            "    background-color: #f9f9f9;"
            "    font-size: 14px;"
            "    color: #333333;"
            "}"
            "QLineEdit:focus, QComboBox:focus, QSpinBox:focus, QDoubleSpinBox:focus {"
            "    border: 1px solid #0078d7;"
            "    background-color: #ffffff;"
            "}"
            "QComboBox::drop-down {"
            "    border-left: 1px solid #bfbfbf;"
            "}"
            "QComboBox QAbstractItemView {"
            "    border: 1px solid #bfbfbf;"
            "    background-color: #ffffff;"
            "    selection-background-color: #0078d7;"
            "    selection-color: #ffffff;"
            "}"
        )

        self.customer_mode_input.setStyleSheet(input_style)
        self.customer_select_input.setStyleSheet(input_style)
        self.customer_name_input.setStyleSheet(input_style)
        self.customer_mobile_input.setStyleSheet(input_style)
        self.customer_email_input.setStyleSheet(input_style)
        self.customer_address_input.setStyleSheet(input_style)
        self.source_input.setStyleSheet(input_style)
        self.order_type_input.setStyleSheet(input_style)
        self.staff_input.setStyleSheet(input_style)
        self.offer_input.setStyleSheet(input_style)

        # Add placeholder text for better user experience
        self.customer_mode_input.setToolTip("Select the customer type")
        self.customer_select_input.setToolTip("Select an existing customer")
        self.customer_name_input.setPlaceholderText("Enter customer name")
        self.customer_mobile_input.setPlaceholderText("Enter mobile number")
        self.customer_email_input.setPlaceholderText("Enter email address")
        self.customer_address_input.setPlaceholderText("Enter address")
        self.source_input.setToolTip("Select the table for dine-in orders")
        self.order_type_input.setToolTip("Select the order type")
        self.staff_input.setToolTip("Select the staff responsible for the order")
        self.offer_input.setToolTip("Select an offer if applicable")

        # Adjust layout for better spacing and alignment
        form_layout = QFormLayout()
        form_layout.setSpacing(12)
        form_layout.addRow("Customer Type", self.customer_mode_input)
        form_layout.addRow("Select Customer", self.customer_select_input)
        form_layout.addRow("Customer Name", self.customer_name_input)
        form_layout.addRow("Mobile", self.customer_mobile_input)
        form_layout.addRow("Email", self.customer_email_input)
        form_layout.addRow("Address", self.customer_address_input)
        form_layout.addRow("Order Type", self.order_type_input)
        form_layout.addRow("Table (for Dine In)", self.source_input)
        form_layout.addRow("Assigned Staff", self.staff_input)
        form_layout.addRow("Offer", self.offer_input)

        self.content_layout.addLayout(form_layout)

        self.customer_mode_input.currentTextChanged.connect(self._handle_customer_mode_change)
        self.customer_select_input.currentIndexChanged.connect(self._handle_customer_selection_change)
        self.order_type_input.currentTextChanged.connect(self._handle_order_type_change)
        self.source_input.currentIndexChanged.connect(self._handle_order_source_change)
        self.offer_input.currentIndexChanged.connect(self.refresh_totals)

        item_intro = QLabel("Add items to the order below. Selecting the same item again updates its quantity in the current order instead of creating a duplicate row.")
        item_intro.setWordWrap(True)
        item_intro.setStyleSheet(
            "background-color: rgba(43, 88, 169, 0.10); color: #274b86; border: 1px solid rgba(43, 88, 169, 0.18);"
            "border-radius: 12px; padding: 12px 14px; font-size: 13px; font-weight: 600;"
        )
        self.content_layout.addWidget(item_intro)

        item_row = QGridLayout()
        item_row.setHorizontalSpacing(12)
        item_row.setVerticalSpacing(10)
        self.item_input = QComboBox()
        for item in self.menu_items:
            stock_note = (
                f"Stock {item['stock_qty']}"
                if int(item["is_stock_tracked"]) == 1
                else "Made fresh on order"
            )
            self.item_input.addItem(f"{item['name']} ({format_currency(item['price'])}, {stock_note})", item["id"])
        configure_combo_box(self.item_input, min_chars=18, popup_width=440)
        self.item_input.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.item_input.currentIndexChanged.connect(self._sync_item_selection_state)
        self.item_id_input = QLineEdit()
        self.item_id_input.setReadOnly(True)
        self.item_price_input = QLineEdit()
        self.item_price_input.setReadOnly(True)
        self.quantity_input = QSpinBox()
        self.quantity_input.setMinimum(1)
        self.quantity_input.setMaximum(100)
        self.quantity_input.setMaximumWidth(110)
        for widget in (self.item_id_input, self.item_price_input, self.quantity_input):
            widget.setMinimumHeight(44)
        add_button = QPushButton("Add Item")
        self.add_item_button = add_button
        add_button.clicked.connect(self.add_item)
        style_button(add_button, "primary")
        remove_button = QPushButton("Remove Item")
        remove_button.clicked.connect(self.remove_selected_item)
        style_button(remove_button, "soft")

        self.item_hint_label = QLabel("")
        self.item_hint_label.setWordWrap(True)
        self.item_hint_label.setStyleSheet("color: #6b584c; font-size: 13px; font-weight: 600;")
        self.item_action_label = QLabel("Choose a menu item, review its ID and price, enter quantity, then click Add Item.")
        self.item_action_label.setWordWrap(True)
        self.item_action_label.setStyleSheet("color: #8a674d; font-size: 12px;")

        item_row.addWidget(QLabel("Menu Item"), 0, 0)
        item_row.addWidget(QLabel("Item ID"), 0, 1)
        item_row.addWidget(QLabel("Unit Price"), 0, 2)
        item_row.addWidget(QLabel("Qty To Add"), 0, 3)
        item_row.addWidget(self.item_input, 1, 0)
        item_row.addWidget(self.item_id_input, 1, 1)
        item_row.addWidget(self.item_price_input, 1, 2)
        item_row.addWidget(self.quantity_input, 1, 3)
        item_row.addWidget(self.item_hint_label, 2, 0, 1, 4)
        item_row.addWidget(self.item_action_label, 3, 0, 1, 4)
        item_row.addWidget(add_button, 4, 2)
        item_row.addWidget(remove_button, 4, 3)
        item_row.setColumnStretch(0, 1)
        item_row.setColumnStretch(1, 1)
        item_row.setColumnStretch(2, 1)
        self.content_layout.addLayout(item_row)

        self.items_table = QTableWidget(0, 5)
        self.items_table.setHorizontalHeaderLabels(["ID", "Item", "Qty", "Unit Price", "Line Total"])
        self.items_table.setColumnHidden(0, True)
        configure_table_widget(self.items_table, stretch_last=True)
        self.items_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.items_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.items_table.setMinimumHeight(180)
        self.content_layout.addWidget(self.items_table)

        self.summary_label = QLabel("Subtotal: Rs.0.00")
        self.summary_label.setWordWrap(True)
        self.summary_label.setStyleSheet("font-size: 14px; font-weight: 700; color: #5a473d;")
        self.content_layout.addWidget(self.summary_label)

        buttons = self.create_button_box("Create Order")
        buttons.accepted.connect(self.validate_and_accept)
        buttons.rejected.connect(self.reject)
        self.content_layout.addWidget(buttons)
        self._handle_customer_mode_change(self.customer_mode_input.currentText())
        self._handle_order_type_change(self.order_type_input.currentText())
        self._sync_item_selection_state()
        self.refresh_totals()

    def update_order_type(self):
        self._handle_order_source_change(self.source_input.currentIndex())

    def _current_menu_item(self):
        menu_item_id = self.item_input.currentData()
        if menu_item_id is None:
            return None
        return next((item for item in self.menu_items if int(item["id"]) == int(menu_item_id)), None)

    def _selected_quantity_for_item(self, menu_item_id):
        return next(
            (int(item["quantity"]) for item in self.selected_items if int(item["menu_item_id"]) == int(menu_item_id)),
            0,
        )

    def _available_quantity_for_item(self, menu_item):
        return max(int(menu_item["stock_qty"]) - self._selected_quantity_for_item(menu_item["id"]), 0)

    def _sync_item_selection_state(self):
        menu_item = self._current_menu_item()
        if not menu_item:
            self.quantity_input.setEnabled(False)
            self.quantity_input.setMinimum(1)
            self.quantity_input.setMaximum(1)
            self.quantity_input.setValue(1)
            self.item_id_input.clear()
            self.item_price_input.clear()
            self.add_item_button.setEnabled(False)
            self.add_item_button.setText("Add Item")
            self.add_item_button.setToolTip("No menu item available to add.")
            self.item_hint_label.setText("No menu item available.")
            self.item_action_label.setText("Choose a menu item, review its ID and price, enter quantity, then click Add Item.")
            return

        available_quantity = self._available_quantity_for_item(menu_item)
        already_added = self._selected_quantity_for_item(menu_item["id"])
        self.item_id_input.setText(str(menu_item["id"]))
        self.item_price_input.setText(format_currency(menu_item["price"]))
        is_stock_tracked = int(menu_item["is_stock_tracked"]) == 1
        self.quantity_input.setMinimum(1)
        if is_stock_tracked:
            self.quantity_input.setEnabled(available_quantity > 0)
            self.quantity_input.setMaximum(max(1, available_quantity))
            self.quantity_input.setValue(min(max(1, self.quantity_input.value()), max(1, available_quantity)))
            self.add_item_button.setEnabled(available_quantity > 0)
        else:
            self.quantity_input.setEnabled(True)
            self.quantity_input.setMaximum(100)
            self.quantity_input.setValue(max(1, self.quantity_input.value()))
            self.add_item_button.setEnabled(True)
        self.add_item_button.setText("Update Qty" if already_added > 0 else "Add Item")
        if not is_stock_tracked:
            self.add_item_button.setToolTip(f"{menu_item['name']} is prepared fresh and does not use direct stock deduction.")
            self.item_input.setToolTip(f"{menu_item['name']} | prepared fresh on order")
            self.item_hint_label.setText(
                f"{menu_item['name']} | Price: {format_currency(menu_item['price'])} | Item ID: {menu_item['id']} | Prepared fresh on order | Already in order: {already_added}"
            )
            if already_added > 0:
                self.item_action_label.setText("This prepared item is already in the order. Adding again increases its quantity in the same row.")
            else:
                self.item_action_label.setText("This prepared item does not use stock tracking. Enter quantity and click Add Item.")
        elif available_quantity > 0:
            self.add_item_button.setToolTip(f"Add up to {available_quantity} unit(s) of {menu_item['name']}.")
            self.item_input.setToolTip(f"{menu_item['name']} | {available_quantity} unit(s) still available for this order")
            self.item_hint_label.setText(
                f"{menu_item['name']} | Item ID: {menu_item['id']} | Price: {format_currency(menu_item['price'])} | In stock: {menu_item['stock_qty']} | Already in order: {already_added} | Can add now: {available_quantity}"
            )
            if already_added > 0:
                self.item_action_label.setText("This item is already in the order. Adding again increases its quantity in the same row.")
            else:
                self.item_action_label.setText("This item is not yet in the order. Choose quantity and click Add Item.")
        else:
            self.add_item_button.setToolTip(f"All available stock of {menu_item['name']} is already added to this order.")
            self.item_input.setToolTip(f"{menu_item['name']} is already fully added to this order")
            self.item_hint_label.setText(
                f"{menu_item['name']} | Item ID: {menu_item['id']} | Price: {format_currency(menu_item['price'])} | In stock: {menu_item['stock_qty']} | Already in order: {already_added} | Can add now: 0"
            )
            self.item_action_label.setText("All available stock of this item is already included in the current order.")

    def add_item(self):
        menu_item = self._current_menu_item()
        if not menu_item:
            QMessageBox.information(self, "Order", "Select a menu item first.")
            return
        menu_item_id = int(menu_item["id"])
        quantity = int(self.quantity_input.value())

        available_quantity = self._available_quantity_for_item(menu_item)
        if int(menu_item["is_stock_tracked"]) == 1 and available_quantity <= 0:
            QMessageBox.warning(
                self,
                "Order",
                f"All available stock of {menu_item['name']} is already added to this order.",
            )
            self._sync_item_selection_state()
            return
        if int(menu_item["is_stock_tracked"]) == 1 and quantity > available_quantity:
            QMessageBox.warning(
                self,
                "Order",
                f"Only {available_quantity} more unit(s) of {menu_item['name']} can be added.",
            )
            self.quantity_input.setValue(available_quantity)
            return

        existing = next((item for item in self.selected_items if int(item["menu_item_id"]) == menu_item_id), None)
        if existing:
            existing["quantity"] += quantity
            self.item_action_label.setText(
                f"Updated {menu_item['name']} to {existing['quantity']} total unit(s) in the current order."
            )
        else:
            self.selected_items.append({"menu_item_id": menu_item_id, "name": menu_item["name"], "price": float(menu_item["price"]), "quantity": quantity})
            self.item_action_label.setText(
                f"Added {menu_item['name']} with {quantity} unit(s) to the current order."
            )
        self.refresh_items_table()
        self._select_item_row(menu_item_id)
        self._sync_item_selection_state()

    def remove_selected_item(self):
        row = self.items_table.currentRow()
        if row < 0:
            return
        item_id = int(self.items_table.item(row, 0).text())
        self.selected_items = [item for item in self.selected_items if int(item["menu_item_id"]) != item_id]
        self.refresh_items_table()
        self._sync_item_selection_state()
        self.item_action_label.setText("Removed the selected item from the current order.")

    def _select_item_row(self, menu_item_id):
        for row in range(self.items_table.rowCount()):
            item = self.items_table.item(row, 0)
            if item and int(item.text()) == int(menu_item_id):
                self.items_table.selectRow(row)
                return

    def refresh_items_table(self):
        self.items_table.setRowCount(len(self.selected_items))
        for row, item in enumerate(self.selected_items):
            line_total = item["price"] * item["quantity"]
            values = [
                item["menu_item_id"],
                item["name"],
                item["quantity"],
                format_currency(item["price"]),
                format_currency(line_total),
            ]
            for column, value in enumerate(values):
                self.items_table.setItem(row, column, QTableWidgetItem(str(value)))
        self.items_table.resizeRowsToContents()
        self.refresh_totals()

    def validate_and_accept(self):
        if not self.selected_items:
            QMessageBox.warning(self, "Order", "Add at least one item before creating the order.")
            return
        order_type = self.order_type_input.currentText()
        if not order_type:
            QMessageBox.warning(self, "Order", "Select an order type.")
            return
        if order_type == "Dine In" and not self.source_input.currentData():
            QMessageBox.warning(self, "Order", "Choose a table for dine-in orders.")
            return
        customer_mode = self.customer_mode_input.currentText()
        if customer_mode == "Existing Customer" and not self.customer_select_input.currentData():
            QMessageBox.warning(self, "Order", "Select an existing customer for this order.")
            return
        if customer_mode == "New Customer":
            if not self.customer_name_input.text().strip() or not self.customer_mobile_input.text().strip():
                QMessageBox.warning(self, "Order", "Enter at least customer name and mobile number for a new customer.")
                return
        self.accept()

    def _set_customer_fields(self, customer_name="", mobile="", email="", address=""):
        self.customer_name_input.setText(customer_name)
        self.customer_mobile_input.setText(mobile)
        self.customer_email_input.setText(email)
        self.customer_address_input.setText(address)

    def _handle_customer_mode_change(self, mode):
        is_walk_in = mode == "Walk-in"
        is_existing = mode == "Existing Customer"
        is_new = mode == "New Customer"

        self.customer_select_input.setEnabled(is_existing)
        self.customer_name_input.setReadOnly(is_walk_in or is_existing)
        self.customer_mobile_input.setReadOnly(is_walk_in or is_existing)
        self.customer_email_input.setReadOnly(is_walk_in or is_existing)
        self.customer_address_input.setReadOnly(is_walk_in or is_existing)

        if is_walk_in:
            self.customer_select_input.setCurrentIndex(0)
            self._set_customer_fields("Walk-in", "", "", "")
            return

        if is_existing:
            if self.customer_select_input.currentData():
                self._handle_customer_selection_change(self.customer_select_input.currentIndex())
            elif self.customer_select_input.count() > 1:
                self.customer_select_input.setCurrentIndex(1)
            else:
                self._set_customer_fields("", "", "", "")
            return

        self.customer_select_input.setCurrentIndex(0)
        self._set_customer_fields("", "", "", "")

    def _handle_customer_selection_change(self, index):
        if self.customer_mode_input.currentText() != "Existing Customer":
            return
        customer = self.customer_select_input.itemData(index)
        if not customer:
            self._set_customer_fields("", "", "", "")
            return
        self._set_customer_fields(
            customer.get("full_name", ""),
            customer.get("mobile", ""),
            customer.get("email", ""),
            customer.get("address", ""),
        )

    def _handle_order_source_change(self, index):
        source = self.source_input.itemData(index) or {}
        order_type = source.get("order_type", "")
        if order_type and self.order_type_input.currentText() != order_type:
            self.order_type_input.setCurrentText(order_type)

    def _handle_order_type_change(self, order_type):
        if order_type == "Dine In":
            self.source_input.setEnabled(True)
            current_table_name = (self.source_input.currentData() or {}).get("table_name")
            self.source_input.clear()
            selected_index = 0
            for label, table_name, _ in ORDER_SOURCE_OPTIONS:
                if "Table" in label:
                    self.source_input.addItem(label, {"table_name": table_name, "order_type": "Dine In"})
                    if table_name == current_table_name:
                        selected_index = self.source_input.count() - 1
            self.source_input.setCurrentIndex(selected_index)
        else:
            self.source_input.setEnabled(False)
            self.source_input.clear()
            table_name = "Takeaway" if order_type == "Take Away" else order_type
            self.source_input.addItem(table_name, {"table_name": table_name, "order_type": order_type})

    def _current_offer(self):
        offer_id = self.offer_input.currentData()
        if offer_id is None:
            return None
        return self.offer_map.get(int(offer_id))

    def _compute_totals(self):
        subtotal = round(sum(float(item["price"]) * int(item["quantity"]) for item in self.selected_items), 2)
        offer = self._current_offer()
        discount_amount = 0.0
        offer_note = "No offer applied"
        if offer:
            minimum = float(offer["min_order_amount"])
            if subtotal >= minimum:
                if offer["discount_type"] == "percent":
                    discount_amount = round(subtotal * (float(offer["discount_value"]) / 100.0), 2)
                else:
                    discount_amount = min(round(float(offer["discount_value"]), 2), subtotal)
                offer_note = f"{offer['name']} applied"
            else:
                offer_note = f"{offer['name']} available on {format_currency(minimum)} and above"
        taxable_amount = max(round(subtotal - discount_amount, 2), 0.0)
        tax_amount = round(taxable_amount * (GST_RATE / 100.0), 2)
        grand_total = round(taxable_amount + tax_amount, 2)
        return {
            "subtotal": subtotal,
            "discount_amount": discount_amount,
            "taxable_amount": taxable_amount,
            "tax_amount": tax_amount,
            "grand_total": grand_total,
            "offer_note": offer_note,
        }

    def refresh_totals(self):
        totals = self._compute_totals()
        self.summary_label.setText(
            f"Subtotal: {format_currency(totals['subtotal'])} | "
            f"Discount: {format_currency(totals['discount_amount'])} | "
            f"GST ({format_percent(GST_RATE)}): {format_currency(totals['tax_amount'])} | "
            f"Grand Total: {format_currency(totals['grand_total'])}\n"
            f"{totals['offer_note']}"
        )

    def get_payload(self):
        order_type = self.order_type_input.currentText()
        source = self.source_input.currentData() or {}
        table_name = source.get("table_name") if order_type == "Dine In" else order_type.replace(" ", "")
        customer_mode = self.customer_mode_input.currentText()
        selected_customer = self.customer_select_input.currentData() if customer_mode == "Existing Customer" else None
        is_walk_in = customer_mode == "Walk-in"
        return {
            "customer_name": "Walk-in" if is_walk_in else self.customer_name_input.text().strip(),
            "table_name": table_name,
            "order_type": order_type,
            "staff_id": int(self.staff_input.currentData()),
            "offer_id": self.offer_input.currentData(),
            "customer_id": int(selected_customer["id"]) if selected_customer else None,
            "customer_mobile": "" if is_walk_in else self.customer_mobile_input.text().strip(),
            "customer_email": "" if is_walk_in else self.customer_email_input.text().strip(),
            "customer_address": "" if is_walk_in else self.customer_address_input.text().strip(),
            "save_customer": customer_mode == "New Customer",
            "items": [{"menu_item_id": int(item["menu_item_id"]), "quantity": int(item["quantity"])} for item in self.selected_items],
        }


class BillPreviewDialog(ThemedDialog):
    def __init__(self, invoice, parent=None):
        super().__init__("GST Bill Preview", "Review the bill and print it with GST breakdown.", width=700, parent=parent)
        self.invoice = invoice
        self.preview = QTextEdit()
        self.preview.setReadOnly(True)
        self.preview.setMinimumHeight(520)
        self.preview.setStyleSheet(
            """
            QTextEdit {
                background-color: #fffdf9;
                border: 1px solid #d6b089;
                border-radius: 12px;
                padding: 8px;
                color: #4d392d;
            }
            """
        )
        self.preview.setHtml(self._build_bill_html())
        self.content_layout.addWidget(self.preview)

        actions = QHBoxLayout()
        actions.addStretch()
        self.print_button = QPushButton("Print Bill")
        style_button(self.print_button, "primary", min_width=144)
        self.print_button.clicked.connect(self.print_bill)
        close_button = QPushButton("Close")
        style_button(close_button, "soft", min_width=120)
        close_button.clicked.connect(self.reject)
        actions.addWidget(self.print_button)
        actions.addWidget(close_button)
        self.content_layout.addLayout(actions)

    def _build_bill_html(self):
        item_rows = "".join(
            f"""
            <tr>
                <td style="padding:8px;border-bottom:1px solid #eadbcf;">{escape(str(item['item_name']))}</td>
                <td style="padding:8px;border-bottom:1px solid #eadbcf;text-align:center;">{int(item['quantity'])}</td>
                <td style="padding:8px;border-bottom:1px solid #eadbcf;text-align:right;">{escape(format_currency(item['unit_price']))}</td>
                <td style="padding:8px;border-bottom:1px solid #eadbcf;text-align:right;">{escape(format_currency(item['line_total']))}</td>
            </tr>
            """
            for item in self.invoice["items"]
        )
        paid_at = format_datetime(self.invoice["paid_at"]) if self.invoice.get("paid_at") else "-"
        created_at = format_datetime(self.invoice["created_at"])
        return f"""
        <div style="font-family:'Segoe UI'; color:#4d392d; padding:12px 10px;">
            <h1 style="margin:0; color:#5a3b1c;">Breaktime Restaurant</h1>
            <p style="margin:6px 0 18px 0; color:#8a674d;">GST Bill / Tax Invoice</p>
            <table style="width:100%; border-collapse:collapse; margin-bottom:18px;">
                <tr>
                    <td style="padding:4px 0;"><b>Order No:</b> {escape(self.invoice['order_number'])}</td>
                    <td style="padding:4px 0; text-align:right;"><b>Date:</b> {escape(created_at)}</td>
                </tr>
                <tr>
                    <td style="padding:4px 0;"><b>Customer:</b> {escape(self.invoice['customer_name'])}</td>
                    <td style="padding:4px 0; text-align:right;"><b>Order Type:</b> {escape(self.invoice['order_type'])}</td>
                </tr>
                <tr>
                    <td style="padding:4px 0;"><b>Mobile:</b> {escape(self.invoice.get('customer_mobile') or '-')}</td>
                    <td style="padding:4px 0; text-align:right;"><b>Source:</b> {escape(self.invoice['table_name'])}</td>
                </tr>
                <tr>
                    <td style="padding:4px 0;"><b>Email:</b> {escape(self.invoice.get('customer_email') or '-')}</td>
                    <td style="padding:4px 0; text-align:right;"><b>Staff:</b> {escape(self.invoice['staff_name'])}</td>
                </tr>
                <tr>
                    <td colspan="2" style="padding:4px 0;"><b>Address:</b> {escape(self.invoice.get('customer_address') or '-')}</td>
                </tr>
            </table>
            <table style="width:100%; border-collapse:collapse; margin-bottom:18px;">
                <thead>
                    <tr style="background:#efe1cf; color:#5a3b1c;">
                        <th style="padding:8px; text-align:left;">Item</th>
                        <th style="padding:8px; text-align:center;">Qty</th>
                        <th style="padding:8px; text-align:right;">Rate</th>
                        <th style="padding:8px; text-align:right;">Amount</th>
                    </tr>
                </thead>
                <tbody>{item_rows}</tbody>
            </table>
            <table style="width:100%; border-collapse:collapse;">
                <tr><td style="padding:4px 0;"><b>Subtotal</b></td><td style="padding:4px 0; text-align:right;">{escape(format_currency(self.invoice['subtotal']))}</td></tr>
                <tr><td style="padding:4px 0;"><b>Offer</b></td><td style="padding:4px 0; text-align:right;">{escape(self.invoice['offer_name'] or 'No Offer')}</td></tr>
                <tr><td style="padding:4px 0;"><b>Discount</b></td><td style="padding:4px 0; text-align:right;">{escape(format_currency(self.invoice['discount_amount']))}</td></tr>
                <tr><td style="padding:4px 0;"><b>Taxable Amount</b></td><td style="padding:4px 0; text-align:right;">{escape(format_currency(self.invoice['taxable_amount']))}</td></tr>
                <tr><td style="padding:4px 0;"><b>CGST ({format_percent(self.invoice['cgst_rate'])})</b></td><td style="padding:4px 0; text-align:right;">{escape(format_currency(self.invoice['cgst_amount']))}</td></tr>
                <tr><td style="padding:4px 0;"><b>SGST ({format_percent(self.invoice['sgst_rate'])})</b></td><td style="padding:4px 0; text-align:right;">{escape(format_currency(self.invoice['sgst_amount']))}</td></tr>
                <tr><td style="padding:8px 0; font-size:16px;"><b>Grand Total</b></td><td style="padding:8px 0; text-align:right; font-size:16px;"><b>{escape(format_currency(self.invoice['total_amount']))}</b></td></tr>
                <tr><td style="padding:4px 0;"><b>Payment Status</b></td><td style="padding:4px 0; text-align:right;">{escape(self.invoice['payment_status'])}</td></tr>
                <tr><td style="padding:4px 0;"><b>Payment Method</b></td><td style="padding:4px 0; text-align:right;">{escape(self.invoice['payment_method'])}</td></tr>
                <tr><td style="padding:4px 0;"><b>Paid At</b></td><td style="padding:4px 0; text-align:right;">{escape(paid_at)}</td></tr>
            </table>
            <p style="margin-top:18px; color:#8a674d;">GST rate assumed in this app: {format_percent(self.invoice['gst_rate'])}. Thank you for visiting Breaktime Restaurant.</p>
        </div>
        """

    def print_bill(self):
        printer = QPrinter(QPrinter.PrinterMode.HighResolution)
        dialog = QPrintDialog(printer, self)
        dialog.setWindowTitle("Print Bill")
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.preview.document().print(printer)


class DashboardWindow(QMainWindow):
    def __init__(self, login_window, current_user=None):
        super().__init__()
        self.login_window = login_window
        self.current_user = current_user or {}
        self.database = get_database()
        self.current_page_name = "Dashboard"
        self.current_role = str(self.current_user.get("role", "")).strip().lower()
        self.allowed_pages = ROLE_PAGE_ACCESS.get(
            self.current_role,
            {"Dashboard", "Orders", "Menu Items", "Billing", "Customers", "Users", "Reports", "Settings", "Logout"},
        )
        self.allowed_actions = ROLE_ACTION_ACCESS.get(
            self.current_role,
            {
                "create_order",
                "update_order_status",
                "apply_offer",
                "record_payment",
                "add_menu_item",
                "edit_menu_item",
                "update_menu_stock",
                "toggle_menu_item",
                "add_offer",
                "edit_offer",
                "toggle_offer",
                "add_customer",
                "view_stock",
            },
        )

        self.setWindowTitle("Breaktime Restaurant")
        self.setWindowIcon(QIcon(str(resource_path("app_icon.png"))))
        self.resize(1400, 900)
        self.setStyleSheet(
            """
            QMainWindow { background-color: #c87d33; }
            QMenuBar { background-color: #5a3a2f; color: white; padding: 6px; }
            QMenu { background-color: #5a3a2f; color: white; }
            QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox {
                background-color: rgba(255, 255, 255, 0.96);
                border: 1px solid #d6b089;
                border-radius: 8px;
                padding: 8px 10px;
                color: #4d392d;
                min-height: 18px;
            }
            QLineEdit:focus, QComboBox:focus, QSpinBox:focus, QDoubleSpinBox:focus {
                border: 1px solid #2b58a9;
            }
            QTableWidget {
                gridline-color: #eadbcf;
                selection-background-color: #f6d8b8;
                selection-color: #4d392d;
            }
            QHeaderView::section {
                padding: 8px;
                border: none;
            }
            QPushButton:hover {
                opacity: 0.95;
            }
            """
        )

        self._load_data()
        self._build_shell()
        start_page = next((item for item in NAVIGATION_ITEMS if item in self.allowed_pages and item != "Logout"), "Orders")
        self.refresh_pages(start_page)

    def _build_shell(self):
        menu_bar = self.menuBar()
        menu_bar.addMenu("File")
        menu_bar.addMenu("Settings")
        menu_bar.addMenu("Help")

        central = WarmBackgroundWidget()
        self.setCentralWidget(central)
        root = QHBoxLayout(central)
        root.setContentsMargins(18, 18, 18, 24)
        root.setSpacing(18)

        sidebar = QFrame()
        sidebar.setFixedWidth(250)
        sidebar.setStyleSheet("background-color: rgba(64, 33, 24, 0.90); border: 1px solid rgba(255,255,255,0.05); border-radius: 10px;")
        add_shadow(sidebar, blur=30)
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(12, 12, 12, 16)
        sidebar_layout.setSpacing(8)

        title = QLabel("Breaktime Restaurant")
        title.setWordWrap(True)
        title.setStyleSheet("color: #f6ece6; font-size: 18px; font-weight: 700; padding: 12px 10px;")
        sidebar_layout.addWidget(title)

        profile_card = QFrame()
        profile_card.setStyleSheet("background-color: rgba(255,255,255,0.08); border-radius: 10px;")
        profile_layout = QVBoxLayout(profile_card)
        profile_layout.setContentsMargins(12, 10, 12, 10)
        profile_layout.setSpacing(4)
        profile_name = QLabel(self.current_user.get("full_name", "Team"))
        profile_name.setStyleSheet("color: white; font-size: 15px; font-weight: 700;")
        profile_role = QLabel(self.current_user.get("role", "Staff"))
        profile_role.setStyleSheet("color: #f3d7c2; font-size: 12px;")
        profile_layout.addWidget(profile_name)
        profile_layout.addWidget(profile_role)
        sidebar_layout.addWidget(profile_card)

        self.sidebar_buttons = {}
        for name in NAVIGATION_ITEMS:
            button = NavButton(name, active=name == "Dashboard", danger=name == "Logout")
            self.sidebar_buttons[name] = button
            sidebar_layout.addWidget(button)
            if name not in self.allowed_pages:
                button.hide()
        sidebar_layout.addStretch()

        self.page_stack = CurrentPageStackedWidget()
        self.page_stack.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Maximum)
        self.content_scroll = QScrollArea()
        self.content_scroll.setWidgetResizable(True)
        self.content_scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.content_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.content_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.content_scroll.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.content_scroll.setStyleSheet("background: transparent;")

        content = QWidget()
        content.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Maximum)
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        content_layout.addWidget(self.page_stack)
        self.content_scroll.setWidget(content)

        root.addWidget(sidebar)
        root.addWidget(self.content_scroll, 1)

        for name, button in self.sidebar_buttons.items():
            if name == "Logout":
                button.clicked.connect(self.logout)
            else:
                button.clicked.connect(lambda _, page=name: self.show_page(page))

        self._fit_to_screen()

    def _fit_to_screen(self):
        screen = self.screen() or QGuiApplication.primaryScreen()
        if not screen:
            return
        available = screen.availableGeometry()
        self.resize(min(1400, max(1040, available.width() - 40)), min(900, max(740, available.height() - 40)))

    def _load_data(self):
        self.metrics = self.database.get_dashboard_metrics()
        self.orders = self.database.get_all_orders()
        self.active_orders = self.database.get_active_orders()
        self.kitchen_queue = self.database.get_kitchen_queue()
        self.menu_items = self.database.get_menu_items(include_inactive=True)
        self.offers = self.database.get_offers(include_inactive=True)
        self.users = self.database.get_all_users()
        self.customer_records = self.database.get_all_customers()
        self.payments = self.database.get_recent_payments()
        self.customers = self.database.get_customer_insights()
        self.staff_report = self.database.get_staff_sales_report()
        self.offer_report = self.database.get_offer_sales_report()
        self.payment_report = self.database.get_payment_method_report()
        self.stock_report = self.database.get_stock_report()
        self.top_items = self.database.get_top_menu_items()
    def refresh_pages(self, page_name=None):
        target_page = page_name or self.current_page_name
        self._load_data()
        while self.page_stack.count():
            page = self.page_stack.widget(0)
            self.page_stack.removeWidget(page)
            page.deleteLater()

        self.pages = {
            "Dashboard": self._build_dashboard_page(),
            "Orders": self._build_orders_page(),
            "Menu Items": self._build_menu_page(),
            "Billing": self._build_billing_page(),
            "Customers": self._build_customers_page(),
            "Users": self._build_users_page(),
            "Reports": self._build_reports_page(),
            "Settings": self._build_settings_page(),
        }
        for page in self.pages.values():
            self.page_stack.addWidget(page)
        self.show_page(target_page)

    def show_page(self, page_name):
        if page_name not in self.allowed_pages:
            return
        page = self.pages.get(page_name)
        if page is None:
            return
        self.current_page_name = page_name
        self.page_stack.setCurrentWidget(page)
        page_height = max(page.minimumSizeHint().height(), page.sizeHint().height())
        self.page_stack.setMinimumHeight(page_height)
        self.page_stack.setMaximumHeight(page_height)
        self.page_stack.updateGeometry()
        for name, button in self.sidebar_buttons.items():
            button.set_active(name == page_name)

    def _can(self, action_name):
        return action_name in self.allowed_actions

    def _create_page(self, title_text, subtitle_text):
        page = QWidget()
        page.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Maximum)
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(18)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        heading = QLabel(title_text)
        heading.setStyleSheet("color: white; font-size: 28px; font-weight: 700;")
        subtitle = QLabel(subtitle_text)
        subtitle.setStyleSheet("color: rgba(255, 245, 236, 0.92); font-size: 15px;")
        subtitle.setWordWrap(True)
        layout.addWidget(heading)
        layout.addWidget(subtitle)
        return page, layout

    def _cards_row(self, cards):
        row = QHBoxLayout()
        row.setSpacing(14)
        for title, value, color in cards:
            row.addWidget(StatCard(title, value, color))
        return row

    def _create_button_row(self, buttons):
        grid = QGridLayout()
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setHorizontalSpacing(10)
        grid.setVerticalSpacing(10)
        columns = min(3 if len(buttons) > 4 else 4, max(1, len(buttons)))
        for index, (text, handler, style) in enumerate(buttons):
            button = QPushButton(text)
            button.setSizePolicy(QSizePolicy.Policy.MinimumExpanding, QSizePolicy.Policy.Fixed)
            style_button(button, style, min_width=150, min_height=44)
            button.clicked.connect(handler)
            row, column = divmod(index, columns)
            grid.addWidget(button, row, column)
        for column in range(columns):
            grid.setColumnStretch(column, 1)
        return grid

    def _create_table(self, headers):
        table = QTableWidget(0, len(headers))
        table.setHorizontalHeaderLabels(headers)
        configure_table_widget(table)
        table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        table.setAlternatingRowColors(True)
        table.verticalHeader().setVisible(False)
        table.setMinimumHeight(240)
        table.setStyleSheet(
            """
            QTableWidget {
                background-color: rgba(255,255,255,0.96);
                alternate-background-color: #f7ede1;
                color: #4d392d;
                border-radius: 8px;
                border: 1px solid rgba(166, 120, 72, 0.28);
                gridline-color: #eadbcf;
            }
            QTableWidget::item {
                color: #4d392d;
                padding: 6px;
            }
            QTableWidget::item:selected {
                background-color: #f6d8b8;
                color: #4d392d;
            }
            QHeaderView::section {
                background-color: #efe1cf;
                color: #5a3b1c;
                font-weight: 700;
                padding: 8px;
                border: none;
            }
            """
        )
        return table

    def _fill_table(self, table, rows):
        table.setRowCount(len(rows))
        for row_index, row_values in enumerate(rows):
            for column_index, value in enumerate(row_values):
                item = QTableWidgetItem(str(value))
                item.setForeground(QColor("#4d392d"))
                item.setToolTip(str(value))
                if column_index == 0:
                    item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                table.setItem(row_index, column_index, item)
        table.resizeColumnsToContents()
        table.resizeRowsToContents()

    def _select_first_row(self, table):
        if table.rowCount() > 0:
            table.selectRow(0)

    def _selected_id(self, table):
        row = table.currentRow()
        if row < 0:
            return None
        item = table.item(row, 0)
        return int(item.text()) if item else None

    def _build_dashboard_page(self):
        page, layout = self._create_page(
            f"Welcome back, {self.current_user.get('full_name', 'Team')}",
            "Restaurant operations, menu, offers, billing, and stock are now managed from one place.",
        )
        layout.addLayout(self._cards_row([
            ("Total Sales", format_currency(self.metrics["total_sales"]), "#1e67c6"),
            ("Total Orders", str(self.metrics["total_orders"]), "#79a70b"),
            ("Pending Bills", format_currency(self.metrics["pending_bills"]), "#d9881f"),
        ]))

        panels = QHBoxLayout()
        panels.setSpacing(14)
        recent_panel = SectionPanel("Recent Orders")
        recent_panel.setMaximumHeight(405)
        recent_badges = QHBoxLayout()
        recent_badges.addWidget(BadgeLabel(f"{len(self.orders)} orders tracked", "#2b58a9"))
        recent_badges.addWidget(BadgeLabel(f"{self.metrics['ready_to_serve']} ready now", "#4f8c2f"))
        recent_badges.addStretch()
        recent_panel.content.addLayout(recent_badges)
        recent_table = self._create_table(["ID", "Order", "Customer", "Total", "Status", "Payment"])
        recent_table.setColumnHidden(0, True)
        recent_table.setMinimumHeight(180)
        recent_table.setMaximumHeight(235)
        self._fill_table(recent_table, [[order["id"], order["order_number"], order["customer_name"], format_currency(order["total_amount"]), order["status"], order["payment_status"]] for order in self.orders[:6]])
        recent_panel.content.addWidget(recent_table)

        stock_panel = SectionPanel("Low Stock Alerts")
        stock_panel.setMaximumHeight(405)
        low_stock = [item for item in self.stock_report if item["stock_status"] == "Low Stock"]
        stock_badges = QHBoxLayout()
        stock_badges.addWidget(BadgeLabel(f"{len(low_stock)} attention needed", "#c7462d"))
        stock_badges.addStretch()
        stock_panel.content.addLayout(stock_badges)
        stock_table = self._create_table(["ID", "Item", "Stock", "Reorder", "Status"])
        stock_table.setColumnHidden(0, True)
        stock_table.setMinimumHeight(180)
        stock_table.setMaximumHeight(235)
        self._fill_table(stock_table, [[item["id"], item["name"], item["stock_qty"], item["reorder_level"], item["stock_status"]] for item in low_stock[:8]])
        stock_panel.content.addWidget(stock_table)

        panels.addWidget(recent_panel, 3)
        panels.addWidget(stock_panel, 2)
        layout.addLayout(panels)
        return page

    def _build_orders_page(self):
        page, layout = self._create_page("Orders", "Take new orders, update kitchen progress, and review line items for each order.")
        active_unpaid = sum(1 for order in self.orders if order["payment_status"] != "Paid")
        layout.addLayout(self._cards_row([
            ("Active Orders", str(self.metrics["active_orders"]), "#2b58a9"),
            ("Ready To Serve", str(self.metrics["ready_to_serve"]), "#4f8c2f"),
            ("Unpaid Orders", str(active_unpaid), "#d9881f"),
        ]))
        order_buttons = []
        if self._can("create_order"):
            order_buttons.append(("New Order", self.create_order, "primary"))
        if self._can("update_order_status"):
            order_buttons.extend(
                [
                    ("Mark Preparing", lambda: self.update_selected_order_status("Preparing"), "secondary"),
                    ("Mark Ready", lambda: self.update_selected_order_status("Ready"), "secondary"),
                    ("Mark Served", lambda: self.update_selected_order_status("Served"), "secondary"),
                    ("Cancel Order", lambda: self.update_selected_order_status("Cancelled"), "danger"),
                ]
            )
        order_buttons.append(("Refresh", lambda: self.refresh_pages("Orders"), "secondary"))
        layout.addLayout(self._create_button_row(order_buttons))

        panels = QHBoxLayout()
        panels.setSpacing(14)
        orders_panel = SectionPanel("Order Queue")
        orders_panel.setMaximumHeight(430)
        self.orders_table = self._create_table(["ID", "Order", "Customer", "Table", "Type", "Staff", "Items", "Total", "Status", "Payment"])
        self.orders_table.setColumnHidden(0, True)
        self.orders_table.setMinimumHeight(220)
        self.orders_table.setMaximumHeight(280)
        self._fill_table(self.orders_table, [[order["id"], order["order_number"], order["customer_name"], order["table_name"], order["order_type"], order["staff_name"], order["items_count"], format_currency(order["total_amount"]), order["status"], order["payment_status"]] for order in self.active_orders])
        self.orders_table.itemSelectionChanged.connect(self.refresh_order_items_table)
        orders_panel.content.addWidget(self.orders_table)
        self._select_first_row(self.orders_table)

        details_panel = SectionPanel("Order Items")
        details_panel.setMaximumHeight(430)
        self.order_meta_label = QLabel("Select an order to view item details.")
        self.order_meta_label.setWordWrap(True)
        self.order_meta_label.setStyleSheet("color: #6b584c; font-size: 14px; font-weight: 600;")
        details_panel.content.addWidget(self.order_meta_label)
        self.order_items_table = self._create_table(["Item", "Qty", "Unit Price", "Line Total"])
        self.order_items_table.setMinimumHeight(180)
        self.order_items_table.setMaximumHeight(240)
        details_panel.content.addWidget(self.order_items_table)
        panels.addWidget(orders_panel, 3)
        panels.addWidget(details_panel, 2)
        panels.setStretch(0, 3)
        panels.setStretch(1, 2)
        layout.addLayout(panels)
        self.refresh_order_items_table()
        return page
    def _build_menu_page(self):
        page, layout = self._create_page("Menu Items", "Add items, edit prices, update stock, and control which items are active for ordering.")
        low_stock = sum(1 for item in self.stock_report if item["stock_status"] == "Low Stock")
        total_stock = sum(int(item["stock_qty"]) for item in self.stock_report)
        tracked_items = sum(1 for item in self.menu_items if int(item["is_stock_tracked"]) == 1)
        stock_status_map = {int(item["id"]): item["stock_status"] for item in self.stock_report}
        layout.addLayout(self._cards_row([
            ("Menu Items", str(len(self.menu_items)), "#2b58a9"),
            ("Tracked Items", str(tracked_items), "#c7462d"),
            ("Tracked Units", str(total_stock), "#d9881f"),
        ]))
        menu_buttons = []
        if self._can("add_menu_item"):
            menu_buttons.append(("Add Item", self.add_menu_item, "primary"))
        if self._can("edit_menu_item"):
            menu_buttons.append(("Edit Item", self.edit_menu_item, "secondary"))
        if self._can("update_menu_stock"):
            menu_buttons.append(("Update Stock", self.update_menu_stock, "secondary"))
        if self._can("toggle_menu_item"):
            menu_buttons.append(("Toggle Active", self.toggle_menu_item, "secondary"))
        menu_buttons.append(("Refresh", lambda: self.refresh_pages("Menu Items"), "secondary"))
        layout.addLayout(self._create_button_row(menu_buttons))
        panel = SectionPanel("Menu Catalog")
        self.menu_table = self._create_table(["ID", "Name", "Category", "Price", "Stock Tracking", "Stock", "Reorder", "Active", "Stock Status"])
        self.menu_table.setColumnHidden(0, True)
        self._fill_table(
            self.menu_table,
            [
                [
                    item["id"],
                    item["name"],
                    item["category"],
                    format_currency(item["price"]),
                    "Tracked" if int(item["is_stock_tracked"]) == 1 else "Prepared",
                    item["stock_qty"] if int(item["is_stock_tracked"]) == 1 else "-",
                    item["reorder_level"] if int(item["is_stock_tracked"]) == 1 else "-",
                    "Yes" if int(item["is_active"]) == 1 else "No",
                    stock_status_map.get(int(item["id"]), "Healthy") if int(item["is_stock_tracked"]) == 1 else "Not Tracked",
                ]
                for item in self.menu_items
            ],
        )
        panel.content.addWidget(self.menu_table)
        self._select_first_row(self.menu_table)
        layout.addWidget(panel)
        return page

    def _build_billing_page(self):
        page, layout = self._create_page("Billing", "Process payments, manage offers, and track recent transaction activity.")
        unpaid_orders = self.database.get_unpaid_orders()
        layout.addLayout(self._cards_row([
            ("Collected Revenue", format_currency(self.metrics["total_sales"]), "#1e67c6"),
            ("Pending Amount", format_currency(self.metrics["pending_bills"]), "#d9881f"),
            ("Discount Given", format_currency(self.metrics["total_discount"]), "#7aaa1e"),
        ]))
        billing_buttons = []
        if self._can("apply_offer"):
            billing_buttons.append(("Apply Offer", self.apply_offer_to_selected_order, "primary"))
        billing_buttons.append(("Print Bill", self.show_bill_preview, "secondary"))
        if self._can("record_payment"):
            billing_buttons.extend(
                [
                    ("Cash Payment", lambda: self.record_selected_payment("Cash"), "secondary"),
                    ("Card Payment", lambda: self.record_selected_payment("Card"), "secondary"),
                    ("UPI Payment", lambda: self.record_selected_payment("UPI"), "secondary"),
                ]
            )
        if self._can("add_offer"):
            billing_buttons.append(("Add Offer", self.add_offer, "secondary"))
        if self._can("edit_offer"):
            billing_buttons.append(("Edit Offer", self.edit_offer, "secondary"))
        if self._can("toggle_offer"):
            billing_buttons.append(("Toggle Offer", self.toggle_offer, "secondary"))
        billing_buttons.append(("Refresh", lambda: self.refresh_pages("Billing"), "secondary"))
        layout.addLayout(self._create_button_row(billing_buttons))

        top = QHBoxLayout()
        orders_panel = SectionPanel("Pending Billing Orders")
        self.billing_orders_table = self._create_table(["ID", "Order", "Customer", "Offer", "Discount", "Total", "Payment"])
        self.billing_orders_table.setColumnHidden(0, True)
        self._fill_table(self.billing_orders_table, [[order["id"], order["order_number"], order["customer_name"], order["offer_name"] or "No Offer", format_currency(order["discount_amount"]), format_currency(order["total_amount"]), order["payment_status"]] for order in unpaid_orders])
        orders_panel.content.addWidget(self.billing_orders_table)
        self._select_first_row(self.billing_orders_table)

        offers_panel = SectionPanel("Offers")
        self.offers_table = self._create_table(["ID", "Name", "Type", "Value", "Min Order", "Active"])
        self.offers_table.setColumnHidden(0, True)
        self._fill_table(self.offers_table, [[offer["id"], offer["name"], offer["discount_type"], offer["discount_value"], format_currency(offer["min_order_amount"]), "Yes" if int(offer["is_active"]) == 1 else "No"] for offer in self.offers])
        offers_panel.content.addWidget(self.offers_table)
        self._select_first_row(self.offers_table)

        top.addWidget(orders_panel, 3)
        top.addWidget(offers_panel, 2)
        layout.addLayout(top)

        payments_panel = SectionPanel("Recent Payments")
        payments_table = self._create_table(["Order", "Customer", "Method", "Amount", "Offer", "Paid At"])
        self._fill_table(payments_table, [[payment["order_number"], payment["customer_name"], payment["method"], format_currency(payment["amount"]), payment["offer_name"] or "No Offer", payment["paid_at"]] for payment in self.payments])
        payments_panel.content.addWidget(payments_table)
        layout.addWidget(payments_panel)
        return page

    def _build_customers_page(self):
        page, layout = self._create_page("Customers", "Review frequent guests, customer spend, and add new customers when needed.")
        repeat_customers = sum(1 for customer in self.customers if int(customer["total_orders"]) > 1)
        layout.addLayout(self._cards_row([
            ("Customer Records", str(len(self.customer_records)), "#2b58a9"),
            ("Repeat Customers", str(repeat_customers), "#7aaa1e"),
            ("Walk-in Orders", str(sum(1 for order in self.orders if order["customer_name"] == "Walk-in")), "#d9881f"),
        ]))
        customer_buttons = [("Refresh", lambda: self.refresh_pages("Customers"), "secondary")]
        if self._can("add_customer"):
            customer_buttons.insert(0, ("Add Customer", self.add_customer, "primary"))
        if self.current_role == "administrator":
            customer_buttons.insert(1, ("Delete Customer", self.delete_customer, "danger"))
        layout.addLayout(self._create_button_row(customer_buttons))

        records_panel = SectionPanel("Customer Registry")
        self.customer_table = self._create_table(["ID", "Name", "Mobile", "Email", "Address", "Created"])
        self.customer_table.setColumnHidden(0, True)
        self._fill_table(
            self.customer_table,
            [[customer["id"], customer["full_name"], customer["mobile"], customer["email"] or "-", customer["address"] or "-", customer["created_at"]] for customer in self.customer_records],
        )
        records_panel.content.addWidget(self.customer_table)
        self._select_first_row(self.customer_table)
        if self.current_role == "receptionist":
            layout.addWidget(records_panel)
        else:
            panels = QHBoxLayout()
            panel = SectionPanel("Customer Insights")
            customers_table = self._create_table(["Customer", "Orders", "Paid Orders", "Total Spent"])
            self._fill_table(customers_table, [[customer["customer_name"], customer["total_orders"], customer["paid_orders"], format_currency(customer["total_spent"])] for customer in self.customers])
            panel.content.addWidget(customers_table)
            panels.addWidget(records_panel, 3)
            panels.addWidget(panel, 2)
            layout.addLayout(panels)
        return page

    def _build_users_page(self):
        page, layout = self._create_page("Users", "Monitor staff accounts and how much business each team member is handling.")
        layout.addLayout(self._cards_row([
            ("Staff Accounts", str(len(self.users)), "#2b58a9"),
            ("Managers", str(sum(1 for user in self.users if user["role"] == "Manager")), "#7aaa1e"),
            ("Administrators", str(sum(1 for user in self.users if user["role"] == "Administrator")), "#d9881f"),
        ]))
        user_buttons = []
        if self.current_role == "administrator":
            user_buttons.append(("Add User", self.add_user, "primary"))
            user_buttons.append(("Edit User", self.edit_user, "secondary"))
        user_buttons.append(("Refresh", lambda: self.refresh_pages("Users"), "secondary"))
        layout.addLayout(self._create_button_row(user_buttons))
        panels = QHBoxLayout()
        user_panel = SectionPanel("User Directory")
        self.users_table = self._create_table(["ID", "Username", "Full Name", "Role", "Mobile", "DOB"])
        self.users_table.setColumnHidden(0, True)
        self._fill_table(self.users_table, [[user["id"], user["username"], user["full_name"], user["role"], user["mobile"], user["dob"]] for user in self.users])
        user_panel.content.addWidget(self.users_table)
        self._select_first_row(self.users_table)
        staff_panel = SectionPanel("Sales Per Staff")
        staff_table = self._create_table(["Staff", "Role", "Orders", "Sales", "Discount Given"])
        self._fill_table(staff_table, [[staff["full_name"], staff["role"], staff["total_orders"], format_currency(staff["total_sales"]), format_currency(staff["discount_given"])] for staff in self.staff_report])
        staff_panel.content.addWidget(staff_table)
        panels.addWidget(user_panel, 2)
        panels.addWidget(staff_panel, 3)
        layout.addLayout(panels)
        return page

    def _build_reports_page(self):
        page, layout = self._create_page("Reports", "Full sales reporting including offers, payments, top-selling items, and stock alerts.")
        layout.addLayout(self._cards_row([
            ("Net Sales", format_currency(self.metrics["total_sales"]), "#1e67c6"),
            ("Discount Value", format_currency(self.metrics["total_discount"]), "#7aaa1e"),
            ("Menu Items Sold", str(sum(int(item["total_quantity"]) for item in self.top_items)), "#d9881f"),
        ]))
        top = QHBoxLayout()
        offer_panel = SectionPanel("Offer Performance")
        offer_table = self._create_table(["Offer", "Orders", "Discount", "Net Sales"])
        self._fill_table(offer_table, [[offer["offer_name"], offer["total_orders"], format_currency(offer["total_discount"]), format_currency(offer["net_sales"])] for offer in self.offer_report])
        offer_panel.content.addWidget(offer_table)
        payment_panel = SectionPanel("Payments By Method")
        payment_table = self._create_table(["Method", "Transactions", "Amount Collected"])
        self._fill_table(payment_table, [[payment["method"], payment["total_payments"], format_currency(payment["amount_collected"])] for payment in self.payment_report])
        payment_panel.content.addWidget(payment_table)
        top.addWidget(offer_panel, 3)
        top.addWidget(payment_panel, 2)
        layout.addLayout(top)

        bottom = QHBoxLayout()
        top_items_panel = SectionPanel("Top Selling Items")
        top_items_table = self._create_table(["Item", "Quantity Sold", "Sales"])
        self._fill_table(top_items_table, [[item["item_name"], item["total_quantity"], format_currency(item["total_sales"])] for item in self.top_items])
        top_items_panel.content.addWidget(top_items_table)
        stock_panel = SectionPanel("Stock Report")
        stock_table = self._create_table(["Item", "Stock", "Reorder", "Status"])
        self._fill_table(stock_table, [[item["name"], item["stock_qty"], item["reorder_level"], item["stock_status"]] for item in self.stock_report])
        stock_panel.content.addWidget(stock_table)
        bottom.addWidget(top_items_panel, 3)
        bottom.addWidget(stock_panel, 2)
        layout.addLayout(bottom)
        return page

    def _build_settings_page(self):
        page, layout = self._create_page("Settings", "Current session and system configuration overview.")
        layout.addLayout(self._cards_row([
            ("Current User", self.current_user.get("username", "Unknown"), "#2b58a9"),
            ("Role", self.current_user.get("role", "Unknown"), "#7aaa1e"),
            ("Database", "SQLite Local", "#d9881f"),
        ]))
        panel = SectionPanel("Session Details")
        for text in [
            f"Logged in as: {self.current_user.get('full_name', 'Unknown User')}",
            f"Username: {self.current_user.get('username', 'Unknown')}",
            f"Role: {self.current_user.get('role', 'Unknown')}",
            f"Database file: {self.database.db_path}",
            f"Orders in system: {len(self.orders)}",
            f"Menu items in system: {len(self.menu_items)}",
            f"Offers configured: {len(self.offers)}",
        ]:
            label = QLabel(text)
            label.setWordWrap(True)
            label.setStyleSheet("color: #4d392d; font-size: 15px;")
            panel.content.addWidget(label)
        layout.addWidget(panel)
        return page

    def refresh_order_items_table(self):
        if not hasattr(self, "order_items_table"):
            return
        order_id = self._selected_id(self.orders_table) if hasattr(self, "orders_table") else None
        rows = self.database.get_order_items(order_id) if order_id else []
        if hasattr(self, "order_meta_label"):
            selected_order = next((order for order in self.active_orders if int(order["id"]) == int(order_id)), None) if order_id else None
            if selected_order:
                self.order_meta_label.setText(
                    f"{selected_order['order_number']} | {selected_order['customer_name']} | "
                    f"{selected_order['table_name']} | {selected_order['status']} | {selected_order['payment_status']} | "
                    f"{format_datetime(selected_order['created_at'])}"
                )
            else:
                self.order_meta_label.setText("Select an order to view item details.")
        self._fill_table(self.order_items_table, [[row["item_name"], row["quantity"], format_currency(row["unit_price"]), format_currency(row["line_total"])] for row in rows])

    def create_order(self):
        if not self._can("create_order"):
            QMessageBox.information(self, "Access", "You do not have permission to create orders.")
            return
        dialog = OrderDialog(
            self.menu_items,
            self.offers,
            self.users,
            self.customer_records,
            current_user=self.current_user,
            restrict_to_current_user=self.current_role == "receptionist",
            parent=self,
        )
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        try:
            self.database.create_order(**dialog.get_payload())
        except Exception as error:
            QMessageBox.warning(self, "Create Order", str(error))
            return
        self.refresh_pages("Orders")

    def update_selected_order_status(self, status):
        if not self._can("update_order_status"):
            QMessageBox.information(self, "Access", "You do not have permission to update order status.")
            return
        order_id = self._selected_id(self.orders_table)
        if order_id is None:
            QMessageBox.information(self, "Orders", "Select an order first.")
            return
        try:
            self.database.update_order_status(order_id, status)
        except Exception as error:
            QMessageBox.warning(self, "Orders", str(error))
            return
        self.refresh_pages("Orders")

    def add_menu_item(self):
        if not self._can("add_menu_item"):
            QMessageBox.information(self, "Access", "You do not have permission to add menu items.")
            return
        dialog = MenuItemDialog(parent=self)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        data = dialog.get_data()
        if not data["name"] or not data["category"]:
            QMessageBox.warning(self, "Menu", "Name and category are required.")
            return
        try:
            self.database.add_menu_item(**data)
        except Exception as error:
            QMessageBox.warning(self, "Menu", str(error))
            return
        self.refresh_pages("Menu Items")

    def add_user(self):
        if self.current_role != "administrator":
            QMessageBox.information(self, "Access", "You do not have permission to add users.")
            return
        dialog = UserDialog(parent=self)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        data = dialog.get_data()
        if not data["username"] or not data["full_name"] or not data["password"] or not data["role"] or not data["mobile"] or not data["dob"]:
            QMessageBox.warning(self, "User", "All fields are required.")
            return
        if data["role"] == "Administrator":
            QMessageBox.warning(self, "User", "Administrator accounts cannot be created from this screen.")
            return
        try:
            self.database.add_user(**data)
        except Exception as error:
            QMessageBox.warning(self, "User", str(error))
            return
        self.refresh_pages("Users")

    def edit_user(self):
        if self.current_role != "administrator":
            QMessageBox.information(self, "Access", "You do not have permission to edit users.")
            return
        user_id = self._selected_id(self.users_table)
        if user_id is None:
            QMessageBox.information(self, "User", "Select a user first.")
            return
        user = next((entry for entry in self.users if int(entry["id"]) == user_id), None)
        if not user:
            return
        if user["role"] == "Administrator":
            QMessageBox.information(self, "User", "Administrator accounts cannot be edited from this screen.")
            return
        dialog = UserDialog(user=user, parent=self)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        data = dialog.get_data()
        if not data["username"] or not data["full_name"] or not data["role"] or not data["mobile"] or not data["dob"]:
            QMessageBox.warning(self, "User", "Username, name, role, mobile, and date of birth are required.")
            return
        if data["role"] == "Administrator":
            QMessageBox.warning(self, "User", "Administrator accounts cannot be assigned from this screen.")
            return
        try:
            self.database.update_user(user_id, **data)
        except Exception as error:
            QMessageBox.warning(self, "User", str(error))
            return
        self.refresh_pages("Users")

    def edit_menu_item(self):
        if not self._can("edit_menu_item"):
            QMessageBox.information(self, "Access", "You do not have permission to edit menu items.")
            return
        item_id = self._selected_id(self.menu_table)
        if item_id is None:
            QMessageBox.information(self, "Menu", "Select a menu item first.")
            return
        item = next((item for item in self.menu_items if int(item["id"]) == item_id), None)
        if not item:
            return
        dialog = MenuItemDialog(item=item, parent=self)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        data = dialog.get_data()
        try:
            self.database.update_menu_item(item_id, data["name"], data["category"], data["price"], data["reorder_level"], data["is_stock_tracked"])
            self.database.update_menu_stock(item_id, data["stock_qty"])
        except Exception as error:
            QMessageBox.warning(self, "Menu", str(error))
            return
        self.refresh_pages("Menu Items")

    def update_menu_stock(self):
        if not self._can("update_menu_stock"):
            QMessageBox.information(self, "Access", "You do not have permission to update stock.")
            return
        item_id = self._selected_id(self.menu_table)
        if item_id is None:
            QMessageBox.information(self, "Stock", "Select a menu item first.")
            return
        item = next((menu_item for menu_item in self.menu_items if int(menu_item["id"]) == item_id), None)
        if item and int(item["is_stock_tracked"]) != 1:
            QMessageBox.information(self, "Stock", "This item is prepared fresh and does not use stock tracking.")
            return
        dialog = StockUpdateDialog(current_value=item["stock_qty"] if item else 0, parent=self)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        self.database.update_menu_stock(item_id, int(dialog.stock_input.value()))
        self.refresh_pages("Menu Items")

    def toggle_menu_item(self):
        if not self._can("toggle_menu_item"):
            QMessageBox.information(self, "Access", "You do not have permission to change item availability.")
            return
        item_id = self._selected_id(self.menu_table)
        if item_id is None:
            QMessageBox.information(self, "Menu", "Select a menu item first.")
            return
        self.database.toggle_menu_item(item_id)
        self.refresh_pages("Menu Items")

    def add_offer(self):
        if not self._can("add_offer"):
            QMessageBox.information(self, "Access", "You do not have permission to add offers.")
            return
        dialog = OfferDialog(parent=self)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        data = dialog.get_data()
        if not data["name"]:
            QMessageBox.warning(self, "Offers", "Offer name is required.")
            return
        try:
            self.database.add_offer(**data)
        except Exception as error:
            QMessageBox.warning(self, "Offers", str(error))
            return
        self.refresh_pages("Billing")

    def edit_offer(self):
        if not self._can("edit_offer"):
            QMessageBox.information(self, "Access", "You do not have permission to edit offers.")
            return
        offer_id = self._selected_id(self.offers_table)
        if offer_id is None:
            QMessageBox.information(self, "Offers", "Select an offer first.")
            return
        offer = next((offer for offer in self.offers if int(offer["id"]) == offer_id), None)
        if not offer:
            return
        dialog = OfferDialog(offer=offer, parent=self)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        data = dialog.get_data()
        try:
            self.database.update_offer(offer_id, data["name"], data["discount_type"], data["discount_value"], data["min_order_amount"])
        except Exception as error:
            QMessageBox.warning(self, "Offers", str(error))
            return
        self.refresh_pages("Billing")

    def toggle_offer(self):
        if not self._can("toggle_offer"):
            QMessageBox.information(self, "Access", "You do not have permission to change offers.")
            return
        offer_id = self._selected_id(self.offers_table)
        if offer_id is None:
            QMessageBox.information(self, "Offers", "Select an offer first.")
            return
        self.database.toggle_offer(offer_id)
        self.refresh_pages("Billing")

    def apply_offer_to_selected_order(self):
        if not self._can("apply_offer"):
            QMessageBox.information(self, "Access", "You do not have permission to apply offers.")
            return
        order_id = self._selected_id(self.billing_orders_table)
        if order_id is None:
            QMessageBox.information(self, "Billing", "Select an order first.")
            return
        offer_id = self._selected_id(self.offers_table)
        try:
            self.database.apply_offer_to_order(order_id, offer_id)
        except Exception as error:
            QMessageBox.warning(self, "Billing", str(error))
            return
        self.refresh_pages("Billing")

    def record_selected_payment(self, method):
        if not self._can("record_payment"):
            QMessageBox.information(self, "Access", "You do not have permission to record payments.")
            return
        order_id = self._selected_id(self.billing_orders_table)
        if order_id is None:
            QMessageBox.information(self, "Billing", "Select an order first.")
            return
        try:
            self.database.record_payment(order_id, method)
        except Exception as error:
            QMessageBox.warning(self, "Billing", str(error))
            return
        QMessageBox.information(self, "Billing", f"{method} payment recorded successfully.")
        self.show_bill_preview(order_id)
        self.refresh_pages("Billing")

    def show_bill_preview(self, order_id=None):
        selected_order_id = order_id if order_id is not None else self._selected_id(self.billing_orders_table)
        if selected_order_id is None:
            QMessageBox.information(self, "Billing", "Select an order first.")
            return
        invoice = self.database.get_order_invoice(selected_order_id)
        if not invoice:
            QMessageBox.warning(self, "Billing", "Bill details could not be loaded.")
            return
        dialog = BillPreviewDialog(invoice, parent=self)
        dialog.exec()

    def add_customer(self):
        if not self._can("add_customer"):
            QMessageBox.information(self, "Access", "You do not have permission to add customers.")
            return
        dialog = CustomerDialog(parent=self)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        data = dialog.get_data()
        if not data["full_name"] or not data["mobile"]:
            QMessageBox.warning(self, "Customers", "Customer name and mobile are required.")
            return
        try:
            self.database.add_customer(**data)
        except Exception as error:
            QMessageBox.warning(self, "Customers", str(error))
            return
        self.refresh_pages("Customers")

    def delete_customer(self):
        if self.current_role != "administrator":
            QMessageBox.information(self, "Access", "You do not have permission to delete customers.")
            return
        customer_id = self._selected_id(self.customer_table)
        if customer_id is None:
            QMessageBox.information(self, "Customers", "Select a customer first.")
            return
        customer = next((entry for entry in self.customer_records if int(entry["id"]) == customer_id), None)
        if not customer:
            return
        confirmation = QMessageBox.question(
            self,
            "Delete Customer",
            f"Delete customer '{customer['full_name']}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if confirmation != QMessageBox.StandardButton.Yes:
            return
        try:
            self.database.delete_customer(customer_id)
        except Exception as error:
            QMessageBox.warning(self, "Customers", str(error))
            return
        self.refresh_pages("Customers")

    def logout(self):
        self.login_window.reset_login_form()
        self.login_window.show()
        self.close()

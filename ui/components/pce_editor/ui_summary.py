from PyInstaller.lib.modulegraph.modulegraph import footer
from PyQt6.QtWidgets import QWidget, QLabel, QGridLayout, QVBoxLayout
from PyQt6.QtGui import QPixmap
from PyQt6.QtCore import Qt
from utils.path_finder import get_icon_path

icon_size = 45

class SummaryWidget(QWidget):
    """Displays summary information with icons, aligned using a grid layout."""

    def __init__(self, dropzone, parent=None):
        super().__init__(parent)
        self.parent_widget = parent
        self.dropzone = dropzone

        self.layout = QGridLayout(self)
        self.layout.setSpacing(5)  # ✅ More vertical space between rows
        self.layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        # **Create Summary Items**
        self.max_od_icon, self.max_od_label, self.max_od_value, self.max_od_metric = self.create_summary_item("Max OD",
                                                                                          "icon_od")
        self.total_length_icon, self.total_length_label, self.total_length_value, self.total_length_metric = self.create_summary_item(
            "Total Length", "icon_length")
        self.total_weight_icon, self.total_weight_label, self.total_weight_value, self.total_weight_metric = self.create_summary_item(
            "Total Weight", "icon_weight")

        # **Add Items to Grid Layout (Ensuring Alignment)**
        self.layout.addWidget(self.max_od_icon, 0, 0)
        self.max_od_icon.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.od_layout = QVBoxLayout()
        self.od_layout.setSpacing(0)
        self.od_layout.addWidget(self.max_od_label)
        self.od_layout.addWidget(self.max_od_value)
        self.od_layout.addWidget(self.max_od_metric)
        self.layout.addLayout(self.od_layout, 0, 1)

        self.layout.addWidget(QLabel(""), 1, 0)  # ✅ Empty row for spacing

        self.layout.addWidget(self.total_length_icon, 2, 0)
        self.total_length_icon.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.length_layout = QVBoxLayout()
        self.length_layout.setSpacing(0)
        self.length_layout.addWidget(self.total_length_label)
        self.length_layout.addWidget(self.total_length_value)
        self.length_layout.addWidget(self.total_length_metric)
        self.layout.addLayout(self.length_layout, 2, 1)

        self.layout.addWidget(QLabel(""), 3, 0)  # ✅ Empty row for spacing

        self.layout.addWidget(self.total_weight_icon, 4, 0)
        self.total_weight_icon.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.weight_layout = QVBoxLayout()
        self.weight_layout.setSpacing(0)
        self.weight_layout.addWidget(self.total_weight_label)
        self.weight_layout.addWidget(self.total_weight_value)
        self.weight_layout.addWidget(self.total_weight_metric)
        self.layout.addLayout(self.weight_layout, 4, 1)

        self.layout.setContentsMargins(0, 0, 0, 0)

        self.update_summary()

    def create_summary_item(self, label_text, icon_name):
        """Creates a structured layout for each summary item."""

        # **Load & Set Icon**
        icon_path = get_icon_path(icon_name)

        icon_label = QLabel()
        icon_label.setPixmap(
            QPixmap(icon_path).scaled(icon_size, icon_size, Qt.AspectRatioMode.KeepAspectRatio))  # ✅ Adjust icon size

        # **Labels**
        label = QLabel(label_text)
        label.setStyleSheet("font-size: 10px; font-weight: bold; ")  # ✅ Small label at the top

        value_label = QLabel("0.00")  # Default value
        value_label.setStyleSheet("font-size: 16px; font-weight: bold; ")  # ✅ Larger value below

        metric_label = QLabel("0.00")  # Default value
        metric_label.setStyleSheet("font-size: 12px; ")  # ✅ Larger value below

        return icon_label, label, value_label, metric_label

    def update_summary(self):
        """Updates summary values dynamically."""

        tool_widgets = self.dropzone.tool_widgets if self.dropzone else None

        max_od = 0.0
        total_length = 0.0
        total_weight = 0.0

        if tool_widgets is not None:
            for tool in tool_widgets:
                # od = float(tool.od_label.text().split()[0]) if tool.od_label.text() != "N/A" else 0.0
                length = float(tool.length_label.text().split()[0]) if tool.length_label.text() != "N/A" else 0.0
                weight = float(tool.weight_label.text().split()[0]) if tool.weight_label.text() != "N/A" else 0.0

                # max_od = max(max_od, od)
                total_length += length
                total_weight += weight

        self.max_od_value.setText(f"{max_od:.3f} in")
        self.max_od_metric.setText(f"({max_od*25.4:.1f} mm)")

        self.total_length_value.setText(f"{total_length:.1f} ft")
        self.total_length_metric.setText(f"({total_length*0.3048:.1f} m)")

        self.total_weight_value.setText(f"{total_weight:.1f} lbs")
        self.total_weight_metric.setText(f"({total_weight*0.453592:.1f} kg)")

def load_icon(label, file_name):
    """Loads an icon and applies color inversion while keeping transparency."""
    icon_path = get_icon_path(file_name)
    pixmap = QPixmap(icon_path)
    label.setPixmap(pixmap.scaled(icon_size, icon_size, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))

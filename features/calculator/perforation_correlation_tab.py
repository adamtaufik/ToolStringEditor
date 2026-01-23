from PyQt6.QtCore import Qt, QRectF, QSize
from PyQt6.QtGui import QPainter, QPen, QColor, QPixmap, QBrush, QFont, QClipboard
from PyQt6.QtWidgets import QMessageBox, QWidget, QVBoxLayout, QSplitter, QLineEdit, QLabel, QPushButton, QTextEdit, \
    QGraphicsView, QGraphicsScene, QGraphicsRectItem, QGraphicsPixmapItem, QGraphicsSimpleTextItem, QHBoxLayout, \
    QGridLayout, QGroupBox, QApplication


class ToolStringCanvas(QGraphicsView):
    def __init__(self):
        super().__init__()

        self.scene = QGraphicsScene(self)
        self.setScene(self.scene)
        self.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.setMinimumSize(250, 350)
        self.setStyleSheet("background-color: #f8f9fa; border: 1px solid #ccc;")

        # State
        self.grccl_hpt_length = 0.0
        self.stacked_gun_length = 0.0
        self.max_tool_length = 0.0

        # Toolstring images
        self.grccl_pixmap = self.create_toolstring_pixmap(QColor(70, 130, 180), "GR/CCL+HPT")
        self.perf_pixmap = self.create_toolstring_pixmap(QColor(178, 34, 34), "PERF")

    def create_toolstring_pixmap(self, color, label):
        """Create a placeholder pixmap for toolstring"""
        pixmap = QPixmap(80, 400)
        pixmap.fill(Qt.GlobalColor.transparent)

        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Draw toolstring body
        painter.setPen(QPen(color.darker(), 2))
        painter.setBrush(QBrush(color.lighter(130)))
        painter.drawRoundedRect(10, 10, 60, 380, 5, 5)

        # Draw toolstring segments
        painter.setPen(QPen(color.darker(), 1))
        for i in range(0, 380, 20):
            painter.drawLine(15, 10 + i, 65, 10 + i)

        # Draw label
        painter.setPen(QPen(Qt.GlobalColor.black, 1))
        font = QFont("Arial", 9)
        painter.setFont(font)
        painter.rotate(-90)
        painter.drawText(-350, 45, label)
        painter.rotate(90)

        painter.end()
        return pixmap

    def update_view(self, corrected_flag, bottom_shot, target_depth, grccl_hpt_length, stacked_gun_length):
        self.grccl_hpt_length = grccl_hpt_length
        self.stacked_gun_length = stacked_gun_length
        self.max_tool_length = max(grccl_hpt_length, stacked_gun_length, 1.0)
        self.draw()

    def draw(self):
        self.scene.clear()

        view_h = self.viewport().height()
        view_w = self.viewport().width()

        # Add canvas title
        title = self.scene.addText("Tool Strings Comparison")
        title.setDefaultTextColor(QColor(33, 37, 41))
        font = QFont("Arial", 10, QFont.Weight.Bold)
        title.setFont(font)
        title.setPos(view_w / 2 - 70, 10)

        # Calculate Y-axis scaling based on maximum tool length
        available_height = view_h - 100
        top_margin = 60

        # Scale factor: available_height / max_tool_length
        scale = available_height / self.max_tool_length if self.max_tool_length > 0 else 1.0

        # Calculate positions for side-by-side display
        left_column_x = view_w * 0.3
        right_column_x = view_w * 0.7

        # Draw Y-axis and scale markers
        self.draw_y_axis_scale(view_w, top_margin, available_height, scale)

        # Draw baseline at the top
        baseline_y = top_margin

        # GR/CCL+HPT Tool String
        if self.grccl_hpt_length > 0:
            grccl_height = self.grccl_hpt_length * scale
            grccl_bottom_y = baseline_y + grccl_height

            # Scale pixmap to fit the toolstring height
            if grccl_height > 0:
                pixmap_scale = grccl_height / self.grccl_pixmap.height()
                scaled_width = self.grccl_pixmap.width() * pixmap_scale

                # Draw toolstring image
                grccl_item = QGraphicsPixmapItem(self.grccl_pixmap)
                grccl_item.setScale(pixmap_scale)
                grccl_item.setPos(left_column_x - scaled_width / 2, baseline_y)
                self.scene.addItem(grccl_item)

                # Draw bounding box
                self.scene.addRect(left_column_x - scaled_width / 2, baseline_y,
                                   scaled_width, grccl_height,
                                   QPen(QColor(70, 130, 180), 1),
                                   QBrush(Qt.GlobalColor.transparent))

            # Draw length indicator line
            self.draw_length_indicator(
                left_column_x, baseline_y, grccl_bottom_y,
                f"{self.grccl_hpt_length:.2f} m",
                QColor(70, 130, 180),
                "left"
            )

            # Draw annotation
            self.draw_toolstring_annotation(
                "GR/CCL+HPT",
                f"Length: {self.grccl_hpt_length:.2f} m",
                QColor(70, 130, 180),
                left_column_x - 50, grccl_bottom_y + 10,
                100
            )

        # Perforation Run Tool String
        if self.stacked_gun_length > 0:
            perf_height = self.stacked_gun_length * scale
            perf_bottom_y = baseline_y + perf_height

            # Scale pixmap to fit the toolstring height
            if perf_height > 0:
                pixmap_scale = perf_height / self.perf_pixmap.height()
                scaled_width = self.perf_pixmap.width() * pixmap_scale

                # Draw toolstring image
                perf_item = QGraphicsPixmapItem(self.perf_pixmap)
                perf_item.setScale(pixmap_scale)
                perf_item.setPos(right_column_x - scaled_width / 2, baseline_y)
                self.scene.addItem(perf_item)

                # Draw bounding box
                self.scene.addRect(right_column_x - scaled_width / 2, baseline_y,
                                   scaled_width, perf_height,
                                   QPen(QColor(178, 34, 34), 1),
                                   QBrush(Qt.GlobalColor.transparent))

            # Draw length indicator line
            self.draw_length_indicator(
                right_column_x, baseline_y, perf_bottom_y,
                f"{self.stacked_gun_length:.2f} m",
                QColor(178, 34, 34),
                "right"
            )

            # Draw annotation
            self.draw_toolstring_annotation(
                "Perforation Run",
                f"Length: {self.stacked_gun_length:.2f} m",
                QColor(178, 34, 34),
                right_column_x - 50, perf_bottom_y + 10,
                100
            )

        # Draw horizontal line at the top (baseline)
        self.scene.addLine(20, baseline_y, view_w - 20, baseline_y,
                           QPen(Qt.GlobalColor.darkGray, 1, Qt.PenStyle.SolidLine))

        # Add baseline label
        baseline_label = self.scene.addText("Top of Tool Strings")
        baseline_label.setDefaultTextColor(Qt.GlobalColor.darkGray)
        baseline_label.setFont(QFont("Arial", 8))
        baseline_label.setPos(10, baseline_y - 15)

        # Draw comparison line if both tool strings are present
        if self.grccl_hpt_length > 0 and self.stacked_gun_length > 0:
            left_bottom = baseline_y + (self.grccl_hpt_length * scale)
            right_bottom = baseline_y + (self.stacked_gun_length * scale)

            # Draw horizontal line at the bottom of the shorter toolstring
            shorter_bottom = min(left_bottom, right_bottom)
            self.scene.addLine(left_column_x - 30, shorter_bottom,
                               right_column_x + 30, shorter_bottom,
                               QPen(Qt.GlobalColor.darkGray, 1, Qt.PenStyle.DotLine))

            # Calculate and display length difference
            length_diff = abs(self.grccl_hpt_length - self.stacked_gun_length)
            if length_diff > 0.01:
                diff_y = shorter_bottom + 20
                diff_label = self.scene.addText(f"Δ Length = {length_diff:.2f} m")
                diff_label.setDefaultTextColor(Qt.GlobalColor.darkBlue)
                diff_label.setFont(QFont("Arial", 9, QFont.Weight.Bold))
                diff_label.setPos(view_w / 2 - 50, diff_y)

    def draw_length_indicator(self, x, top_y, bottom_y, text, color, side="left"):
        """Draw a vertical line with measurement text"""
        # Draw vertical line
        self.scene.addLine(x, top_y, x, bottom_y,
                           QPen(color, 2))

        # Draw measurement text
        mid_y = (top_y + bottom_y) / 2
        length_text = self.scene.addText(text)
        length_text.setDefaultTextColor(color)
        length_text.setFont(QFont("Arial", 9, QFont.Weight.Bold))

        # Position text to the specified side
        if side == "left":
            length_text.setPos(x - 70, mid_y - 10)
        else:
            length_text.setPos(x + 10, mid_y - 10)

    def draw_toolstring_annotation(self, title, length_text, color, x, y, width):
        """Draw annotation box for toolstring"""
        # Create title
        title_item = self.scene.addText(title)
        title_item.setDefaultTextColor(color)
        title_item.setFont(QFont("Arial", 9, QFont.Weight.Bold))
        title_item.setTextWidth(width)
        title_item.setPos(x, y)

        # Create length text
        length_item = self.scene.addText(length_text)
        length_item.setDefaultTextColor(color.darker())
        length_item.setFont(QFont("Arial", 8))
        length_item.setPos(x + 10, y + 20)

    def draw_y_axis_scale(self, view_w, top_y, available_height, scale):
        """Draw Y-axis scale markers on the left side"""
        # Draw Y-axis line
        axis_x = 20
        self.scene.addLine(axis_x, top_y, axis_x, top_y + available_height,
                           QPen(Qt.GlobalColor.darkGray, 1))

        # Draw Y-axis label
        y_label = self.scene.addText("Length (m)")
        y_label.setDefaultTextColor(Qt.GlobalColor.darkGray)
        y_label.setFont(QFont("Arial", 8, QFont.Weight.Bold))
        y_label.setPos(axis_x - 15, top_y - 25)

        # Calculate tick marks
        max_display_length = self.max_tool_length
        num_ticks = 5
        tick_interval = max_display_length / num_ticks

        for i in range(num_ticks + 1):
            length_value = i * tick_interval
            y_pos = top_y + (length_value * scale)

            # Draw tick mark
            self.scene.addLine(axis_x - 5, y_pos, axis_x + 5, y_pos,
                               QPen(Qt.GlobalColor.darkGray, 1))

            # Draw tick label
            tick_label = self.scene.addText(f"{length_value:.1f}")
            tick_label.setDefaultTextColor(Qt.GlobalColor.darkGray)
            tick_label.setFont(QFont("Arial", 7))
            tick_label.setPos(axis_x - 25, y_pos - 7)

            # Draw horizontal grid line
            if i > 0 and i < num_ticks:
                self.scene.addLine(axis_x + 10, y_pos, view_w - 20, y_pos,
                                   QPen(QColor(230, 230, 230), 0.5))

    def resizeEvent(self, event):
        self.draw()
        super().resizeEvent(event)


class WellCanvas(QGraphicsView):
    def __init__(self):
        super().__init__()

        self.scene = QGraphicsScene(self)
        self.setScene(self.scene)
        self.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.setMinimumSize(300, 400)
        self.setStyleSheet("background-color: white; border: 1px solid #ccc;")

        # State
        self.corrected_flag = 0.0
        self.bottom_shot = 0.0
        self.target_depth = 0.0
        self.max_depth = 1500.0

    def update_view(self, corrected_flag, bottom_shot, target_depth):
        self.corrected_flag = corrected_flag
        self.bottom_shot = bottom_shot
        self.target_depth = target_depth

        self.max_depth = max(
            target_depth,
            bottom_shot,
            corrected_flag
        ) * 1.25

        self.draw()

    def draw(self):
        self.scene.clear()

        view_h = self.viewport().height()
        scale = view_h / self.max_depth

        well_x = 100
        well_w = 50

        # # Add canvas title
        # title = self.scene.addText("Wellbore View")
        # title.setDefaultTextColor(QColor(33, 37, 41))
        # font = QFont("Arial", 10, QFont.Weight.Bold)
        # title.setFont(font)
        # title.setPos(well_x - 30, 10)

        # --- Well Casing ---
        casing = QGraphicsRectItem(
            well_x, 0,
            well_w, self.max_depth * scale
        )
        casing.setPen(QPen(Qt.GlobalColor.darkGray, 2))
        casing.setBrush(QColor(245, 245, 245))
        self.scene.addItem(casing)

        # Add casing label
        casing_label = self.scene.addText("Casing")
        casing_label.setDefaultTextColor(Qt.GlobalColor.darkGray)
        casing_label.setFont(QFont("Arial", 9))
        casing_label.setPos(well_x + well_w / 2 - 20, -25)

        # --- Corrected Flag --- (MOVED TO LEFT SIDE)
        cf_y = self.corrected_flag * scale
        self.scene.addLine(
            well_x - 15, cf_y,
            well_x + well_w + 15, cf_y,
            QPen(QColor(0, 102, 204), 2)
        )
        # Draw corrected flag label on the LEFT side
        cf_text = self.scene.addText(
            f"Corrected Flag\n{self.corrected_flag:.2f} m"
        )
        cf_text.setDefaultTextColor(QColor(0, 102, 204))
        # Position to the left with negative X offset
        cf_text.setPos(well_x - 180, cf_y - 18)

        # Draw connection point for GR/CCL+HPT
        self.scene.addEllipse(well_x - 10, cf_y - 3, 6, 6,
                              QPen(QColor(70, 130, 180), 1),
                              QBrush(QColor(70, 130, 180)))

        # --- Gun Stack (in well) ---
        gun_height = (self.bottom_shot - self.corrected_flag) * scale
        if gun_height > 0:
            gun = QGraphicsRectItem(
                well_x + 8,
                cf_y,
                well_w - 16,
                gun_height
            )
            gun.setPen(QPen(QColor(120, 0, 0), 1))
            gun.setBrush(QColor(180, 50, 50, 180))
            self.scene.addItem(gun)

            # Add gun label
            gun_label = self.scene.addText("Gun String")
            gun_label.setDefaultTextColor(QColor(178, 34, 34))
            gun_label.setFont(QFont("Arial", 9))
            gun_label.setPos(well_x + well_w / 2 - 25, cf_y + gun_height / 2 - 10)

        # --- Bottom Shot --- (remains on right side)
        bs_y = self.bottom_shot * scale
        self.scene.addLine(
            well_x - 15, bs_y,
            well_x + well_w + 15, bs_y,
            QPen(QColor(180, 0, 0), 2)
        )
        bs_text = self.scene.addText(
            f"Bottom Shot\n{self.bottom_shot:.2f} m"
        )
        bs_text.setDefaultTextColor(QColor(180, 0, 0))
        bs_text.setPos(well_x + well_w + 20, bs_y - 18)

        # Draw connection point for Perf Run bottom
        self.scene.addEllipse(well_x - 10, bs_y - 3, 6, 6,
                              QPen(QColor(178, 34, 34), 1),
                              QBrush(QColor(178, 34, 34)))

        # --- Target Depth --- (remains on right side)
        td_y = self.target_depth * scale
        self.scene.addLine(
            well_x - 20, td_y,
            well_x + well_w + 20, td_y,
            QPen(QColor(0, 150, 0), 2, Qt.PenStyle.DashLine)
        )
        td_text = self.scene.addText(
            f"Target Depth\n{self.target_depth:.2f} m"
        )
        td_text.setDefaultTextColor(QColor(0, 150, 0))
        td_text.setPos(well_x + well_w + 20, td_y - 18)

        # --- Wire Movement Arrow ---
        movement = self.target_depth - self.bottom_shot
        if abs(movement) > 0.01:
            direction = 1 if movement > 0 else -1
            arrow_y1 = bs_y
            arrow_y2 = bs_y + (direction * 40)

            # Draw arrow line
            self.scene.addLine(
                well_x - 40, arrow_y1,
                well_x - 40, arrow_y2,
                QPen(Qt.GlobalColor.black, 2)
            )

            # Arrow head
            if direction > 0:
                # Down arrow
                self.scene.addLine(well_x - 40, arrow_y2, well_x - 45, arrow_y2 - 10, QPen(Qt.GlobalColor.black, 2))
                self.scene.addLine(well_x - 40, arrow_y2, well_x - 35, arrow_y2 - 10, QPen(Qt.GlobalColor.black, 2))
                arrow_label = "Move Down"
            else:
                # Up arrow
                self.scene.addLine(well_x - 40, arrow_y2, well_x - 45, arrow_y2 + 10, QPen(Qt.GlobalColor.black, 2))
                self.scene.addLine(well_x - 40, arrow_y2, well_x - 35, arrow_y2 + 10, QPen(Qt.GlobalColor.black, 2))
                arrow_label = "Move Up"

            arrow_text = self.scene.addText(
                f"{arrow_label}\n{abs(movement):.2f} m"
            )
            arrow_text.setDefaultTextColor(Qt.GlobalColor.darkBlue)
            arrow_text.setPos(well_x - 110, min(arrow_y1, arrow_y2) - 10)

        # --- Depth Markers ---
        step = max(50, round(self.max_depth / 5, -1))
        for d in range(0, int(self.max_depth) + 1, int(step)):
            y = d * scale
            self.scene.addLine(
                well_x + well_w, y,
                well_x + well_w + 8, y,
                QPen(Qt.GlobalColor.gray, 1)
            )
            t = self.scene.addText(f"{d:.0f} m")
            t.setDefaultTextColor(Qt.GlobalColor.darkGray)
            t.setFont(QFont("Arial", 8))
            t.setPos(well_x + well_w + 12, y - 8)

    def resizeEvent(self, event):
        self.draw()
        super().resizeEvent(event)


class PerforationOffsetTab(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()
        self.setup_connections()

        # Store current calculation data for copying
        self.current_calculation_data = ""

    def init_ui(self):
        # Main horizontal layout with three columns
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)

        # Create three main sections
        left_widget = self.create_left_section()
        middle_widget = self.create_middle_section()
        right_widget = self.create_right_section()

        # Add stretch factors to make middle section larger
        main_layout.addWidget(left_widget, 2)  # 2 parts
        main_layout.addWidget(middle_widget, 3)  # 3 parts (larger)
        main_layout.addWidget(right_widget, 2)  # 2 parts

    def create_left_section(self):
        """Create the left section with inputs and toolstring illustrations"""
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setSpacing(10)

        # Input section with a group box
        input_group = QGroupBox("Input Parameters")
        input_layout = QVBoxLayout(input_group)

        # Create a grid for better alignment
        grid_layout = QGridLayout()
        grid_layout.setSpacing(10)

        # Row 0: Target Depth
        grid_layout.addWidget(QLabel("Target Depth (m RKB)"), 0, 0)
        self.target_depth = QLineEdit()
        self.target_depth.setPlaceholderText("e.g., 1500.0")
        grid_layout.addWidget(self.target_depth, 0, 1)

        # Row 1: Uncorrected Flag Depth
        grid_layout.addWidget(QLabel("Uncorrected Flag Depth (m RKB)"), 1, 0)
        self.uncorrected_flag = QLineEdit()
        self.uncorrected_flag.setPlaceholderText("e.g., 1495.0")
        grid_layout.addWidget(self.uncorrected_flag, 1, 1)

        # Row 2: Log Offset
        grid_layout.addWidget(QLabel("Log Offset (+/- m)"), 2, 0)
        self.log_offset = QLineEdit()
        self.log_offset.setPlaceholderText("e.g., -2.5")
        grid_layout.addWidget(self.log_offset, 2, 1)

        # Row 3: GR/CCL+HPT Length
        grid_layout.addWidget(QLabel("GR/CCL+HPT Length (m)"), 3, 0)
        self.grccl_hpt_length = QLineEdit()
        self.grccl_hpt_length.setPlaceholderText("e.g., 15.0")
        grid_layout.addWidget(self.grccl_hpt_length, 3, 1)

        # Row 4: Stacked Gun Length
        grid_layout.addWidget(QLabel("Perf. Run Length (m)"), 4, 0)
        self.stacked_gun_length = QLineEdit()
        self.stacked_gun_length.setPlaceholderText("e.g., 12.0")
        grid_layout.addWidget(self.stacked_gun_length, 4, 1)

        input_layout.addLayout(grid_layout)

        # Calculate button
        self.calculate_btn = QPushButton("Calculate Wire Movement")
        self.calculate_btn.setStyleSheet("""
            QPushButton {
                background-color: #4a6fa5;
                color: white;
                font-weight: bold;
                padding: 8px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #5a7fb5;
            }
        """)
        input_layout.addWidget(self.calculate_btn)

        # Result label
        self.result_label = QLabel("Wire Movement: —")
        self.result_label.setStyleSheet("""
            QLabel {
                font-size: 14px;
                font-weight: bold;
                color: #2c3e50;
                padding: 5px;
                background-color: #ecf0f1;
                border-radius: 4px;
            }
        """)
        self.result_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        input_layout.addWidget(self.result_label)

        left_layout.addWidget(input_group)

        # Toolstring illustrations
        self.toolstring_canvas = ToolStringCanvas()
        left_layout.addWidget(self.toolstring_canvas)

        return left_widget

    def create_middle_section(self):
        """Create the middle section with well illustration"""
        middle_widget = QWidget()
        middle_layout = QVBoxLayout(middle_widget)

        # Well illustration with a title
        title_label = QLabel("Wellbore Schematic")
        title_label.setStyleSheet("""
            QLabel {
                font-size: 14px;
                font-weight: bold;
                color: #2c3e50;
                padding: 5px;
                background-color: #ecf0f1;
                border-radius: 4px;
            }
        """)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        middle_layout.addWidget(title_label)

        self.well_canvas = WellCanvas()
        middle_layout.addWidget(self.well_canvas)

        # Add some explanatory text
        explanation = QLabel(
            "Illustration shows:\n"
            "• Corrected Flag (left side, blue)\n"
            "• Bottom Shot (right side, red)\n"
            "• Target Depth (right side, green)\n"
            "• Wire movement direction (arrow)"
        )
        explanation.setStyleSheet("""
            QLabel {
                font-size: 11px;
                color: #666;
                padding: 5px;
                background-color: #f8f9fa;
                border: 1px solid #ddd;
                border-radius: 4px;
            }
        """)
        explanation.setWordWrap(True)
        middle_layout.addWidget(explanation)

        return middle_widget

    def create_right_section(self):
        """Create the right section with formulas"""
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setSpacing(10)

        # Title with copy button in a horizontal layout
        header_widget = QWidget()
        header_layout = QHBoxLayout(header_widget)
        header_layout.setContentsMargins(0, 0, 0, 0)

        title_label = QLabel("Calculation Breakdown")
        title_label.setStyleSheet("""
            QLabel {
                font-size: 14px;
                font-weight: bold;
                color: #2c3e50;
                padding: 5px;
            }
        """)

        # Copy button
        self.copy_button = QPushButton("📋 Copy")
        self.copy_button.setToolTip("Copy calculation details to clipboard")
        self.copy_button.setStyleSheet("""
            QPushButton {
                background-color: #5cb85c;
                color: white;
                font-weight: bold;
                padding: 5px 10px;
                border-radius: 4px;
                border: none;
            }
            QPushButton:hover {
                background-color: #4cae4c;
            }
            QPushButton:disabled {
                background-color: #cccccc;
                color: #666666;
            }
        """)
        self.copy_button.setEnabled(False)  # Disabled until calculation is done

        header_layout.addWidget(title_label)
        header_layout.addStretch()
        header_layout.addWidget(self.copy_button)

        right_layout.addWidget(header_widget)

        # Formula display
        self.formula_display = QTextEdit()
        self.formula_display.setReadOnly(True)
        self.formula_display.setMinimumHeight(350)
        self.formula_display.setStyleSheet("""
            QTextEdit {
                background-color: #f8f9fa;
                border: 1px solid #ccc;
                border-radius: 4px;
                padding: 10px;
                font-family: 'Segoe UI', Arial, sans-serif;
            }
        """)

        # Add example/instructions
        instructions = QLabel(
            "Enter values in the left panel and click 'Calculate' "
            "to see detailed calculations here. Use the Copy button to save results."
        )
        instructions.setStyleSheet("""
            QLabel {
                font-size: 12px;
                color: #666;
                padding: 10px;
                background-color: #e8f4f8;
                border: 1px solid #b8e2f0;
                border-radius: 4px;
                margin-top: 5px;
            }
        """)
        instructions.setWordWrap(True)

        right_layout.addWidget(self.formula_display)
        right_layout.addWidget(instructions)

        return right_widget

    def setup_connections(self):
        self.calculate_btn.clicked.connect(self.calculate)
        self.copy_button.clicked.connect(self.copy_calculation_to_clipboard)

    def calculate(self):
        try:
            target = float(self.target_depth.text())
            ufd = float(self.uncorrected_flag.text())
            offset = float(self.log_offset.text())
            grccl_length = float(self.grccl_hpt_length.text())
            stacked_length = float(self.stacked_gun_length.text())

            corrected_flag = ufd + offset
            rs_corrected_flag = corrected_flag - grccl_length
            bottom_shot = rs_corrected_flag + stacked_length
            movement = target - bottom_shot

            if abs(movement) < 0.01:
                direction = "On Depth"
                color = "#27ae60"
            elif movement > 0:
                direction = "Down"
                color = "#e74c3c"
            else:
                direction = "Up"
                color = "#3498db"

            self.result_label.setText(
                f"Wire Movement: {abs(movement):.2f} m ({direction})"
            )
            self.result_label.setStyleSheet(f"""
                QLabel {{
                    font-size: 14px;
                    font-weight: bold;
                    color: white;
                    padding: 8px;
                    background-color: {color};
                    border-radius: 4px;
                }}
            """)

            # Generate formula HTML
            html_content = self.generate_formula(
                target, ufd, offset,
                grccl_length, stacked_length,
                corrected_flag,
                rs_corrected_flag,
                bottom_shot,
                movement
            )
            self.formula_display.setHtml(html_content)

            # Generate plain text for copying
            self.generate_plain_text_for_copying(
                target, ufd, offset,
                grccl_length, stacked_length,
                corrected_flag,
                rs_corrected_flag,
                bottom_shot,
                movement,
                direction
            )

            # Enable copy button
            self.copy_button.setEnabled(True)

            # Update illustrations
            self.toolstring_canvas.update_view(
                corrected_flag,
                bottom_shot,
                target,
                grccl_length,
                stacked_length
            )

            self.well_canvas.update_view(
                corrected_flag,
                bottom_shot,
                target
            )

        except ValueError:
            QMessageBox.warning(
                self,
                "Input Error",
                "Please enter valid numeric values in all fields."
            )
            self.result_label.setText("Wire Movement: —")
            self.result_label.setStyleSheet("""
                QLabel {
                    font-size: 14px;
                    font-weight: bold;
                    color: #2c3e50;
                    padding: 5px;
                    background-color: #ecf0f1;
                    border-radius: 4px;
                }
            """)
            self.copy_button.setEnabled(False)

    def generate_formula(self, target, ufd, offset, grccl_length, stacked_length, corrected_flag, rs_corrected_flag,
                         bottom_shot, movement):
        if abs(movement) < 0.01:
            direction_display = "On Depth"
            movement_display = "0.00"
            result_color = "#27ae60"
        elif movement > 0:
            direction_display = "Down"
            movement_display = f"{movement:.2f}"
            result_color = "#e74c3c"
        else:
            direction_display = "Up"
            movement_display = f"{abs(movement):.2f}"
            result_color = "#3498db"

        return f"""
            <style>
                .formula {{ 
                    font-family: 'Cambria Math', 'Times New Roman', serif;
                    font-size: 12pt;
                    margin: 8px 0;
                    padding: 5px;
                    border-left: 3px solid #3498db;
                    background-color: #f8f9fa;
                }}
                .result {{
                    font-weight: bold;
                    color: #2c3e50;
                    margin: 12px 0 6px 0;
                    padding-bottom: 4px;
                    border-bottom: 2px solid #7f8c8d;
                }}
                .variable {{
                    color: #2980b9;
                    font-weight: 600;
                }}
                .value {{
                    color: #27ae60;
                    font-weight: 600;
                }}
                .highlight {{
                    background-color: #fffacd;
                    padding: 2px 4px;
                    border-radius: 3px;
                }}
                .final-result {{
                    font-size: 14pt;
                    font-weight: bold;
                    color: {result_color};
                    margin: 15px 0;
                    padding: 10px;
                    background-color: #f0f8ff;
                    border: 2px solid {result_color};
                    border-radius: 5px;
                    text-align: center;
                }}
            </style>

            <div class="result">Input Parameters</div>
            <div class="formula">Target Depth (<span class="variable">T</span>) = <span class="value">{target:.2f}</span> m RKB</div>
            <div class="formula">Uncorrected Flag Depth (<span class="variable">UFD</span>) = <span class="value">{ufd:.2f}</span> m RKB</div>
            <div class="formula">Log Offset (<span class="variable">O</span>) = <span class="value">{offset:+.2f}</span> m</div>
            <div class="formula">GR/CCL+HPT Length (<span class="variable">L<sub>GR</sub></span>) = <span class="value">{grccl_length:.2f}</span> m</div>
            <div class="formula">Stacked Gun Length (<span class="variable">L<sub>Gun</sub></span>) = <span class="value">{stacked_length:.2f}</span> m</div>

            <div class="result">Step 1: Calculate Corrected Flag Depth</div>
            <div class="formula"><span class="variable">CFD</span> = <span class="variable">UFD</span> + <span class="variable">O</span></div>
            <div class="formula"><span class="variable">CFD</span> = {ufd:.2f} + ({offset:+.2f})</div>
            <div class="formula"><span class="variable">CFD</span> = <span class="value">{corrected_flag:.2f}</span> m RKB</div>

            <div class="result">Step 2: Calculate Rope Socket Depth</div>
            <div class="formula"><span class="variable">RS Depth</span> = <span class="variable">CFD</span> - <span class="variable">L<sub>GR</sub></span></div>
            <div class="formula"><span class="variable">RS Depth</span> = {corrected_flag:.2f} - {grccl_length:.2f}</div>
            <div class="formula"><span class="variable">RS Depth</span> = <span class="value">{rs_corrected_flag:.2f}</span> m RKB</div>

            <div class="result">Step 3: Calculate Bottom Shot Depth</div>
            <div class="formula"><span class="variable">BSD</span> = <span class="variable">RS Depth</span> + <span class="variable">L<sub>Gun</sub></span></div>
            <div class="formula"><span class="variable">BSD</span> = {rs_corrected_flag:.2f} + {stacked_length:.2f}</div>
            <div class="formula"><span class="variable">BSD</span> = <span class="value">{bottom_shot:.2f}</span> m RKB</div>

            <div class="result">Step 4: Calculate Required Wire Movement</div>
            <div class="formula"><span class="variable">WM</span> = <span class="variable">T</span> - <span class="variable">BSD</span></div>
            <div class="formula"><span class="variable">WM</span> = {target:.2f} - {bottom_shot:.2f}</div>
            <div class="formula"><span class="variable">WM</span> = <span class="value">{movement:+.2f}</span> m</div>

            <div class="final-result">Required Wire Movement: {movement_display} m ({direction_display})</div>

            <div class="result">Summary</div>
            <div class="formula">• Current bottom shot: <span class="value">{bottom_shot:.2f}</span> m RKB</div>
            <div class="formula">• Target depth: <span class="value">{target:.2f}</span> m RKB</div>
            <div class="formula">• Gun string length: <span class="value">{stacked_length:.2f}</span> m</div>
            <div class="formula">• GR/CCL+HPT length: <span class="value">{grccl_length:.2f}</span> m</div>

            {"<div class='final-result' style='background-color: #d4edda; border-color: #c3e6cb; color: #155724;'>✓ Perfect! Gun is already on target depth</div>" if abs(movement) < 0.01 else ""}
        """

    def generate_plain_text_for_copying(self, target, ufd, offset, grccl_length, stacked_length, corrected_flag,
                                        rs_corrected_flag, bottom_shot, movement, direction):
        """Generate plain text version of calculation for clipboard"""
        import datetime

        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        self.current_calculation_data = f"""PERFORATION OFFSET CALCULATION
================================
Calculation Time: {timestamp}

INPUT PARAMETERS:
-----------------
Target Depth (T): {target:.2f} m RKB
Uncorrected Flag Depth (UFD): {ufd:.2f} m RKB
Log Offset (O): {offset:+.2f} m
GR/CCL+HPT Length (L_GR): {grccl_length:.2f} m
Stacked Gun Length (L_Gun): {stacked_length:.2f} m

CALCULATION STEPS:
------------------
1. Corrected Flag Depth (CFD)
   CFD = UFD + O
   CFD = {ufd:.2f} + ({offset:+.2f})
   CFD = {corrected_flag:.2f} m RKB

2. Rope Socket Depth
   RS Depth = CFD - L_GR
   RS Depth = {corrected_flag:.2f} - {grccl_length:.2f}
   RS Depth = {rs_corrected_flag:.2f} m RKB

3. Bottom Shot Depth (BSD)
   BSD = RS Depth + L_Gun
   BSD = {rs_corrected_flag:.2f} + {stacked_length:.2f}
   BSD = {bottom_shot:.2f} m RKB

4. Wire Movement Required (WM)
   WM = T - BSD
   WM = {target:.2f} - {bottom_shot:.2f}
   WM = {movement:+.2f} m

RESULTS:
--------
Required Wire Movement: {abs(movement):.2f} m ({direction})

SUMMARY:
--------
• Current bottom shot: {bottom_shot:.2f} m RKB
• Target depth: {target:.2f} m RKB
• Gun string length: {stacked_length:.2f} m
• GR/CCL+HPT length: {grccl_length:.2f} m

{"• STATUS: Gun is already on target depth - no movement required" if abs(movement) < 0.01 else ""}
================================
"""

    def copy_calculation_to_clipboard(self):
        """Copy the calculation details to clipboard"""
        if self.current_calculation_data:
            clipboard = QApplication.clipboard()
            clipboard.setText(self.current_calculation_data)

            # Show a temporary confirmation
            original_text = self.copy_button.text()
            self.copy_button.setText("✓ Copied!")
            self.copy_button.setStyleSheet("""
                QPushButton {
                    background-color: #5cb85c;
                    color: white;
                    font-weight: bold;
                    padding: 5px 10px;
                    border-radius: 4px;
                    border: none;
                }
            """)

            # Reset button text after 2 seconds
            from PyQt6.QtCore import QTimer
            QTimer.singleShot(2000, lambda: self.copy_button.setText("📋 Copy"))
            QTimer.singleShot(2000, lambda: self.copy_button.setStyleSheet("""
                QPushButton {
                    background-color: #5cb85c;
                    color: white;
                    font-weight: bold;
                    padding: 5px 10px;
                    border-radius: 4px;
                    border: none;
                }
                QPushButton:hover {
                    background-color: #4cae4c;
                }
            """))
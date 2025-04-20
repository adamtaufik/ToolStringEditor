from PIL import Image as PILImage
from PIL.ImageQt import ImageQt
from PyQt6.QtCore import QSize, Qt
from PyQt6.QtGui import QPixmap, QImage



def expand_and_center_images(images, max_width=1000):
    """Expands the transparent background of images horizontally while keeping their original size and centering them."""

    expanded_images = []
    for img in images:
        if isinstance(img, QPixmap):
            img = img.toImage()  # ✅ Convert QPixmap to QImage if needed

        pil_img = PILImage.fromqimage(img).convert("RGBA")  # ✅ Now safe conversion

        # Create a transparent canvas with max_width while keeping the original height
        canvas_height = pil_img.height
        expanded_img = PILImage.new("RGBA", (max_width, canvas_height), (255, 255, 255, 0))

        # Calculate x offset to center the image
        x_offset = (max_width - pil_img.width) // 2

        # Paste the original image onto the expanded transparent canvas
        expanded_img.paste(pil_img, (x_offset, 0), pil_img)

        expanded_images.append(expanded_img)

    return expanded_images


def expand_and_center_images_dropzone(tool_widgets, diagram_width, total_dropzone_height):
    """Expands background width first, then resizes all tool images only if needed."""

    if not tool_widgets:
        return

    dropzone_height = total_dropzone_height - 40  # Adjusted for padding
    max_width = diagram_width  # ✅ Set a fixed width for all images

    min_image_height = max(tool.label.height() for tool in tool_widgets)  # Prevents images from being too small

    # ✅ Step 1: Expand background width while keeping images at original size
    for tool in tool_widgets:
        if tool.image_label.pixmap():
            original_pixmap = tool.image_label.pixmap()
            # **Expand background to max_width without changing image size**
            new_width = max_width  # Fixed background width
            new_height = original_pixmap.height()  # Keep original height initially

            # **Convert to PIL and expand background**
            qimage = original_pixmap.toImage()
            pil_img = PILImage.fromqimage(qimage).convert("RGBA")

            expanded_img = PILImage.new("RGBA", (new_width, new_height), (255, 255, 255, 0))
            x_offset = (new_width - pil_img.width) // 2
            expanded_img.paste(pil_img, (x_offset, 0), pil_img)

            # **Convert back to QPixmap**
            qimage_expanded = ImageQt(expanded_img)
            pixmap_expanded = QPixmap.fromImage(qimage_expanded)

            # **Apply expanded background**
            tool.image_label.setPixmap(pixmap_expanded)
            tool.image_label.setFixedSize(QSize(new_width, new_height))

    # ✅ Step 2: Check if resizing is needed (Only resize if the total height exceeds DropZone height)
    original_total_height = sum(tool.image_label.height() for tool in tool_widgets)

    if original_total_height > dropzone_height:
        scale_factor = dropzone_height / original_total_height  # Compute scaling factor
    else:
        scale_factor = 1.0  # No scaling needed

    # ✅ Step 3: Resize all tool images if necessary
    if scale_factor < 1.0:
        for tool in tool_widgets:
            if tool.image_label.pixmap():
                original_pixmap = tool.image_label.pixmap()

                # Apply uniform scaling
                new_height = max(int(original_pixmap.height() * scale_factor),
                                 min_image_height)  # Ensure min height
                new_width = max_width  # Keep width fixed

                resized_pixmap = original_pixmap.scaled(
                    new_width, new_height,
                    Qt.AspectRatioMode.IgnoreAspectRatio,  # ✅ No aspect ratio preservation
                    Qt.TransformationMode.SmoothTransformation
                )

                # **Convert to PIL for background adjustment**
                qimage = resized_pixmap.toImage()
                pil_img = PILImage.fromqimage(qimage).convert("RGBA")

                # **Create new expanded background**
                resized_img = PILImage.new("RGBA", (max_width, new_height), (255, 255, 255, 0))
                x_offset = (max_width - pil_img.width) // 2
                resized_img.paste(pil_img, (x_offset, 0), pil_img)

                # **Convert back to QPixmap**
                qimage_resized = ImageQt(resized_img)
                pixmap_resized = QPixmap.fromImage(qimage_resized)

                # **Apply resized image**
                tool.image_label.setPixmap(pixmap_resized)
                tool.image_label.setFixedSize(QSize(max_width, new_height))  # Ensure QLabel matches new size


def combine_tool_images(images):
    """Stacks tool images vertically into one image."""
    if not images:
        return None

    total_height = sum(img.height for img in images)
    max_width = max(img.width for img in images)

    combined_image = PILImage.new("RGBA", (max_width, total_height), (255, 255, 255, 0))

    y_offset = 0
    for img in images:
        combined_image.paste(img, (0, y_offset), img)
        y_offset += img.height

    return combined_image

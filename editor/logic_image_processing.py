from PIL import Image as PILImage
from PIL.ImageQt import ImageQt
from PyQt6.QtCore import QSize
from PyQt6.QtGui import QPixmap, QImage

from utils.screen_info import get_height


def expand_and_center_images(images, max_width, return_list=False):
    """
    Processes a list of images by:
    1. Expanding their backgrounds to a uniform width.
    2. Optionally resizing all images if their combined height exceeds the dropzone height.
    3. Optionally returning the processed PIL images for export or further use.

    Args:
        images (list): List of image objects or widgets containing QPixmaps.
        max_width (int): Target background width.
        return_list (bool): If True, returns a list of expanded PIL images instead of updating UI.

    Returns:
        list: (Optional) List of expanded PIL images if return_list=True.
    """
    if not images:
        return [] if return_list else None

    expanded_images = []
    dropzone_height = get_height() - 55  # Adjust for padding
    scale_factor = 1.0
    min_height = 0

    if not return_list:
        min_height = max(img.label.height() for img in images)
        total_height = sum(img.image_label.height() for img in images)
        scale_factor = min(1.0, dropzone_height / total_height)

    for img in images:
        qimage = img if return_list else img.image_label.pixmap().toImage()
        expanded = expand_image(qimage, max_width, scale_factor, min_height)
        expanded_images.append(expanded)

        if not return_list:
            updated_pixmap = QPixmap.fromImage(ImageQt(expanded))
            img.image_label.setPixmap(updated_pixmap)
            img.image_label.setFixedSize(QSize(max_width, updated_pixmap.height()))

    return expanded_images if return_list else None


def expand_image(img, width, scale_factor=1.0, min_height=0):
    """
    Converts a QImage or QPixmap to a PIL image, resizes it if necessary, and
    expands the canvas horizontally to the given width while centering the image.

    Args:
        img (QImage | QPixmap): Image to expand.
        width (int): Target background width.
        scale_factor (float): Factor to resize image height (used for scaling to fit dropzone).
        min_height (int): Minimum height to enforce after scaling.

    Returns:
        PIL.Image: Expanded and centered PIL image.
    """
    if isinstance(img, QPixmap):
        img = img.toImage()

    # Ensure QImage format is compatible
    if img.format() != QImage.Format.Format_RGBA8888:
        img = img.convertToFormat(QImage.Format.Format_RGBA8888)

    pil_img = PILImage.fromqimage(img).convert("RGBA")
    height = max(int(pil_img.height * scale_factor), min_height)

    expanded = PILImage.new("RGBA", (width, height), (255, 255, 255, 0))
    x_offset = (width - pil_img.width) // 2
    expanded.paste(pil_img, (x_offset, 0), pil_img)

    return expanded


def combine_tool_images(images):
    """
    Stacks multiple PIL images vertically into a single combined image.

    Args:
        images (list[PIL.Image]): List of PIL images to combine.

    Returns:
        PIL.Image: Combined vertically stacked image.
    """
    if not images:
        return None

    total_height = sum(img.height for img in images)
    max_width = max(img.width for img in images)

    combined = PILImage.new("RGBA", (max_width, total_height), (255, 255, 255, 0))

    y_offset = 0
    for img in images:
        combined.paste(img, (0, y_offset), img)
        y_offset += img.height

    return combined

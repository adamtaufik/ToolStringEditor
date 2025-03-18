from PIL import Image as PILImage
from PIL.ImageQt import ImageQt
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

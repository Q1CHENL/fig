"""
Image conversion utilities for PIL Images and GdkPixbufs.

This module provides efficient conversion between PIL Images and GdkPixbuf objects
for use in GTK applications.
"""

from PIL import Image
import gi
gi.require_version('GdkPixbuf', '2.0')
from gi.repository import GdkPixbuf


class ImageConverter:
    """Utility class for converting between PIL Images and GdkPixbufs"""

    @staticmethod
    def pil_to_pixbuf(pil_image):
        """Convert PIL image to GdkPixbuf more efficiently

        Args:
            pil_image (PIL.Image): The PIL image to convert

        Returns:
            GdkPixbuf.Pixbuf: The converted pixbuf
        """
        # Get image data
        width, height = pil_image.size
        data = pil_image.tobytes()

        # Create pixbuf directly from data
        has_alpha = pil_image.mode == 'RGBA'
        colorspace = GdkPixbuf.Colorspace.RGB
        bps = 8
        rowstride = width * (4 if has_alpha else 3)

        return GdkPixbuf.Pixbuf.new_from_data(
            data,
            colorspace,
            has_alpha,
            bps,
            width,
            height,
            rowstride
        )

    @staticmethod
    def pixbuf_to_pil(pixbuf):
        """Convert GdkPixbuf to PIL Image

        Args:
            pixbuf (GdkPixbuf.Pixbuf): The pixbuf to convert

        Returns:
            PIL.Image: The converted PIL image
        """
        width, height = pixbuf.get_width(), pixbuf.get_height()
        pixels = pixbuf.get_pixels()
        stride = pixbuf.get_rowstride()
        mode = "RGBA" if pixbuf.get_has_alpha() else "RGB"

        return Image.frombytes(mode, (width, height), pixels, "raw", mode, stride)

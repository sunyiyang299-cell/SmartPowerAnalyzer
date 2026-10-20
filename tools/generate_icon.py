"""Rebuild the original vector icon at Windows icon sizes; no network assets."""
from pathlib import Path
import sys

from PIL import Image
from PySide6.QtCore import QRectF
from PySide6.QtGui import QImage, QPainter
from PySide6.QtSvg import QSvgRenderer

root = Path(__file__).resolve().parents[1]
renderer = QSvgRenderer(str(root / 'smartpower/assets/app.svg'))
assert renderer.isValid()
image = QImage(256, 256, QImage.Format.Format_ARGB32)
image.fill(0)
painter = QPainter(image)
renderer.render(painter, QRectF(0, 0, 256, 256))
painter.end()
assert image.save(str(root / 'smartpower/assets/app.png'))
with Image.open(root / 'smartpower/assets/app.png') as source:
    source.save(root / 'smartpower/assets/app.ico', sizes=[(16,16),(32,32),(48,48),(64,64),(256,256)])
print('Original SVG -> PNG and multi-size ICO')

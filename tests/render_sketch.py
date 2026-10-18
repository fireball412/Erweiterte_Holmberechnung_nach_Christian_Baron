"""Render vector sketch at high resolution using FreeCAD's bundled Qt."""
from pathlib import Path
from PySide6.QtGui import QGuiApplication,QFontDatabase,QImage,QPainter
from PySide6.QtSvg import QSvgRenderer
app=QGuiApplication([])
for font in ['arial.ttf','arialbd.ttf']:
    QFontDatabase.addApplicationFont('C:/Windows/Fonts/'+font)
path=Path(__file__).resolve().parents[1]/'docs/stegannahmen.svg'
renderer=QSvgRenderer(str(path))
assert renderer.isValid()
size=renderer.defaultSize()
image=QImage(size.width()*2,size.height()*2,QImage.Format_ARGB32)
image.fill(0xffffffff)
painter=QPainter(image);renderer.render(painter);painter.end()
assert image.save(str(path.with_suffix('.png')))

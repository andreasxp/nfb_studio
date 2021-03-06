from PySide2.QtCore import Qt, QRectF
from PySide2.QtGui import QFont, QFontMetricsF, QBrush, QPainter
from PySide2.QtWidgets import QGraphicsItem, QAbstractGraphicsShapeItem, QGraphicsRectItem

from .unitconv import inches_to_pixels as px


class TextLineItem(QAbstractGraphicsShapeItem):
    """A one-line text item.

    Default origin point is at the left side of the baseline. This can change if setAlignMode is called. TextLineItem
    also supports drawing text background. Its brush can be set using setBackgroundBrush(). Text must not contain
    newline characters.
    """
    def __init__(self, text=None, parent=None):
        super().__init__(parent)

        self._text = text or ""
        self._elided_text = text or ""
        self._elide_mode = Qt.ElideRight
        self._align_mode = Qt.AlignLeft
        self._max_width = None
        self._font = QFont()
        self._bounding_rect = QRectF()
        """Bounding and drawing rectangle. Determined automatically."""

        self.background = QGraphicsRectItem(self)
        self.background.setPen(Qt.NoPen)
        self.background.setFlag(QGraphicsItem.ItemStacksBehindParent)

        self.adjust()

    def setText(self, text: str, /) -> None:
        if '\n' in text:
            raise ValueError("text must not contain newline characters")

        self.prepareGeometryChange()
        self._text = text
        self.adjust()

    def setElideMode(self, mode: int, /) -> None:
        """Elide mode specifies where the ellipsis should be located when the text is elided. Default value is 
        Qt.ElideRight.
        """
        self.prepareGeometryChange()
        self._elide_mode = mode
        self.adjust()

    def setAlignMode(self, mode: int, /) -> None:
        """Align mode specifies text alignment.

        Text alignment changes the origin point x position:  
        - If mode is Qt.AlignLeft, the origin point is on the left of the baseline.
        - If mode is Qt.AlignHCenter, the origin point is in the center of the baseline.
        - If mode is Qt.AlignRight, the origin point is on the right of the baseline.

        Vertical alignment has no meaning for one line of text and should not be set. Default value is Qt.AlignLeft.
        """
        self.prepareGeometryChange()
        self._align_mode = mode
        self.adjust()

    def setMaximumWidth(self, width, /):
        """Set the maximum width the text is allowed to be. `None` represents unlimited width."""
        self.prepareGeometryChange()
        self._max_width = width
        self.adjust()

    def setFont(self, font: QFont, /) -> None:
        self.prepareGeometryChange()
        self._font = font
        self.adjust()

    def setBackgroundBrush(self, brush: QBrush, /):
        self.background.setBrush(brush)

    def text(self) -> str:
        return self._text

    def elidedText(self) -> str:
        return self._elided_text

    def elideMode(self) -> int:
        return self._elide_mode

    def alignMode(self) -> int:
        return self._align_mode

    def maximumWidth(self):
        """Maximum width the text is allowed to be. `None` represents unlimited width."""
        return self._max_width

    def font(self) -> QFont:
        return self._font

    def backgroundBrush(self):
        return self.background.brush()

    def adjust(self):
        """Adjust the item's geometry in response to changes."""
        metrics = QFontMetricsF(self.font())

        # Get bounding rectangle for full text
        self._bounding_rect = metrics.boundingRect(self.text())

        # Constrain by maximum width
        if self.maximumWidth() is not None:
            self._bounding_rect.setWidth(self.maximumWidth())

        # Compute elided text
        self._elided_text = metrics.elidedText(self.text(), self.elideMode(), self.boundingRect().width())

        # Get bounding rectangle for elided text
        self._bounding_rect = metrics.boundingRect(self.elidedText())
        # It seems that for small characters like "..." the bounding rect returned is too small. Adjust it by a small
        # value.
        metrics_correction = px(1/72)
        self._bounding_rect.adjust(-metrics_correction, 0, metrics_correction, 0)

        # Move origin point according to the alignment
        if self.alignMode() & Qt.AlignLeft:
            self._bounding_rect.moveLeft(0)
        elif self.alignMode() & Qt.AlignRight:
            self._bounding_rect.moveRight(0)
        else:
            self._bounding_rect.moveLeft(-self._bounding_rect.width()/2)

        # Set background rect
        self.background.setRect(self.boundingRect())

    def boundingRect(self) -> QRectF:
        return self._bounding_rect

    def paint(self, painter: QPainter, option, widget=...) -> None:
        painter.setBrush(self.brush())
        painter.setPen(self.pen())
        painter.setFont(self.font())

        painter.drawText(self.boundingRect(), self.alignMode(), self.elidedText())

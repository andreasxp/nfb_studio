from Qt.QtCore import Qt, QPointF, QMimeData
from Qt.QtGui import QPainter, QKeySequence
from Qt.QtWidgets import QGraphicsScene, QGraphicsView, QGraphicsItem, QShortcut, QApplication

from nfb_studio import bytestr_encoder as encoder, standard_decoder as decoder

from .graph import Graph, GraphSnapshot
from .node import Node
from .edge import Edge
from .connection import Input, Output


class Scheme(Graph, QGraphicsScene):
    def __init__(self, parent=None):
        """A data model for the nfb experiment's system of signals and their components.

        This graph holds two sets: a set of nodes and a set of edges.
        Intended to use inside the scheme.

        See Also
        --------
        Node
        Edge
        """
        Graph.__init__(self)
        QGraphicsScene.__init__(self, parent)

    def addItem(self, item: QGraphicsItem):
        """Add an item to the scene.

        An override of QGraphicsScene.addItem method that detects when a node or edge was added.
        """
        if isinstance(item, Node):
            Graph.addNode(self, item)

        if isinstance(item, Edge):
            Graph.addEdge(self, item)

        QGraphicsScene.addItem(self, item)

    def removeItem(self, item):
        """Add an item to the scene.

        An override of QGraphicsScene.removeItem method that detects when a node or edge was removed.
        """
        QGraphicsScene.removeItem(self, item)

        if isinstance(item, Node):
            Graph.removeNode(self, item)

        if isinstance(item, Edge):
            Graph.removeEdge(self, item)

    def connect_nodes(self, source: Output, target: Input):
        edge = Graph.connect_nodes(self, source, target)
        QGraphicsScene.addItem(self, edge)

        return edge

    def disconnect_nodes(self, source: Output, target: Input):
        edge = Graph.disconnect_nodes(self, source, target)
        if edge is not None:
            QGraphicsScene.removeItem(self, edge)

    def selectedGraph(self) -> GraphSnapshot:
        """Return the selected part of the dataflow graph as a GraphSnapshot."""
        result = GraphSnapshot()

        selected_nodes = [node for node in self.nodes if node.isSelected()]
        selected_edges = [edge for edge in self.edges if edge.isShadowSelected()]

        result.nodes = frozenset(selected_nodes)
        result.edges = frozenset(selected_edges)

        return result

    def copySelectedGraph(self):
        """Copies the selected graph and places it in the clipboard."""
        snapshot = self.selectedGraph()

        package = QMimeData()
        package.setText(encoder.encode(snapshot))

        clipboard = QApplication.clipboard()
        clipboard.setMimeData(package)

        '''
        snapshot = self.selectedGraph()
        bstr = QByteArray(bytes(encoder.encode(snapshot), "ascii"))

        package = QMimeData()
        package.setData("application/x-nfb_graph+json", bstr)

        clipboard = QApplication.clipboard()
        clipboard.setMimeData(package)
        '''

    def paste(self):
        """Retrieves the data from a clipboard and pastes it."""
        clipboard = QApplication.clipboard()
        package = clipboard.mimeData()

        if package.hasText():
            self.clearSelection()

            data = package.text()
            snapshot: GraphSnapshot = decoder.decode(data)

            for node in snapshot.nodes:
                node.setPosition(node.position() + QPointF(0.5, 0.5))
                self.addItem(node)
            for edge in snapshot.edges:
                self.addItem(edge)

    def getView(self) -> QGraphicsView:
        """Generate and return a new QGraphicsView, configured for optimal viewing."""
        v = QGraphicsView(self)
        v.setDragMode(QGraphicsView.RubberBandDrag)
        v.setRubberBandSelectionMode(Qt.ContainsItemShape)
        v.setRenderHint(QPainter.Antialiasing)
        v.setRenderHint(QPainter.SmoothPixmapTransform)

        copy_shortcut = QShortcut(QKeySequence.Copy, v)
        copy_shortcut.activated.connect(self.copySelectedGraph)

        paste_shortcut = QShortcut(QKeySequence.Paste, v)
        paste_shortcut.activated.connect(self.paste)

        return v

    # def serialize(self) -> dict: Inherited from Graph

    def deserialize(self, data: dict):
        # Clear --------------------------------------------------------------------------------------------------------
        for node in self.nodes:
            self.removeItem(node)

        # Deserialize as graph -----------------------------------------------------------------------------------------
        Graph.deserialize(self, data)

        # Bring the scene up to speed ----------------------------------------------------------------------------------
        for node in self.nodes:
            QGraphicsScene.addItem(self, node)

        for edge in self.edges:
            QGraphicsScene.addItem(self, edge)
from qgis.core import *
from qgis.gui import *
from PyQt4.QtGui import *
from PyQt4.QtCore import *

import math


class CaptureTool(QgsMapTool):
    """ Simplified port of QgsMapToolCapture from QGIS source.
    """
    CAPTURE_LINE    = 1
    CAPTURE_POLYGON = 2

    def __init__(self, canvas, onGeometryAdded, captureMode):
        QgsMapTool.__init__(self, canvas)
        self.canvas = canvas
        self.currentTool = canvas.mapTool()
        self.onGeometryAdded = onGeometryAdded
        self.captureMode     = captureMode
        self.rubberBand      = None # Rubber band for lines and polygons.
        self.tempRubberBand  = None # Connects last added point to mouse pos.
        self.capturedPoints  = []   # List of captured points in layer coords.
        self.capturing       = False
        self.setCursor(Qt.CrossCursor)


    def canvasReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            if not self.capturing:
                self.startCapturing()
            self.addVertex(event.pos())
        elif event.button() == Qt.RightButton:
            points = self.getCapturedGeometry()
            self.stopCapturing()
            if points != None:
                self.geometryCaptured(points)


    def canvasMoveEvent(self, event):
        if self.tempRubberBand != None and self.capturing:
            mapPt = self.transformCoordinates(event.pos())
            self.tempRubberBand.movePoint(mapPt)


    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Backspace or event.key() == Qt.Key_Delete:
            self.removeLastVertex()
            event.ignore()
        if event.key() == Qt.Key_Return or event.key() == Qt.Key_Enter:
            points = self.getCapturedGeometry()
            self.stopCapturing()
            if points != None:
                self.geometryCaptured(points)


    def transformCoordinates(self, screenPt):
        return self.toMapCoordinates(screenPt)

    def startCapturing(self):
        color = QColor("red")
        color.setAlphaF(0.50)

        self.rubberBand = QgsRubberBand(self.canvas, self.bandType())
        self.rubberBand.setWidth(2)
        self.rubberBand.setColor(color)
        self.rubberBand.show()

        self.tempRubberBand = QgsRubberBand(self.canvas, self.bandType())
        self.tempRubberBand.setWidth(2)
        self.tempRubberBand.setColor(color)
        self.tempRubberBand.setLineStyle(Qt.DotLine)
        self.tempRubberBand.show()

        self.capturing = True

    def stopCapturing(self):
        if self.rubberBand:
            self.canvas.scene().removeItem(self.rubberBand)
            self.rubberBand = None
        if self.tempRubberBand:
            self.canvas.scene().removeItem(self.tempRubberBand)
            self.tempRubberBand = None
        self.capturing = False
        self.capturedPoints = []
        self.canvas.refresh()

    def addVertex(self, canvasPoint):
        mapPt = self.transformCoordinates(canvasPoint)

        self.rubberBand.addPoint(mapPt)
        self.capturedPoints.append(mapPt)

        self.tempRubberBand.reset(self.bandType())
        if self.captureMode == CaptureTool.CAPTURE_LINE:
            self.tempRubberBand.addPoint(mapPt)
        elif self.captureMode == CaptureTool.CAPTURE_POLYGON:
            firstPoint = self.rubberBand.getPoint(0, 0)
            self.tempRubberBand.addPoint(firstPoint)
            self.tempRubberBand.movePoint(mapPt)
            self.tempRubberBand.addPoint(mapPt)


    def removeLastVertex(self):
        if not self.capturing: return

        bandSize     = self.rubberBand.numberOfVertices()
        tempBandSize = self.tempRubberBand.numberOfVertices()
        numPoints    = len(self.capturedPoints)

        if bandSize < 1 or numPoints < 1:
            return

        self.rubberBand.removePoint(-1)

        if bandSize > 1:
            if tempBandSize > 1:
                point = self.rubberBand.getPoint(0, bandSize-2)
                self.tempRubberBand.movePoint(tempBandSize-2, point)
        else:
            self.tempRubberBand.reset(self.bandType())

        del self.capturedPoints[-1]


    def bandType(self):
        if self.captureMode == CaptureTool.CAPTURE_POLYGON:
            return QGis.Polygon
        else:
            return QGis.Line


    def getCapturedGeometry(self):
        points = self.capturedPoints
        if self.captureMode == CaptureTool.CAPTURE_LINE and len(points) < 2:
            return None
        if self.captureMode == CaptureTool.CAPTURE_POLYGON and len(points) < 3:
            return None
        if self.captureMode == CaptureTool.CAPTURE_POLYGON:
            points.append(points[0]) # Close polygon.
        return points


    def geometryCaptured(self, layerCoords):
        if self.captureMode == CaptureTool.CAPTURE_LINE:
            geometry = QgsGeometry.fromPolyline(layerCoords)
        elif self.captureMode == CaptureTool.CAPTURE_POLYGON:
            geometry = QgsGeometry.fromPolygon([layerCoords])

        self.onGeometryAdded(geometry)

#############################################################################

class AddPointTool(QgsMapTool):
    """ Let the user add a point to canvas.
    """
    def __init__(self, canvas, onGeometryAdded):
        """ Standard initializer.
        """
        QgsMapTool.__init__(self, canvas)
        self.canvas          = canvas
        self.currentTool = canvas.mapTool()
        self.onGeometryAdded = onGeometryAdded
        self.setCursor(Qt.CrossCursor)


    def canvasReleaseEvent(self, event):
        point = self.toMapCoordinates(event.pos())
        self.onGeometryAdded(QgsGeometry.fromPoint(point))

#############################################################################

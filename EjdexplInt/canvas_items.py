from qgis.gui import *
from qgis.core import *
from PyQt4 import QtGui

class CanvasItems(object):
    """
    Helper class for administrations of Rubberband and Vertex markers
    """
   
    def __init__(self, canvas, color, style, width, icon, size):
        self.markers = []
        self.canvas = canvas
        self.color = color
        self.style = style
        self.width = width
        self.icon = icon
        self.size = size

    def setMarkerGeom(self, geom):
        self.clearMarkerGeom()
        self._setMarkerGeom(geom)

    def setMarkerGeomBuffer(self, geom, buffer):
        self.clearMarkerGeom()
        geomb = geom.buffer(buffer,12)
        self._setMarkerGeom(geomb)

    def _setMarkerGeom(self, geom):
        if geom.isMultipart():
            geometries = self._extractAsSingle(geom)
            for g in geometries:
                self._setMarkerGeom(g)
        else:
            m = None
            if geom.type() == 0:
                m = self._setPointMarker(geom)
            elif geom.type() in (1,2):
                m = self._setRubberBandMarker(geom)
            if not m is None:
                self.markers.append( m )

    def _setPointMarker(self, pointgeom):
        m = QgsVertexMarker(self.canvas)
        m.setColor(QtGui.QColor(self.color))
        m.setIconType(self.icon)
        m.setPenWidth(self.width)
        m.setIconSize(self.size)
        m.setCenter(pointgeom.asPoint())
        return m

    def _setRubberBandMarker(self, geom):
        m = QgsRubberBand(self.canvas, False)  # not polygon
        if geom.wkbType() == QGis.WKBLineString:
            linegeom = geom
        elif geom.wkbType() == QGis.WKBPolygon:
            linegeom = QgsGeometry.fromPolyline(geom.asPolygon()[0])
        m.setToGeometry(linegeom, None)
        m.setBorderColor(QtGui.QColor(self.color))
        m.setLineStyle(self.style)
        m.setWidth(self.width)
        return m

    def _extractAsSingle(self, geom):
        multiGeom = QgsGeometry()
        geometries = []
        if geom.type() == QGis.Point:
            if geom.isMultipart():
                multiGeom = geom.asMultiPoint()
                for i in multiGeom:
                    geometries.append(QgsGeometry().fromPoint(i))
            else:
                geometries.append(geom)
        elif geom.type() == QGis.Line:
            if geom.isMultipart():
                multiGeom = geom.asMultiPolyline()
                for i in multiGeom:
                    geometries.append(QgsGeometry().fromPolyline(i))
            else:
                geometries.append(geom)
        elif geom.type() == QGis.Polygon:
            if geom.isMultipart():
                multiGeom = geom.asMultiPolygon()
                for i in multiGeom:
                    geometries.append(QgsGeometry().fromPolygon(i))
            else:
                geometries.append(geom)
        return geometries

    def clearMarkerGeom(self):
        if self.markers:
            for m in self.markers:
                self.canvas.scene().removeItem(m)
        self.markers = []
        
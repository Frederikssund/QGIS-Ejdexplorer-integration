# -*- coding: utf-8 -*-
"""
/***************************************************************************
 EjdexplInt
                                 A QGIS plugin
 Opens Ejdexplorer with data chosen from QGIS
                              -------------------
        begin                : 2017-02-20
        git sha              : $Format:%H$
        copyright            : (C) 2017 by Bo Victor Thomsen, Municipality of Frederikssund
        email                : bvtho at frederikssund dot dk
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""

from PyQt4.QtSql  import QSqlDatabase,QSqlQuery
from PyQt4.QtCore import QSettings, QTranslator, qVersion, QCoreApplication
from PyQt4.QtGui import QAction, QIcon, QToolButton, QMenu, QActionGroup, QApplication, QMessageBox
import resources
#from ejdexplr_int_dialog import EjdexplIntDialog
from mapTools import *
from subprocess import Popen
import os.path
import urllib
import urllib2

class EjdexplInt:

    def __init__(self, iface):

        self.iface = iface
        self.plugin_dir = os.path.dirname(__file__)
        self.searchobj = None
        self.readconfig()
        self.updateconfig()
        self.db = QSqlDatabase.addDatabase('QODBC')
        self.db.setDatabaseName(self.config['connection'])
        
        locale = QSettings().value('locale/userLocale')[0:2]
        locale_path = os.path.join(self.plugin_dir,'i18n','EjdexplInt_{}.qm'.format(locale))
        if os.path.exists(locale_path):
            self.translator = QTranslator()
            self.translator.load(locale_path)

            if qVersion() > '4.3.3':
                QCoreApplication.installTranslator(self.translator)

    def tr(self, message):

        return QCoreApplication.translate('EjdexplInt', message)

    def initGui(self):
    
        self.action = QAction(QIcon(":/plugins/EjdexplInt/icons/icon.png"),self.tr(u'Activate EjdExplorer tool'),self.iface.mainWindow())
        self.action.setWhatsThis(u"Activate EjdExplorer tool")
        self.action.triggered.connect(self.run)
    
        self.tbmenu = QMenu()

        self.ag1 = QActionGroup(self.tbmenu,exclusive=True)
        self.acPol  = self.ag1.addAction(QAction(QIcon(':/plugins/ImpactAnalysis/icons/Icons8-Ios7-Maps-Polygon.ico'),self.tr(u'Draw polygon'),self.tbmenu,checkable=True))
        self.acLin  = self.ag1.addAction(QAction(QIcon(':/plugins/ImpactAnalysis/icons/Icons8-Ios7-Maps-Polyline.ico'),self.tr(u'Draw line'),self.tbmenu,checkable=True))
        self.acPnt  = self.ag1.addAction(QAction(QIcon(':/plugins/ImpactAnalysis/icons/Icons8-Ios7-Maps-Geo-Fence.ico'),self.tr(u'Draw point'),self.tbmenu,checkable=True))
        self.acAlay = self.ag1.addAction(QAction(QIcon(':/plugins/ImpactAnalysis/icons/Icons8-Ios7-Maps-Layers.ico'),self.tr(u'Active selection'),self.tbmenu,checkable=True))
        self.acPobj = self.ag1.addAction(QAction(QIcon(':/plugins/ImpactAnalysis/icons/Icons8-Ios7-Maps-Quest.ico'),self.tr(u'Previous object'),self.tbmenu,checkable=True))
        self.tbmenu.addActions(self.ag1.actions());
        self.acPol.setChecked(True)

        self.tbmenu.addSeparator()

        self.ag2 = QActionGroup(self.tbmenu,exclusive=True)
        self.acSingle = self.ag2.addAction(QAction(self.tr(u'Use single mode'),self.tbmenu,checkable=True))
        self.acBulk = self.ag2.addAction(QAction(self.tr(u'Use bulk mode'),self.tbmenu,checkable=True))
        self.acMerge = self.ag2.addAction(QAction(self.tr(u'Use merge mode'),self.tbmenu,checkable=True))
        self.tbmenu.addActions(self.ag2.actions());
        self.acSingle.setChecked(True)


        self.toolButton = QToolButton()
        self.toolButton.addAction(self.action)
        self.toolButton.setDefaultAction(self.action)
        self.toolButton.setMenu(self.tbmenu)
        self.toolButton.setPopupMode(QToolButton.MenuButtonPopup)
        self.iface.addToolBarWidget(self.toolButton)
        self.iface.addPluginToMenu(self.tr(u'Activate EjdExplorer tool'), self.action)

        self.ag1.triggered.connect(self.drawChanged)    

    def drawChanged(self, action):
        if action.isChecked():
            self.run()
    
    def unload(self):

        self.iface.removePluginMenu(self.tr(u'Activate EjdExplorer tool'), self.action)
        self.iface.removeToolBarIcon(self.action)
        del self.tbmenu     # No parent
        del self.toolButton # No parent


    def run(self):

        geoms =  None
        canvas = self.iface.mapCanvas()

        if self.acPol.isChecked():   # polygon
            tool = CaptureTool(canvas, self.geometryAdded, CaptureTool.CAPTURE_POLYGON)
            canvas.setMapTool(tool)        
        elif self.acLin.isChecked(): # line
            tool = CaptureTool(canvas, self.geometryAdded, CaptureTool.CAPTURE_LINE)
            canvas.setMapTool(tool)        
        elif self.acPnt.isChecked(): # point
            tool = AddPointTool(canvas, self.geometryAdded)
            canvas.setMapTool(tool)        
        elif self.acAlay.isChecked(): # active layer selection
            layer = self.iface.activeLayer()
            if (layer) and (layer.type() == QgsMapLayer.VectorLayer):
                selection = layer.selectedFeatures()
                if (selection):
                    for f in selection:
                        if geoms == None:
                            geoms = f.geometry()
                        else:
                            geoms = geoms.combine( f.geometry() )
            if (geoms != None):
                self.geometryAdded(geoms)            
            else:
                self.iface.messageBar().pushMessage(self.tr(u'EjdExplorer - Object definition'), self.tr(u'No object found'), QgsMessageBar.CRITICAL, 6)
        elif self.acPobj.isChecked(): # existing object
            geoms = self.searchobj
            if (geoms != None):
                self.geometryAdded(geoms)            
            else:
                self.iface.messageBar().pushMessage(self.tr(u'EjdExplorer - Object definition'), self.tr(u'No existing object found'), QgsMessageBar.CRITICAL, 6)
                self.acPol.setChecked(True)
        else:
            self.iface.messageBar().pushMessage(self.tr(u'EjdExplorer - Object definition'), self.tr(u'Uknown search tool'), QgsMessageBar.CRITICAL, 6)

    def cnvobj2wkt (self,gobj,epsg_in,epsg_out):

        crsSrc = QgsCoordinateReferenceSystem(int(epsg_in))
        crsDest = QgsCoordinateReferenceSystem(int(epsg_out))
        xform = QgsCoordinateTransform(crsSrc, crsDest)
        i = gobj.transform(xform)
        return gobj.exportToWkt()

    def geometryAdded(self, geom):

        self.iface.messageBar().pushMessage(self.tr(u'EjdExplorer - Start EjdExplorer'), self.tr(u'Starting EjdExplorer program, takes a few seconds..'), QgsMessageBar.INFO, 6)

        self.searchobj = geom
        epsg_in = self.iface.mapCanvas().mapRenderer().destinationCrs().authid().replace('EPSG:','')
        geom_txt = self.cnvobj2wkt (geom,epsg_in,self.config['epsg'])
        txt1, txt2 = self.getlists (geom_txt)
        
        mode = u'single'
        if self.acBulk.isChecked():
            mode = u'bulk'
        if self.acMerge.isChecked():
            mode = u'merge'

        # NB! parameters dosn't work as expected, LIFA contacted (and admit to an error in their program)
        txt = u'start ' + self.config['command'] + u' "' + self.config['parameter'].format(mode, txt1,txt2) + u'"'
        txt = txt.encode('latin-1')
        if len(txt) <= 8190: # max length of command-line parameter 
            os.system ( txt)
        else:
            self.iface.messageBar().pushMessage(self.tr(u'EjdExplorer - Start EjdExplorer'), self.tr(u'To many entities selected; try with a smaller search object'), QgsMessageBar.CRITICAL, 6)       

        self.iface.actionPan().trigger()


    def msgbox (self,txt1):

        cb = QApplication.clipboard()
        cb.setText(txt1)
        msgBox = QMessageBox()
        msgBox.setText(txt1)
        msgBox.exec_()

    def getlists(self, wkt):

        ejrlrv = []
        matrnr = []

        if (self.db.open()==True):     
 			    
            query = QSqlQuery (self.config['sqlquery'].format(wkt,self.config['epsg'])) 
            while (query.next()):
                ejrlrv.append(query.value(0))
                matrnr.append(query.value(1))
        else:
            self.iface.messageBar().pushMessage(self.tr(u'EjdExplorer - Database Error'), db.lastError().text(), QgsMessageBar.INFO, 6)

        return u','.join(ejrlrv), u','.join(matrnr) 

        
    def readconfig(self):

        s = QSettings()
        k = __package__
        self.config = {
            'epsg':       unicode(s.value(k + "/epsg"       , "25832", type=str)),
            'sqlquery':   unicode(s.value(k + "/sqlquery"   , "select  LTRIM(RTRIM(CONVERT(varchar(10), [landsejerlavskode]))) as ejrlvnr, LTRIM(RTRIM([matrikelnummer])) as matrnr from [dbo].[Jordstykke] where geometry::STGeomFromText('{0}',{1}).STIntersects([geometri])=1", type=str)),
            'connection': unicode(s.value(k + "/connection" , "Driver={SQL Server};Server=f-sql12;Database=LOIS;Trusted_Connection=Yes;", type=str)),
            'command':    unicode(s.value(k + "/command"    , 'C:/"Program Files (x86)"/LIFA/EjdExplorer/LIFA.EjdExplorer.GUI.exe', type=str)),
            'parameter':  unicode(s.value(k + "/parameter"  , 'ejdexpl://?mode={0}&CadastralDistrictIdentifier={1}&RealPropertyKey={2}', type=str))
        }

    def updateconfig(self):

        s = QSettings()
        k = __package__
        s.setValue(k + "/epsg",          self.config['epsg'])
        s.setValue(k + "/sqlquery",      self.config['sqlquery'])
        s.setValue(k + "/connection",    self.config['connection'])
        s.setValue(k + "/command",       self.config['command'])
        s.setValue(k + "/parameter",     self.config['parameter'])
        s.sync


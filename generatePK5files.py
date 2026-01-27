######################## PeKa2D-v5 Graphical User Interface (GUI) #########################

# PeKa2D-v5 GUI plugin for QGIS 3 
# © 2025 Sergio Martínez-Aranda. License CC BY-NC-SA 4.0 
# To view a copy of this license, visit https://creativecommons.org/licenses/by-nc-sa/4.0/

###########################################################################################

from qgis.PyQt.QtWidgets import (
    QMessageBox,
    QInputDialog,
    QDialog, QVBoxLayout, QPushButton,
    QCheckBox, QLabel, QLineEdit
)
from qgis.core import (
    QgsProject, 
    QgsVectorLayer,
    QgsRasterLayer, 
    QgsField, 
    QgsFields, 
    QgsVectorFileWriter, 
    QgsMeshLayer, 
    QgsPointXY, 
    QgsFeature, 
    QgsGeometry,
    QgsMapLayerProxyModel,
    QgsSpatialIndex,
    QgsGraduatedSymbolRenderer,
    QgsFillSymbol,
    QgsStyle,
    QgsEditorWidgetSetup   
)
from qgis.gui import (
    QgsMapLayerComboBox
)
from PyQt5.QtCore import (
    Qt,
    QVariant,
    QSettings
)
from PyQt5.QtWidgets import QSpinBox
from PyQt5.QtGui import QIntValidator
import os
from . import tools
from .messages import (
    log_info,
    log_error,
    log_warning
)


def openExportDialog(iface):
    dlg = exportDialog(iface, iface.mainWindow())
    dlg.exec()


class exportDialog(QDialog):

    def __init__(self, iface, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Export PeKa2D-v5 files")
        self.iface = iface
        
        layout = QVBoxLayout(self) 

        # Case base name
        case_name = "case1" 

        # Export DAT-FED
        btn_create1 = QPushButton("Export DAT-FED files")
        btn_create1.clicked.connect(self.on_export_dat_fed_files(case_name))
        layout.addWidget(btn_create1)

        # Export hotstart
        btn_create2 = QPushButton("Export HOTSTART file")
        btn_create2.clicked.connect(self.on_export_hotstart_file)
        layout.addWidget(btn_create2) 

        # Export OBCP
        btn_create3 = QPushButton("Export OBCP file")
        btn_create3.clicked.connect(self.on_export_obcp_file)
        layout.addWidget(btn_create3)              


    # Actions
    def on_export_dat_fed_files(self,case_name):     
        createDATFEDfiles(case_name)

    def on_export_hotstart_file(self,case_name):     
        createHOTSTARTfiles(case_name)

    def on_export_obcp_file(self,case_name):     
        createOBCPfiles(case_name)        


def createDATFEDfiles(case_name):

    msg=f"Export {case_name}.DAT and {case_name}.FED files done." 
    log_info(msg)


def createHOTSTARTfiles(case_name):

    msg=f"Export {case_name}.DAT and {case_name}.FED files done." 
    log_info(msg)


def createOBCPfiles(case_name):

    msg=f"Export {case_name}.DAT and {case_name}.FED files done." 
    log_info(msg)  


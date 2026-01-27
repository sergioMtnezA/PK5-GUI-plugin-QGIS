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


def openBoundaryDialog(iface):
    dlg = boundaryDialog(iface, iface.mainWindow())
    dlg.exec()


class boundaryDialog(QDialog):

    def __init__(self, iface, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Open Boundary Conditions")
        self.iface = iface
        
        layout = QVBoxLayout(self)

        ### INLETS #############################################
        layout.addWidget(QLabel("########## Inlet zones ##########"))

        # Create vectorial layer
        btn_create1 = QPushButton("Define inlet boundaries")
        btn_create1.clicked.connect(self.on_create_inlet_layer)
        layout.addWidget(btn_create1)

        ### OUTLETS #############################################
        layout.addWidget(QLabel("########## Outlet zones ##########"))

        btn_create2 = QPushButton("Define outlet boundaries")
        btn_create2.clicked.connect(self.on_create_outlet_layer)
        layout.addWidget(btn_create2)     


    # Actions
    def on_create_inlet_layer(self):
        layer_name = "Inlets"
        value_list = [
            {"HYD_INFLOW_Q" : "HYD_INFLOW_Q"},
            {"HYD_INFLOW_HZ" : "HYD_INFLOW_HZ"},
            {"HYD_INFLOW_QHZ" : "HYD_INFLOW_QHZ"}        
        ]
        createOpenBoundaryLayer(layer_name,value_list)

        fill_color = None
        edge_color = "0, 0, 255"        
        reloadAndStyleBoundary(layer_name,value_list,fill_color,edge_color,self.iface)        


    def on_create_outlet_layer(self):
        layer_name = "Outlets"
        value_list = [
            {"HYD_OUTFLOW_GAUGE" : "HYD_OUTFLOW_GAUGE"},
            {"HYD_OUTFLOW_HZ" : "HYD_OUTFLOW_HZ"},
            {"HYD_OUTFLOW_FREE" : "HYD_OUTFLOW_FREE"},
            {"HYD_OUTFLOW_FR" : "HYD_OUTFLOW_FR"},
            {"HYD_OUTFLOW_NORMAL" : "HYD_OUTFLOW_NORMAL"}
        ]            
        createOpenBoundaryLayer(layer_name,value_list)

        fill_color = None
        edge_color = "255, 0, 0"        
        reloadAndStyleBoundary(layer_name,value_list,fill_color,edge_color,self.iface)    


def createOpenBoundaryLayer(layer_name,value_list):
    # Obtener carpeta del proyecto
    project_path = QgsProject.instance().fileName()
    if not project_path:
        QMessageBox.critical(None, "Error", "Guarda primero el proyecto")
        return
    project_folder = os.path.dirname(project_path)

    # Tomar CRS del proyecto
    project_crs = QgsProject.instance().crs() 

    # Ruta del shapefile
    shp_path = os.path.join(project_folder, f"{layer_name}.shp")

    # Crear capa poligonal en memoria con CRS del proyecto
    layer = QgsVectorLayer(f"Polygon?crs={project_crs.authid()}", layer_name, "memory")        

    # Añadir campo IDname
    field_name1="IDname"
    layer.dataProvider().addAttributes([QgsField(field_name1, QVariant.String)])
    layer.updateFields()

    # Añadir campo Type
    field_name2 = "Type"
    layer.dataProvider().addAttributes([QgsField(field_name2, QVariant.String)])
    layer.updateFields()

    # Añadir campo File
    field_name3 = "File"
    layer.dataProvider().addAttributes([QgsField(field_name3, QVariant.String)])
    layer.updateFields()    

    # Opciones modernas para guardar
    options = QgsVectorFileWriter.SaveVectorOptions()
    options.driverName = "ESRI Shapefile"
    options.fileEncoding = "UTF-8"

    # Guardar capa con QgsVectorFileWriter (forma moderna)
    writer = QgsVectorFileWriter(
        shp_path, "UTF-8", layer.fields(), layer.wkbType(), layer.crs(), "ESRI Shapefile"
    )

    if writer.hasError() != QgsVectorFileWriter.NoError:
        QMessageBox.critical(None, "Error", f"No se pudo crear {shp_path}")
        return

    # Copiar features de la capa en memoria
    for feat in layer.getFeatures():
        writer.addFeature(feat)

    del writer  # cerrar archivo correctamente

    # Cargar capa en QGIS
    #loaded_layer = QgsVectorLayer(shp_path, layer_name, "ogr")

    # Configurar el widget para el campo "Type"
    #field_idx = loaded_layer.fields().indexOf("Type")
    #if field_idx >= 0:
    #    widget_setup = QgsEditorWidgetSetup("ValueMap", {"map": value_list})
    #    loaded_layer.setEditorWidgetSetup(field_idx, widget_setup)

    # Configurar widget para el campo "File"
    #field_idx = loaded_layer.fields().indexOf("File")
    #if field_idx >= 0:
    #    file_config = { #file-selector
    #        'RelativeStorage': 0,  # 0 = ruta absoluta, 1 = relativa
    #        'StorageMode': 0,      # 0 = guardar ruta, 1 = base64
    #        'FileWidget': True,    # Mostrar widget de archivo
    #        'FileWidgetButton': True,  # Botón para explorar
    #        'Filter': 'Archivos de texto (*.txt);;Todos los archivos (*.*)'
    #    }
    #    widget_setup = QgsEditorWidgetSetup("ExternalResource", file_config)
    #    loaded_layer.setEditorWidgetSetup(field_idx, widget_setup)        
    
    # Añadir la capa al proyecto
    #QgsProject.instance().addMapLayer(loaded_layer)    

    msg=f"{layer_name} layer created." 
    log_info(msg)  


def reloadAndStyleBoundary(layer_name,value_list,fill_color,edge_color,iface):
    #tools.remove_layer_by_name(layer_name)

    project_folder = os.path.dirname(QgsProject.instance().fileName())
    layer_path = os.path.join(project_folder, f"{layer_name}.shp")
    layer = QgsVectorLayer(layer_path, layer_name, "ogr")

    # Configurar el widget para el campo "Type"
    field_idx = layer.fields().indexOf("Type")
    if field_idx >= 0:
        widget_setup = QgsEditorWidgetSetup("ValueMap", {"map": value_list})
        layer.setEditorWidgetSetup(field_idx, widget_setup)

    # Configurar widget para el campo "File"
    field_idx = layer.fields().indexOf("File")
    if field_idx >= 0:
        file_config = { #file-selector
            'RelativeStorage': 0,  # 0 = ruta absoluta, 1 = relativa
            'StorageMode': 0,      # 0 = guardar ruta, 1 = base64
            'FileWidget': True,    # Mostrar widget de archivo
            'FileWidgetButton': True,  # Botón para explorar
            'Filter': 'Archivos de texto (*.txt);;Todos los archivos (*.*)'
        }
        widget_setup = QgsEditorWidgetSetup("ExternalResource", file_config)
        layer.setEditorWidgetSetup(field_idx, widget_setup)     

    # --- Renderer ---
    renderer = tools.createSimpleRenderer(fill_color, edge_color, opacity=1.0)
    layer.setRenderer(renderer)

    # --- Añadir al proyecto y refrescar ---
    QgsProject.instance().addMapLayer(layer)
    layer.triggerRepaint()
    iface.mapCanvas().refresh()    



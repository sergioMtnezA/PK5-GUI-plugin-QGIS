######################## PeKa2D-v5 Graphical User Interface (GUI) #########################

# PeKa2D-v5 GUI plugin for QGIS 3 
# © 2025 Sergio Martínez-Aranda. License CC BY-NC-SA 4.0 
# To view a copy of this license, visit https://creativecommons.org/licenses/by-nc-sa/4.0/

###########################################################################################

from qgis.PyQt.QtWidgets import (
    QMessageBox,
    QInputDialog,
    QDialog, QVBoxLayout, QPushButton,
    QCheckBox, QLabel
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
    QgsStyle    
)
from qgis.gui import (
    QgsMapLayerComboBox
)
from PyQt5.QtCore import (
    Qt,
    QVariant
)
import os
from . import tools
from .messages import (
    log_info,
    log_error,
    log_warning
)


def openTerrainDialog(iface):
    dlg = terrainDialog(iface, iface.mainWindow())
    dlg.exec()


class terrainDialog(QDialog):

    def __init__(self, iface, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Terrain features")
        self.iface = iface
        layout = QVBoxLayout(self)

        ### TERRAIN ELEVATION #############################################
        layout.addWidget(QLabel("########## Terrain elevation data ##########"))

        # --- Botón crear bed_elevation_layer ---
        btn_bed = QPushButton("Generate terrain elevation layer")
        btn_bed.clicked.connect(self.on_create_terrain_elevation_layer)
        layout.addWidget(btn_bed)

        # --- Checkbox para interpolar con raster ---
        self.checkbox_terrain = QCheckBox("Sample terrain elevation with raster")
        self.checkbox_terrain.stateChanged.connect(self.on_checkbox_terrain_changed)
        layout.addWidget(self.checkbox_terrain)

        # --- Selector de raster ---
        self.raster_terrain_selector = QgsMapLayerComboBox()
        self.raster_terrain_selector.setFilters(QgsMapLayerProxyModel.RasterLayer)
        self.raster_terrain_selector.setEnabled(False)  # deshabilitado hasta marcar el checkbox
        layout.addWidget(self.raster_terrain_selector)
 
        # --- Botón add bed_elevation_layer ---
        btn_add_bed = QPushButton("Add terrain elevation to mesh")
        btn_add_bed.clicked.connect(self.on_add_terrain_elevation)
        layout.addWidget(btn_add_bed)



        ### MANNING ROUGHNESS #############################################
        layout.addWidget(QLabel("########## Surface roughness data ##########"))

        # --- Botón crear vectorial layer ---
        btn_nman = QPushButton("Generate nManning roughness layer")
        btn_nman.clicked.connect(self.on_create_nmanning_layer)
        layout.addWidget(btn_nman)

        # --- Checkbox para interpolar con raster ---
        self.checkbox_nmanning = QCheckBox("Sample nManning roughness with raster")
        self.checkbox_nmanning.stateChanged.connect(self.on_checkbox_nmanning_changed)
        layout.addWidget(self.checkbox_nmanning)

        # --- Selector de raster ---
        self.raster_nmanning_selector = QgsMapLayerComboBox()
        self.raster_nmanning_selector.setFilters(QgsMapLayerProxyModel.RasterLayer)
        self.raster_nmanning_selector.setEnabled(False)  # deshabilitado hasta marcar el checkbox
        layout.addWidget(self.raster_nmanning_selector)
 
        # --- Botón add bed_elevation_layer ---
        btn_add_nman = QPushButton("Add  nManning roughness to mesh")
        btn_add_nman.clicked.connect(self.on_add_nmanning)
        layout.addWidget(btn_add_nman)


    # Terrain elevation actions
    def on_create_terrain_elevation_layer(self):
        layer_name = "terrainZ"
        field_name = "zbed"
        createFeatureLayer(layer_name,field_name,self.iface)    

        fill_color = "222, 184, 135"
        edge_color = "222, 184, 135"        
        reloadAndStyleFeature(layer_name,fill_color,edge_color,self.iface)

    def on_checkbox_terrain_changed(self, state):
        self.raster_terrain_selector.setEnabled(state == Qt.Checked)  # 2 = Qt.Checked   

    def on_add_terrain_elevation(self):
        if self.checkbox_terrain.isChecked():
            raster = self.raster_terrain_selector.currentLayer()
            field_name = "zbed"
            addFeatureToMeshFromRaster(raster,field_name)
        else:
            layer_name = "terrainZ"
            field_name = "zbed"
            addFeatureToMesh(layer_name,field_name)

        reloadAndStyleMesh("zbed",self.iface)


    # nManning roughness actions
    def on_create_nmanning_layer(self):
        layer_name = "nManning"
        field_name = "nman"
        createFeatureLayer(layer_name,field_name,self.iface) 

        fill_color = "50,200,50"
        edge_color = "50,200,50"        
        reloadAndStyleFeature(layer_name,fill_color,edge_color,self.iface)

    def on_checkbox_nmanning_changed(self, state):
        self.raster_nmanning_selector.setEnabled(state == Qt.Checked)  # 2 = Qt.Checked   

    def on_add_nmanning(self):
        if self.checkbox_nmanning.isChecked():
            raster = self.raster_nmanning_selector.currentLayer()
            field_name = "nman"
            addFeatureToMeshFromRaster(raster,field_name)
        else:
            layer_name = "nManning"
            field_name = "nman"
            addFeatureToMesh(layer_name,field_name)

        reloadAndStyleMesh("nman",self.iface)



def createFeatureLayer(layer_name,field_name,iface):
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

    # Añadir campo zb
    layer.dataProvider().addAttributes([QgsField(field_name, QVariant.Double)])
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

    # Copiar features de la capa en memoria (aquí no hay, pero sirve para futuras inserciones)
    for feat in layer.getFeatures():
        writer.addFeature(feat)

    del writer  # cerrar archivo correctamente

    # Cargar capa en QGIS
    #QgsProject.instance().addMapLayer(
    #    QgsVectorLayer(shp_path, layer_name, "ogr")
    #)
    #reloadAndStyleFeature(layer_name,iface)

    msg=f"{layer_name} feature layer created." 
    log_info(msg)
    #QMessageBox.information(None, "DOMAIN", f"Capa domain creada en {shp_path}")


def addFeatureToMesh(layer_name,field_name):

    # Project folder
    project_path = QgsProject.instance().fileName()
    project_folder = os.path.dirname(project_path)

    # Mesh layer
    mesh_path = os.path.join(project_folder, "mesh.shp")
    mesh = QgsVectorLayer(mesh_path, "mesh", "ogr")
    if not mesh.isValid():
        log_error("Domain mesh not found or invalid")
        return

    # Source layer
    source_path = os.path.join(project_folder, f"{layer_name}.shp")
    source = QgsVectorLayer(source_path, layer_name, "ogr")
    source_polygons = list(source.getFeatures())  # orden de la capa

    # New mesh field
    if field_name not in [f.name() for f in mesh.fields()]:
        mesh.startEditing()
        mesh.addAttribute(QgsField(field_name, QVariant.Double))
        mesh.updateFields()
        mesh.commitChanges()

    # Sample new mesh values
    mesh.startEditing()
    for feat in mesh.getFeatures():
        centroid = feat.geometry().centroid()

        val = None
        for pol in source_polygons:
            if pol.geometry().contains(centroid):
                val = pol[field_name]

        if val is not None:
            feat[field_name] = val
        else:
            feat[field_name] = 0.0
        
        mesh.updateFeature(feat)

    mesh.commitChanges()

    msg=f"Feature {field_name} added to mesh layer"
    log_info(msg)


def addFeatureToMeshFromRaster(raster,field_name):

    # Project folder
    project_path = QgsProject.instance().fileName()
    project_folder = os.path.dirname(project_path)

    # Mesh layer
    mesh_path = os.path.join(project_folder, "mesh.shp")
    mesh = QgsVectorLayer(mesh_path, "mesh", "ogr")
    if not mesh.isValid():
        log_error("Domain mesh not found or invalid")
        return
    
    # Get raster layer data
    provider = raster.dataProvider()

    # New mesh field
    if field_name not in [f.name() for f in mesh.fields()]:
        mesh.startEditing()
        mesh.addAttribute(QgsField(field_name, QVariant.Double))
        mesh.updateFields()
        mesh.commitChanges()

    # Sample new mesh values
    mesh.startEditing()
    for feat in mesh.getFeatures():
        pt = feat.geometry().centroid().asPoint()
        result = provider.sample(pt, 1)

        if result[1]:  # ok
            feat[field_name] = result[0]
        else:
            feat[field_name] = 0.0            
        
        mesh.updateFeature(feat)


    mesh.commitChanges()

    msg=f"Feature {field_name} sampled to mesh layer from raster"
    log_info(msg)


def reloadAndStyleMesh(var,iface):    
    tools.remove_layer_by_name("mesh")

    project_folder = os.path.dirname(QgsProject.instance().fileName())
    mesh_path = os.path.join(project_folder, "mesh.shp")
    mesh = QgsVectorLayer(mesh_path, "mesh", "ogr")
    if not mesh.isValid():
        log_error("Domain mesh not found or invalid")
        return

    if var not in [f.name() for f in mesh.fields()]:
        raise RuntimeError(f"Field {var} does not exist in mesh")

    # --- Renderer graduado ---
    #renderer = tools.createGraduatedRenderer(mesh, var, n_classes=9)
    renderer = tools.createContinuousRenderer(mesh, var, n_classes=12)
    #ramp_name="Terrain_color"
    #xml_style_path=r"C:\Users\marti\AppData\Roaming\QGIS\QGIS3\profiles\default\python\plugins\gmshMesherPK5\styles\terrain_qgis.xml"
    #renderer = tools.createContinuousRenderer(mesh, var, xml_style_path, ramp_name, n_classes=9)
    mesh.setRenderer(renderer)

    # --- Añadir al proyecto y refrescar ---
    QgsProject.instance().addMapLayer(mesh)
    mesh.triggerRepaint()
    iface.mapCanvas().refresh()


def reloadAndStyleFeature(layer_name,fill_color,edge_color,iface):
    tools.remove_layer_by_name(layer_name)

    project_folder = os.path.dirname(QgsProject.instance().fileName())
    layer_path = os.path.join(project_folder, f"{layer_name}.shp")
    layer = QgsVectorLayer(layer_path, layer_name, "ogr")

    # --- Renderer ---
    #fill_color = None
    #edge_color = "50,50,50"
    renderer = tools.createSimpleRenderer(fill_color, edge_color, opacity=0.2)
    layer.setRenderer(renderer)

    # --- Añadir al proyecto y refrescar ---
    QgsProject.instance().addMapLayer(layer)
    layer.triggerRepaint()
    iface.mapCanvas().refresh()



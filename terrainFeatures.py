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
        layout.addWidget(QLabel("Terrain elevation data :::::::::::::::::"))

        # --- Botón crear bed_elevation_layer ---
        btn_bed = QPushButton("Generate terrain elevation layer")
        btn_bed.clicked.connect(self.on_create_terrain_elevation_layer)
        layout.addWidget(btn_bed)

        # --- Checkbox para interpolar con raster ---
        self.checkbox_terrain = QCheckBox("Sample terrain elevation with raster")
        self.checkbox_terrain.stateChanged.connect(self.on_checkbox_changed)
        layout.addWidget(self.checkbox_terrain)

        # --- Selector de raster ---
        self.raster_selector = QgsMapLayerComboBox()
        self.raster_selector.setFilters(QgsMapLayerProxyModel.RasterLayer)
        self.raster_selector.setEnabled(False)  # deshabilitado hasta marcar el checkbox
        layout.addWidget(self.raster_selector)
 
        # --- Botón add bed_elevation_layer ---
        btn_add_bed = QPushButton("Add terrain elevation to mesh")
        btn_add_bed.clicked.connect(self.on_add_terrain_elevation)
        layout.addWidget(btn_add_bed)





    def on_create_terrain_elevation_layer(self):
        createTerrainElevationLayer()    

    def on_checkbox_changed(self, state):
        self.raster_selector.setEnabled(state == Qt.Checked)  # 2 = Qt.Checked   

    def on_add_terrain_elevation(self):
        if self.checkbox_terrain.isChecked():
            raster = self.raster_selector.currentLayer()
            addTerrainElevationToMeshFromRaster(raster)
        else:
            addTerrainElevationToMesh()

        #reload mesh layer with zbed
        reloadAndStyleMesh("zbed",self.iface)


def createTerrainElevationLayer():
    # Obtener carpeta del proyecto
    project_path = QgsProject.instance().fileName()
    if not project_path:
        QMessageBox.critical(None, "Error", "Guarda primero el proyecto")
        return
    project_folder = os.path.dirname(project_path)

    # Tomar CRS del proyecto
    project_crs = QgsProject.instance().crs() 

    # Ruta del shapefile
    shp_path = os.path.join(project_folder, "terrainElevation.shp")

    # Crear capa poligonal en memoria con CRS del proyecto
    layer = QgsVectorLayer(f"Polygon?crs={project_crs.authid()}", "terrainElevation", "memory")        

    # Añadir campo zb
    layer.dataProvider().addAttributes([QgsField("zbed", QVariant.Double)])
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
    QgsProject.instance().addMapLayer(
        QgsVectorLayer(shp_path, "terrainElevation", "ogr")
    )

    msg=f"Bed elevation layer created."    
    log_info(msg)
    #QMessageBox.information(None, "DOMAIN", f"Capa domain creada en {shp_path}")


def addTerrainElevationToMesh():

    # Obtener carpeta del proyecto
    project_path = QgsProject.instance().fileName()
    project_folder = os.path.dirname(project_path)

    # --- Obtener capas ---
    # Mesh layer
    mesh_path = os.path.join(project_folder, "mesh.shp")
    mesh = QgsVectorLayer(mesh_path, "mesh", "ogr")
    if not mesh.isValid():
        log_error("Domain mesh not found or invalid")
        return

    # Terrain elevation layer
    bed_path = os.path.join(project_folder, "terrainElevation.shp")
    bed = QgsVectorLayer(bed_path, "terrainElevation", "ogr")

    # --- Campo destino ---
    field_name = "zbed"
    if field_name not in [f.name() for f in mesh.fields()]:
        mesh.startEditing()
        mesh.addAttribute(QgsField(field_name, QVariant.Double))
        mesh.updateFields()
        mesh.commitChanges()

    # --- Construir lista de polígonos bed ---
    bed_features = list(bed.getFeatures())  # orden de la capa

    mesh.startEditing()

    for feat in mesh.getFeatures():

        centroid = feat.geometry().centroid()

        z_val = None
        for bed_feat in bed_features:
            if bed_feat.geometry().contains(centroid):
                z_val = bed_feat["zbed"]

        if z_val is not None:
            feat[field_name] = z_val
            mesh.updateFeature(feat)

    mesh.commitChanges()

    msg="Elevation added to mesh from terrain layer"
    log_info(msg)


def addTerrainElevationToMeshFromRaster(raster_layer):

    # Obtener carpeta del proyecto
    project_path = QgsProject.instance().fileName()
    project_folder = os.path.dirname(project_path)

    # --- Obtener capas ---
    # Mesh layer
    mesh_path = os.path.join(project_folder, "mesh.shp")
    mesh = QgsVectorLayer(mesh_path, "mesh", "ogr")
    if not mesh.isValid():
        log_error("Domain mesh not found or invalid")
        return

    # --- Campo destino ---
    field_name = "zbed"
    if field_name not in [f.name() for f in mesh.fields()]:
        mesh.startEditing()
        mesh.addAttribute(QgsField(field_name, QVariant.Double))
        mesh.updateFields()
        mesh.commitChanges()

    # Get raster layer data
    provider = raster_layer.dataProvider()

    mesh.startEditing()

    for feat in mesh.getFeatures():

        pt = feat.geometry().centroid().asPoint()
        result = provider.sample(pt, 1)

        if result[1]:  # ok
            feat[field_name] = result[0]
            mesh.updateFeature(feat)

    mesh.commitChanges()

    msg="Elevation added to mesh from MDT raster"
    log_info(msg)


def reloadAndStyleMesh(var,iface):
    """
    Recarga la capa de malla y aplica simbología graduada por zbed
    """
    tools.remove_layer_by_name("mesh")
    tools.remove_layer_by_name("mesh_v2")

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
    renderer = tools.createContinuousRenderer(mesh, var, n_classes=9)
    #ramp_name="Terrain_color"
    #xml_style_path=r"C:\Users\marti\AppData\Roaming\QGIS\QGIS3\profiles\default\python\plugins\gmshMesherPK5\styles\terrain_qgis.xml"
    #renderer = tools.createContinuousRenderer(mesh, var, xml_style_path, ramp_name, n_classes=9)
    mesh.setRenderer(renderer)

    # --- Añadir al proyecto y refrescar ---
    QgsProject.instance().addMapLayer(mesh)
    mesh.triggerRepaint()
    iface.mapCanvas().refresh()



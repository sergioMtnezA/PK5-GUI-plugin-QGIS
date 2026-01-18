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
    QgsStyle    
)
from qgis.gui import (
    QgsMapLayerComboBox
)
from PyQt5.QtCore import (
    Qt,
    QVariant
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


def openInitialDialog(iface):
    dlg = initialDialog(iface, iface.mainWindow())
    dlg.exec()


class initialDialog(QDialog):

    def __init__(self, iface, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Initial Conditions")
        self.iface = iface

        self.n_sediments = 1  #default
        
        layout = QVBoxLayout(self)

        ### FLOW DEPTH #############################################
        layout.addWidget(QLabel("########## Flow depth ##########"))

        # Create vectorial layer
        btn_create1 = QPushButton("Create flow depth layer")
        btn_create1.clicked.connect(self.on_create_flow_depth_layer)
        layout.addWidget(btn_create1)

        # Checkbox for raster interpolation
        self.checkbox1 = QCheckBox("Sample flow depth with raster")
        self.checkbox1.stateChanged.connect(self.on_checkbox_flow_depth_changed)
        layout.addWidget(self.checkbox1)

        # Raster selector list
        self.select_raster1 = QgsMapLayerComboBox()
        self.select_raster1.setFilters(QgsMapLayerProxyModel.RasterLayer)
        self.select_raster1.setEnabled(False)
        layout.addWidget(self.select_raster1)
 
        # Add feature to mesh
        btn_add1 = QPushButton("Add flow depth to mesh")
        btn_add1.clicked.connect(self.on_add_flow_depth)
        layout.addWidget(btn_add1)


       ### FLOW VELOCITY #############################################
        layout.addWidget(QLabel("########## Flow velocity ##########"))

        # Create vectorial layer
        btn_create2 = QPushButton("Create flow velocity layer")
        btn_create2.clicked.connect(self.on_create_flow_vel_layer)
        layout.addWidget(btn_create2)

        # Checkbox for raster interpolation
        self.checkbox2 = QCheckBox("Sample flow velocity with raster")
        self.checkbox2.stateChanged.connect(self.on_checkbox_flow_vel_changed)
        layout.addWidget(self.checkbox2)

        # Raster selector list
        layout.addWidget(QLabel("U-velocity"))
        self.select_raster2x = QgsMapLayerComboBox()
        self.select_raster2x.setFilters(QgsMapLayerProxyModel.RasterLayer)
        self.select_raster2x.setEnabled(False)
        layout.addWidget(self.select_raster2x)

        layout.addWidget(QLabel("V-velocity"))
        self.select_raster2y = QgsMapLayerComboBox()
        self.select_raster2y.setFilters(QgsMapLayerProxyModel.RasterLayer)
        self.select_raster2y.setEnabled(False)
        layout.addWidget(self.select_raster2y)        
 
        # Add feature to mesh
        btn_add2 = QPushButton("Add flow velocity to mesh")
        btn_add2.clicked.connect(self.on_add_flow_vel)
        layout.addWidget(btn_add2)


        ### FLOW SED CONCENTRATION #############################################
        layout.addWidget(QLabel("########## Sediment concentration ##########"))

        # Number of sediments/layers
        self.btn_spin3 = QSpinBox()
        self.btn_spin3.setMinimum(1)
        self.btn_spin3.setMaximum(50)
        self.btn_spin3.setValue(self.n_sediments)
        self.btn_spin3.valueChanged.connect(self.on_nsediments_changed)
        layout.addWidget(QLabel("Number of sediment/layers:"))
        layout.addWidget(self.btn_spin3)

        # Create vectorial layer
        btn_create3 = QPushButton("Create sediment concentration layer")
        btn_create3.clicked.connect(self.on_create_sediment_concentratrion_layer)
        layout.addWidget(btn_create3)
 
        # Add feature to mesh
        btn_add3 = QPushButton("Add sediment concentration to mesh")
        btn_add3.clicked.connect(self.on_add_sediment_concentratrion)
        layout.addWidget(btn_add3)       


    # Flow depth actions
    def on_create_flow_depth_layer(self):
        layer_name = "flowH"
        field_name = "hini"
        createFlowScalarLayer(layer_name,field_name)

        fill_color = "0, 0, 200"
        edge_color = "0, 0, 200"        
        reloadAndStyleFlow(layer_name,fill_color,edge_color,self.iface)        

    def on_checkbox_flow_depth_changed(self, state):
        self.select_raster1.setEnabled(state == Qt.Checked)  # 2 = Qt.Checked   

    def on_add_flow_depth(self):
        if self.checkbox1.isChecked():
            raster = self.select_raster1.currentLayer()
            field_name = "hini"
            addFlowScalarToMeshFromRaster(raster,field_name)
        else:
            layer_name = "flowH"
            field_name = "hini"
            addFlowScalarToMesh(layer_name,field_name)

        reloadAndStyleMesh("hini",self.iface)


    # Flow velocity actions
    def on_create_flow_vel_layer(self):
        layer_name = "flowVEL"
        field1_name = "uini"
        field2_name = "vini"
        createFlowVectorLayer(layer_name,field1_name,field2_name)    

        fill_color = "255, 220, 120"
        edge_color = "255, 220, 120"        
        reloadAndStyleFlow(layer_name,fill_color,edge_color,self.iface)           

    def on_checkbox_flow_vel_changed(self, state):
        self.select_raster2x.setEnabled(state == Qt.Checked)  # 2 = Qt.Checked
        self.select_raster2y.setEnabled(state == Qt.Checked)  # 2 = Qt.Checked   

    def on_add_flow_vel(self):
        if self.checkbox2.isChecked():
            rasterX = self.select_raster2x.currentLayer()
            rasterY = self.select_raster2y.currentLayer()
            field1_name = "uini"
            field2_name = "vini"
            addFlowVectorToMeshFromRaster(rasterX,rasterY,field1_name,field2_name)
        else:
            layer_name = "flowVEL"
            field1_name = "uini"
            field2_name = "vini"
            addFlowVectorToMesh(layer_name,field1_name,field2_name)

        reloadAndStyleMesh("uini",self.iface)        


    # Sediment concentration actions
    def on_nsediments_changed(self, value):
        self.n_sediments = value

    def on_create_sediment_concentratrion_layer(self):
        layer_name = "flowPhi"
        field_name = "phi"
        createFlowMultiScalarLayer(layer_name,field_name,self.n_sediments)

        fill_color = "255, 102, 255"
        edge_color = "255, 102, 255"        
        reloadAndStyleFlow(layer_name,fill_color,edge_color,self.iface)        

    def on_add_sediment_concentratrion(self):
        layer_name = "flowPhi"
        field_name = "phi"
        addMultiScalarToMesh(layer_name,field_name,self.n_sediments)

        reloadAndStyleMesh("phi1",self.iface)



def createFlowScalarLayer(layer_name,field_name):
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
    QgsProject.instance().addMapLayer(
        QgsVectorLayer(shp_path, layer_name, "ogr")
    )

    msg=f"{layer_name} flow variable layer created." 
    log_info(msg)
    #QMessageBox.information(None, "DOMAIN", f"Capa domain creada en {shp_path}")


def createFlowMultiScalarLayer(layer_name,field_prefix,nvar):
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

    # Crear campos sed1, sed2, ...
    provider = layer.dataProvider()
    fields = []
    for i in range(1, nvar + 1):
        field_name = f"{field_prefix}{i}"
        fields.append(QgsField(field_name, QVariant.Double))

    provider.addAttributes(fields)
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
        QgsVectorLayer(shp_path, layer_name, "ogr")
    )

    msg=f"{layer_name} flow variable layer created." 
    log_info(msg)
    #QMessageBox.information(None, "DOMAIN", f"Capa domain creada en {shp_path}")


def createFlowVectorLayer(layer_name,field1_name,field2_name):
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
    layer.dataProvider().addAttributes([QgsField(field1_name, QVariant.Double)])
    layer.dataProvider().addAttributes([QgsField(field2_name, QVariant.Double)])
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
        QgsVectorLayer(shp_path, layer_name, "ogr")
    )

    msg=f"{layer_name} flow vector layer created." 
    log_info(msg)
    #QMessageBox.information(None, "DOMAIN", f"Capa domain creada en {shp_path}")


def addFlowScalarToMesh(layer_name,field_name):

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

    msg=f"Flow variable {field_name} added to mesh layer"
    log_info(msg)


def addFlowVectorToMesh(layer_name,field1_name,field2_name):

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
    if field1_name not in [f.name() for f in mesh.fields()]:
        mesh.startEditing()
        mesh.addAttribute(QgsField(field1_name, QVariant.Double))
        mesh.updateFields()
        mesh.commitChanges()

    if field2_name not in [f.name() for f in mesh.fields()]:
        mesh.startEditing()
        mesh.addAttribute(QgsField(field2_name, QVariant.Double))
        mesh.updateFields()
        mesh.commitChanges()        

    # Sample new mesh values
    mesh.startEditing()
    for feat in mesh.getFeatures():
        centroid = feat.geometry().centroid()

        val1 = None
        val2 = None
        for pol in source_polygons:
            if pol.geometry().contains(centroid):
                val1 = pol[field1_name]
                val2 = pol[field2_name]

        if val1 is not None:
            feat[field1_name] = val1
        else:
            feat[field1_name] = 0.0

        if val2 is not None:
            feat[field2_name] = val2
        else:
            feat[field2_name] = 0.0            
        
        mesh.updateFeature(feat)

    mesh.commitChanges()

    msg=f"Flow vector ({field1_name,field2_name}) added to mesh layer"
    log_info(msg)


def addMultiScalarToMesh(layer_name,field_prefix,nvar):

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

    # --- Generate field names: sed1, sed2, ...
    field_names = [f"{field_prefix}{i+1}" for i in range(nvar)]

    # --- Add fields if not present
    mesh.startEditing()
    existing_fields = [f.name() for f in mesh.fields()]
    for fname in field_names:
        if fname not in existing_fields:
            mesh.addAttribute(QgsField(fname, QVariant.Double))
    mesh.updateFields()
    mesh.commitChanges()


    # Sample new mesh values
    mesh.startEditing()
    for feat in mesh.getFeatures():
        centroid = feat.geometry().centroid()

        values = {fname: 0.0 for fname in field_names}

        for pol in source_polygons:
            if pol.geometry().contains(centroid):
                for fname in field_names:
                    values[fname] = pol[fname]
                break

        for fname in field_names:
            feat[fname] = values[fname]

        mesh.updateFeature(feat)

    mesh.commitChanges()

    msg=f"Sediment concentration {field_prefix}{nvar}-component added to mesh layer"
    log_info(msg)


def addFlowScalarToMeshFromRaster(raster,field_name):

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

    msg=f"Flow variable {field_name} sampled to mesh layer from raster"
    log_info(msg)


def addFlowVectorToMeshFromRaster(rasterX,rasterY,field1_name,field2_name):

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
    providerX = rasterX.dataProvider()
    providerY = rasterY.dataProvider()

    # New mesh field
    if field1_name not in [f.name() for f in mesh.fields()]:
        mesh.startEditing()
        mesh.addAttribute(QgsField(field1_name, QVariant.Double))
        mesh.updateFields()
        mesh.commitChanges()

    if field2_name not in [f.name() for f in mesh.fields()]:
        mesh.startEditing()
        mesh.addAttribute(QgsField(field2_name, QVariant.Double))
        mesh.updateFields()
        mesh.commitChanges()

    # Sample new mesh values
    mesh.startEditing()
    for feat in mesh.getFeatures():
        pt = feat.geometry().centroid().asPoint()
        result1 = providerX.sample(pt, 1)
        result2 = providerY.sample(pt, 1)

        if result1[1]:  # ok
            feat[field1_name] = result1[0]
        else:
            feat[field1_name] = 0.0

        if result2[1]:  # ok
            feat[field2_name] = result2[0]
        else:
            feat[field2_name] = 0.0            
        
        mesh.updateFeature(feat)

    mesh.commitChanges()

    msg=f"Flow vector ({field1_name,field2_name}) added to mesh layer from raster"
    log_info(msg)


def reloadAndStyleMesh(var,iface):
    
    tools.remove_layer_by_name("mesh")
    #tools.remove_layer_by_name("mesh_v2")

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


def reloadAndStyleFlow(layer_name,fill_color,edge_color,iface):
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



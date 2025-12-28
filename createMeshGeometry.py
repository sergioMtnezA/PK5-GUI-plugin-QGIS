######################## PeKa2D-v5 Graphical User Interface (GUI) #########################

# PeKa2D-v5 GUI plugin for QGIS 3 
# © 2025 Sergio Martínez-Aranda. License CC BY-NC-SA 4.0 
# To view a copy of this license, visit https://creativecommons.org/licenses/by-nc-sa/4.0/

###########################################################################################

from qgis.PyQt.QtWidgets import QAction, QMessageBox
from qgis.core import QgsProject, QgsVectorLayer, QgsField, QgsFields, QgsVectorFileWriter, QgsMeshLayer, QgsPointXY, QgsFeature, QgsGeometry
from PyQt5.QtCore import QVariant
import os
from .messages import (
    log_info,
    log_error,
    log_warning
)

def defineDomain(mesh_type):
    if mesh_type == "triangle":
        defineDomainPolygonTriangle()
    elif mesh_type == "quad":
        defineDomainPolygonQuad()
    else:
        raise ValueError(f"Tipo de malla no soportado: {mesh_type}")


def defineDomainPolygonTriangle():
    # Obtener carpeta del proyecto
    project_path = QgsProject.instance().fileName()
    if not project_path:
        QMessageBox.critical(None, "Error", "Guarda primero el proyecto")
        return
    project_folder = os.path.dirname(project_path)

    # Tomar CRS del proyecto
    project_crs = QgsProject.instance().crs()        

    # Ruta del shapefile
    shp_path = os.path.join(project_folder, "domain.shp")

    # Crear capa poligonal en memoria con CRS del proyecto
    layer = QgsVectorLayer(f"Polygon?crs={project_crs.authid()}", "domain", "memory")        

    # Añadir campo mesh_size
    layer.dataProvider().addAttributes([QgsField("mesh_size", QVariant.Double)])
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
        QgsVectorLayer(shp_path, "domain", "ogr")
    )

    msg=f"Domain layer created for triangle mesh"    
    log_info(msg)
    #QMessageBox.information(None, "DOMAIN", f"Capa domain creada en {shp_path}")


def defineRefineLines():
   # Obtener carpeta del proyecto
    project_path = QgsProject.instance().fileName()
    if not project_path:
        QMessageBox.critical(None, "Error", "Guarda primero el proyecto")
        return
    project_folder = os.path.dirname(project_path)

    # Tomar CRS del proyecto
    project_crs = QgsProject.instance().crs()        

    # Ruta del shapefile
    shp_path = os.path.join(project_folder, "refineLines.shp")

    # Crear capa poligonal en memoria con CRS del proyecto
    layer = QgsVectorLayer(f"LineString?crs={project_crs.authid()}", "refineLines", "memory")        

    # Añadir campo mesh_size
    layer.dataProvider().addAttributes([QgsField("size_min", QVariant.Double)])
    layer.dataProvider().addAttributes([QgsField("dist_min", QVariant.Double)])
    layer.dataProvider().addAttributes([QgsField("size_max", QVariant.Double)])
    layer.dataProvider().addAttributes([QgsField("dist_max", QVariant.Double)])
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
        QgsVectorLayer(shp_path, "refineLines", "ogr")
    )

    msg=f"Refine layers created for triangle mesh"    
    log_info(msg)
    #QMessageBox.information(None, "REFINELINES", f"Capa refineLines creada en {shp_path}")   


def defineDomainPolygonQuad():
    # Obtener carpeta del proyecto
    project_path = QgsProject.instance().fileName()
    if not project_path:
        QMessageBox.critical(None, "Error", "Guarda primero el proyecto")
        return
    project_folder = os.path.dirname(project_path)

    # Tomar CRS del proyecto
    project_crs = QgsProject.instance().crs()        

    # Ruta del shapefile
    shp_path = os.path.join(project_folder, "domain.shp")

    # Crear capa lineal en memoria con CRS del proyecto
    layer = QgsVectorLayer(f"LineString?crs={project_crs.authid()}", "domain_lines", "memory")

    # Añadir campos number_seg y growth_ratio
    layer.dataProvider().addAttributes([
        QgsField("nseg", QVariant.Double),
        QgsField("gratio", QVariant.Double)
    ])
    layer.updateFields()

    # Opciones para guardar
    options = QgsVectorFileWriter.SaveVectorOptions()
    options.driverName = "ESRI Shapefile"
    options.fileEncoding = "UTF-8"

    # Crear el writer moderno
    writer = QgsVectorFileWriter(
        shp_path, "UTF-8", layer.fields(), layer.wkbType(), layer.crs(), "ESRI Shapefile"
    )

    if writer.hasError() != QgsVectorFileWriter.NoError:
        QMessageBox.critical(None, "Error", f"No se pudo crear {shp_path}")
        return

    # Copiar features existentes (si hubiera)
    for feat in layer.getFeatures():
        writer.addFeature(feat)

    del writer  # cerrar archivo correctamente

    # Cargar capa en QGIS
    QgsProject.instance().addMapLayer(
        QgsVectorLayer(shp_path, "domain", "ogr")
    )
    
    msg=f"Domain layer created for quad mesh"    
    log_info(msg)
    #QMessageBox.information(None, "DOMAIN", f"Capa domain creada en {shp_path}")
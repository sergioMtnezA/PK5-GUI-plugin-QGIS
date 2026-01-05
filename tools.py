######################## PeKa2D-v5 Graphical User Interface (GUI) #########################

# PeKa2D-v5 GUI plugin for QGIS 3
# # © 2025 Sergio Martínez-Aranda. License CC BY-NC-SA 4.0 
# To view a copy of this license, visit https://creativecommons.org/licenses/by-nc-sa/4.0/

###########################################################################################

from qgis.core import (
    QgsProject, QgsVectorLayer, QgsField, QgsVectorFileWriter, QgsPointXY, QgsFeature, QgsGeometry,
    QgsSimpleFillSymbolLayer, QgsFillSymbol, QgsSingleSymbolRenderer, QgsUnitTypes
)
from qgis.PyQt.QtGui import QColor
from PyQt5.QtCore import QVariant
import os
import glob
import time
import meshio


def remove_layer_by_name(layer_name):
    project = QgsProject.instance()
    for layer in project.mapLayers().values():
        if layer.name() == layer_name:
            project.removeMapLayer(layer.id())


def remove_shapefile(shp_path):
    base = os.path.splitext(shp_path)[0]
    for f in glob.glob(base + ".*"):
        os.remove(f)


def wait_for_shapefile(shp_path, timeout=3):
    """Espera hasta que los archivos .shp, .shx y .dbf existan"""
    base = os.path.splitext(shp_path)[0]
    files = [base + ext for ext in (".shp", ".shx", ".dbf")]
    t0 = time.time()
    while time.time() - t0 < timeout:
        if all(os.path.exists(f) for f in files):
            return True
        time.sleep(0.1)  # esperar 100 ms
    return False        


def showMesh(project_crs,msh_path,shp_path):

    remove_layer_by_name(shp_path)

    mesh = meshio.read(msh_path)

    points = mesh.points[:, :2]  # XY
    triangles = mesh.cells_dict.get("triangle", [])
    quads = mesh.cells_dict.get("quad", [])

    shp_layer = QgsVectorLayer(f"Polygon?crs={project_crs.authid()}","temp_mesh","memory")
    pr = shp_layer.dataProvider()
    pr.addAttributes([QgsField("midx", QVariant.Int)])
    shp_layer.updateFields()

    fid = 0 # Memory index
    # --- TRIÁNGULOS ---
    for tri in triangles:
        pts = [QgsPointXY(*points[idx]) for idx in tri]
        feat = QgsFeature()
        feat.setGeometry(QgsGeometry.fromPolygonXY([pts]))
        feat.setAttributes([fid])
        pr.addFeature(feat)
        fid += 1

    # --- QUADS ---
    for quad in quads:
        pts = [QgsPointXY(*points[idx]) for idx in quad]
        feat = QgsFeature()
        feat.setGeometry(QgsGeometry.fromPolygonXY([pts]))
        feat.setAttributes([fid])
        pr.addFeature(feat)
        fid += 1

    QgsVectorFileWriter.writeAsVectorFormat(
        shp_layer,
        shp_path,
        "UTF-8",
        project_crs,
        "ESRI Shapefile"
    )

    # Esperar a que el SHP esté completo
    #if not tools.wait_for_shapefile(shp_path):
    #    raise RuntimeError("Shapefile incompleto (.shp, .shx o .dbf)")    

    mesh_layer = QgsVectorLayer(shp_path, "mesh", "ogr")
    applyMeshStyle(mesh_layer)
    QgsProject.instance().addMapLayer(mesh_layer)


def applyMeshStyle(mesh_layer):
    """
    Aplica estilo:
      - Sin relleno
      - Bordes verdes
    """

    # Crear símbolo base para polígonos
    symbol = QgsFillSymbol.createSimple({})

    # Capa de relleno simple
    fill_layer = QgsSimpleFillSymbolLayer()
    fill_layer.setFillColor(QColor(0, 0, 0, 0))  # Transparente
    fill_layer.setStrokeColor(QColor(245, 245, 245))  # Blanco
    fill_layer.setStrokeWidth(0.2)  # Ancho borde
    fill_layer.setStrokeWidthUnit(QgsUnitTypes.RenderMillimeters)

    symbol.changeSymbolLayer(0, fill_layer)

    # Renderer
    renderer = QgsSingleSymbolRenderer(symbol)
    mesh_layer.setRenderer(renderer)

    # Refrescar
    mesh_layer.triggerRepaint()



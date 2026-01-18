######################## PeKa2D-v5 Graphical User Interface (GUI) #########################

# PeKa2D-v5 GUI plugin for QGIS 3
# # © 2025 Sergio Martínez-Aranda. License CC BY-NC-SA 4.0 
# To view a copy of this license, visit https://creativecommons.org/licenses/by-nc-sa/4.0/

###########################################################################################

from qgis.core import (
    QgsProject, QgsVectorLayer, QgsField, QgsVectorFileWriter, QgsPointXY, QgsFeature, QgsGeometry,
    QgsSimpleFillSymbolLayer, QgsFillSymbol, QgsSingleSymbolRenderer, QgsUnitTypes,
    QgsGraduatedSymbolRenderer, QgsStyle,
    QgsSymbol, QgsRendererRange, QgsClassificationEqualInterval
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


def createSimpleRenderer(fill_color, edge_color, opacity=1.0):

    # Crear símbolo simple con bordes blancos
    if fill_color is not None:
        symbol = QgsFillSymbol.createSimple({
            "color": fill_color,  # Color de relleno (gris claro)
            "outline_color": edge_color,  # Color del borde
            "outline_width": "0.2",  # Ancho del borde
            "style": "solid"  # Estilo sólido
        })

        # Aplicar opacidad
        if opacity < 1.0:
            symbol.setOpacity(opacity)
    else:
        symbol = QgsFillSymbol.createSimple({
            "outline_color": edge_color,  # Color del borde
            "outline_width": "0.2",  # Ancho del borde
            "style": "no"  # Estilo sólido
        })        
    
    # Renderizador de símbolo único
    renderer = QgsSingleSymbolRenderer(symbol)
    
    return renderer



def createGraduatedRenderer(layer, field_name, n_classes=9):

    # Calcular valores min y max del campo
    values = [f[field_name] for f in layer.getFeatures()]
    min_val, max_val = min(values), max(values)

    step = (max_val - min_val) / n_classes
    ranges = []

    # Obtener rampa personalizada
    style = QgsStyle().defaultStyle()
    ramp = style.colorRamp("Turbo")
    if ramp is None:
        ramp = style.colorRamp("Viridis")

    for i in range(n_classes):
        lower = min_val + i*step
        upper = min_val + (i+1)*step

        # Crear símbolo base con bordes blancos
        symbol = QgsFillSymbol.createSimple({
            "outline_color": "255,255,255",   # bordes blancos
            "outline_width": "0.2",
            "color": "255,255,255,0"          # relleno transparente, se sobrescribe
        })

        # Asignar color de la rampa
        symbol.setColor(ramp.color(float(i)/n_classes))

        rng = QgsRendererRange(lower, upper, symbol, f"{lower:.1f}-{upper:.1f}")
        ranges.append(rng)

    renderer = QgsGraduatedSymbolRenderer(field_name, ranges)
    renderer.setMode(QgsGraduatedSymbolRenderer.EqualInterval)

    return renderer


def createContinuousRenderer(layer, field_name, n_classes):
#def createContinuousRenderer(layer, field_name, xml_style_path, ramp_name, n_classes=9):
    # Obtener rampa personalizada
    #ramp = loadColorRampFromXml(xml_style_path, ramp_name)
    style = QgsStyle().defaultStyle()
    ramp = style.colorRamp("Turbo")
    if ramp is None:
        ramp = style.colorRamp("Viridis")

    # Crear símbolo base con bordes blancos
    base_symbol = QgsFillSymbol.createSimple({
        "outline_color": "255,255,255",   # bordes blancos
        "outline_width": "0.2",
        "color": "255,255,255,0"          # relleno transparente, se sobrescribe
    })        

    # Renderer graduado
    renderer = QgsGraduatedSymbolRenderer()
    renderer.setClassAttribute(field_name)
    renderer.setSourceColorRamp(ramp)
    #renderer.setMode(QgsGraduatedSymbolRenderer.EqualInterval)
    renderer.setClassificationMethod(QgsClassificationEqualInterval())
    
    renderer.updateClasses(layer, n_classes)
    renderer.updateSymbols(base_symbol)
    
    return renderer


def loadColorRampFromXml(xml_path, ramp_name):
    """
    Carga una color ramp desde un archivo XML de estilo QGIS
    y la devuelve como QgsColorRamp
    """
    style = QgsStyle()
    ok = style.importXml(xml_path)
    if not ok:
        raise RuntimeError(f"Error loading style XML")

    ramp = style.colorRamp(ramp_name)
    if ramp is None:
        raise RuntimeError(f"Color ramp '{ramp_name}' not found in {xml_path}")

    return ramp

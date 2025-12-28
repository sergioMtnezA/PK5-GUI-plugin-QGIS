######################## PeKa2D-v5 Graphical User Interface (GUI) #########################

# PeKa2D-v5 GUI plugin for QGIS 3
# # © 2025 Sergio Martínez-Aranda. License CC BY-NC-SA 4.0 
# To view a copy of this license, visit https://creativecommons.org/licenses/by-nc-sa/4.0/

###########################################################################################

from qgis.core import QgsProject
import os
import glob
import time

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

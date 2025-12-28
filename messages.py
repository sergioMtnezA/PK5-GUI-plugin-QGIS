######################## PeKa2D-v5 Graphical User Interface (GUI) #########################

# PeKa2D-v5 GUI plugin for QGIS 3 
# © 2025 Sergio Martínez-Aranda. License CC BY-NC-SA 4.0 
# To view a copy of this license, visit https://creativecommons.org/licenses/by-nc-sa/4.0/

###########################################################################################

from qgis.core import QgsMessageLog, Qgis

PLUGIN_TAG = "PeKa2D-v5 GUI"

def log_info(msg):
    QgsMessageLog.logMessage(str(msg), PLUGIN_TAG, Qgis.Info)

def log_warning(msg):
    QgsMessageLog.logMessage(str(msg), PLUGIN_TAG, Qgis.Warning)

def log_error(msg):
    QgsMessageLog.logMessage(str(msg), PLUGIN_TAG, Qgis.Critical)

def log_gmsh(msg_gmsh):
    msg = f"GMSH | {str(msg_gmsh)}"
    QgsMessageLog.logMessage(msg, PLUGIN_TAG, Qgis.Info)
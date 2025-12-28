######################## PeKa2D-v5 Graphical User Interface (GUI) #########################

# PeKa2D-v5 GUI plugin for QGIS 3
# © 2025 Sergio Martínez-Aranda. License CC BY-NC-SA 4.0 
# To view a copy of this license, visit https://creativecommons.org/licenses/by-nc-sa/4.0/

###########################################################################################

def classFactory(iface):
    from .pluginInterface import pluginPK5mesher
    return pluginPK5mesher(iface)

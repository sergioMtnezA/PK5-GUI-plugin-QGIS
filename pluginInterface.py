######################## PeKa2D-v5 Graphical User Interface (GUI) #########################

# PeKa2D-v5 GUI plugin for QGIS 3
# © 2025 Sergio Martínez-Aranda. License CC BY-NC-SA 4.0 
# To view a copy of this license, visit https://creativecommons.org/licenses/by-nc-sa/4.0/

###########################################################################################

from qgis.PyQt.QtWidgets import (
    QAction, QMessageBox, QToolButton, QMenu, QLabel
)
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtCore import QObject
from qgis.core import Qgis

from . import createMeshGeometry
from . import generateMeshElements
from . import defineMeshOrdering
from . import terrainFeatures
from . import tools
from .messages import (
    log_info,
    log_error,
    log_warning
)


class pluginPK5mesher:

    def __init__(self, iface):
        self.iface = iface

        # Crear barra de herramientas propia
        self.toolbar = self.iface.addToolBar("PeKa2D-v5 GUI")
        self.toolbar.setObjectName("PeKa2D-v5 GUI")
       
        # Tipo de malla inicial
        self.mesh_type = "triangle"  # valor por defecto

        msg = f"PeKa2D-v5 Graphical User Interface (GUI)"   
        log_info(msg)
        msg = f"Sergio Martínez-Aranda 2024. License CC BY-NC-SA 4.0\n"    
        log_info(msg)


    def initGui(self):

        ################ Boton tipo de malla
        self.mesh_button = QToolButton()
        if self.mesh_type == "triangle":
            self.mesh_button.setText("TRIANGLE")
        elif self.mesh_type == "quad":
            self.mesh_button.setText("QUAD")
        #self.mesh_button.setIcon(QIcon(":/plugins/myplugin/icon_mesh.svg"))
        self.mesh_button.setPopupMode(QToolButton.MenuButtonPopup)

        # Menu del bottom
        menu = QMenu()

        self.action_mesh_triangle = QAction("Triangle", self.iface.mainWindow())
        self.action_mesh_triangle.triggered.connect(lambda: self.set_mesh_type("triangle"))
        menu.addAction(self.action_mesh_triangle)        

        self.action_mesh_quad = QAction("Quad", self.iface.mainWindow())
        self.action_mesh_quad.triggered.connect(lambda: self.set_mesh_type("quad"))
        menu.addAction(self.action_mesh_quad)

        self.mesh_button.setMenu(menu)
        self.toolbar.addWidget(self.mesh_button)        


        ################ Botón DOMAIN
        self.action_domain = QAction("DOMAIN", self.iface.mainWindow())
        self.action_domain.setToolTip("Crear capa domain con mesh_size")
        self.action_domain.triggered.connect(lambda: createMeshGeometry.defineDomain(self.mesh_type))
        self.toolbar.addAction(self.action_domain)   

        ################ Botón REFINE
        self.action_refine = QAction("REFINE", self.iface.mainWindow())
        self.action_refine.setToolTip("Generate refinement lines")
        self.action_refine.triggered.connect(createMeshGeometry.defineRefineLines) 
        self.toolbar.addAction(self.action_refine)             

        ################ Botón MESHING
        self.action_mallar = QAction("MESHING", self.iface.mainWindow())
        self.action_mallar.setToolTip("Generar malla del dominio")
        self.action_mallar.triggered.connect(lambda: generateMeshElements.generateMesh(self))
        self.toolbar.addAction(self.action_mallar)

        ################ Botón ORDERING
        self.action_ordering = QAction("ORDERING", self.iface.mainWindow())
        self.action_ordering.setToolTip("Optimiza ordenacion de malla")
        self.action_ordering.triggered.connect(lambda: defineMeshOrdering.getMeshConnectivity(self))
        self.toolbar.addAction(self.action_ordering) 
 
        ################ Botón TERRAIN
        self.action_terrain = QAction("TERRAIN", self.iface.mainWindow())
        self.action_terrain.setToolTip("Define layers with the terrain features")
        self.action_terrain.triggered.connect(self.openTerrainDialog)
        self.toolbar.addAction(self.action_terrain)      


    def set_mesh_type(self, mesh_type):
        self.mesh_type = mesh_type

        if self.mesh_type == "triangle":
            self.mesh_button.setText("TRIANGLE")
            self.action_domain.setVisible(True)
            self.action_refine.setVisible(True)
            self.action_mallar.setVisible(True)
        elif self.mesh_type == "quad":
            self.mesh_button.setText("QUAD")
            self.action_domain.setVisible(True)
            self.action_refine.setVisible(False)
            self.action_mallar.setVisible(True)

        tools.remove_layer_by_name("domain")
        tools.remove_layer_by_name("refineLines")
        tools.remove_layer_by_name("mesh")

        msg=f"Selected mesh type: {mesh_type}"    
        log_info(msg)

        label = QLabel(f"PeKa2D-v5 GUI: Selected mesh type: {mesh_type}")
        label.setStyleSheet("QLabel { color: black; padding: 4px; }")
        self.iface.messageBar().pushWidget(
            label,
            level=Qgis.Info,
            duration=2
        )


    def openTerrainDialog(self, checked=False):
        terrainFeatures.openTerrainDialog(self.iface)


    def unload(self):
        if self.toolbar:
            self.iface.mainWindow().removeToolBar(self.toolbar)



######################## PeKa2D-v5 Graphical User Interface (GUI) #########################

# PeKa2D-v5 GUI plugin for QGIS 3 
# © 2025 Sergio Martínez-Aranda. License CC BY-NC-SA 4.0 
# To view a copy of this license, visit https://creativecommons.org/licenses/by-nc-sa/4.0/

###########################################################################################

from qgis.PyQt.QtWidgets import (
    QMessageBox,
    QInputDialog,
    QDialog, QVBoxLayout, QPushButton,
    QCheckBox, QLabel, QLineEdit, QHBoxLayout
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
    QgsStyle,
    QgsEditorWidgetSetup   
)
from qgis.gui import (
    QgsMapLayerComboBox
)
from PyQt5.QtCore import (
    Qt,
    QVariant,
    QSettings
)
from PyQt5.QtWidgets import QSpinBox
from PyQt5.QtGui import QIntValidator
import os
import platform
from . import tools
from .messages import (
    log_info,
    log_error,
    log_warning
)

SETTINGS_GROUP = "gmshMesherPK5/CaseDialog"

def openExportDialog(iface, mesh_type):
    dlg = exportDialog(iface, mesh_type, iface.mainWindow())
    dlg.exec()


class exportDialog(QDialog):

    def __init__(self, iface, mesh_type, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Export PeKa2D-v5 files")
        self.iface = iface
        self.mesh_type = mesh_type
        log_info(mesh_type)
        
        # ==========================
        # Settings
        # ==========================
        self.settings = QSettings()
        self.settings_group = SETTINGS_GROUP

        layout = QVBoxLayout(self)

        # ==========================
        # Case data fields
        # ==========================
        self.case_name = QLineEdit()
        self.Ttotal = QLineEdit()
        self.CFL = QLineEdit()
        self.Tdump = QLineEdit()
        self.Tout = QLineEdit()
        self.nIterInfo = QLineEdit()

        # ---- Load stored values ----
        self.load_settings()

        # ==========================
        # Buttons
        # ==========================
        # Export FED
        btn_create1 = QPushButton("Create DAT case")
        btn_create1.clicked.connect(self.on_export_dat_file)

        # Export DAT-FED
        btn_create2 = QPushButton("Export FED file")
        btn_create2.clicked.connect(self.on_export_fed_file)

        # Export hotstart
        btn_create3 = QPushButton("Export HOTSTART file")
        btn_create3.clicked.connect(self.on_export_hotstart_file)

        # Export OBCP
        btn_create4 = QPushButton("Export OBCP file")
        btn_create4.clicked.connect(self.on_export_obcp_file)

        # ==========================
        # Layout
        # ==========================
        layout.addWidget(QLabel("Case name"))
        layout.addWidget(self.case_name)

        row1 = QHBoxLayout()
        row1.addWidget(QLabel("Ttotal"))
        row1.addWidget(self.Ttotal)
        row1.addWidget(QLabel("CFL"))
        row1.addWidget(self.CFL)
        layout.addLayout(row1)

        row2 = QHBoxLayout()
        row2.addWidget(QLabel("Tout"))
        row2.addWidget(self.Tout)
        row2.addWidget(QLabel("Tdump"))
        row2.addWidget(self.Tdump)
        row2.addWidget(QLabel("nIterInfo"))
        row2.addWidget(self.nIterInfo)
        layout.addLayout(row2)

        layout.addWidget(btn_create1)
        layout.addWidget(btn_create2)
        layout.addWidget(btn_create3)
        layout.addWidget(btn_create4)


    def closeEvent(self, event):
        self.save_settings()
        event.accept()                   


    # Actions
    def load_settings(self):
        self.settings.beginGroup(self.settings_group)

        self.case_name.setText(self.settings.value("case_name", ""))
        self.Ttotal.setText(self.settings.value("Ttotal", ""))
        self.CFL.setText(self.settings.value("CFL", ""))
        self.Tdump.setText(self.settings.value("Tdump", ""))
        self.Tout.setText(self.settings.value("Tout", ""))
        self.nIterInfo.setText(self.settings.value("nIterInfo", ""))

        self.settings.endGroup()


    def save_settings(self):
        self.settings.beginGroup(self.settings_group)

        self.settings.setValue("case_name", self.case_name.text())
        self.settings.setValue("Ttotal", self.Ttotal.text())
        self.settings.setValue("CFL", self.CFL.text())
        self.settings.setValue("Tdump", self.Tdump.text())
        self.settings.setValue("Tout", self.Tout.text())
        self.settings.setValue("nIterInfo", self.nIterInfo.text())

        self.settings.endGroup()        


    def on_export_dat_file(self):
        # Carpeta del proyecto
        project_path = QgsProject.instance().fileName()
        project_folder = os.path.dirname(project_path)

        self.save_settings()
        case_name = self.case_name.text().strip()
        Ttotal = self.Ttotal.text().strip()
        CFL = self.CFL.text().strip()
        Tout = self.Tout.text().strip()
        Tdump = self.Tdump.text().strip()
        nIterInfo = self.nIterInfo.text().strip()

        # Crear carpeta del caso
        case_folder = os.path.join(project_folder, case_name)
        os.makedirs(case_folder, exist_ok=True)

        # Crear archivo DAT
        dat_path = os.path.join(case_folder, f"{case_name}.DAT")  
        createDATfiles(self, dat_path)

        # Crear archivo borrar resultados
        system = platform.system()
        if system == "Windows":
            clear_path = os.path.join(case_folder, f"clean.bat")
        elif system == "Linux":
            clear_path = os.path.join(case_folder, f"clean.sh") 
        createCLEANfiles(system, clear_path)        


    def on_export_fed_file(self):  
        # Carpeta del proyecto
        project_path = QgsProject.instance().fileName()
        project_folder = os.path.dirname(project_path)

        msh_path = os.path.join(project_folder, "mesh.msh")
        shp_path = os.path.join(project_folder, "mesh.shp")

        self.save_settings()
        case_name = self.case_name.text().strip()
        case_folder = os.path.join(project_folder, case_name)
        fed_path = os.path.join(case_folder, f"{case_name}.FED")
        createFEDfile(msh_path, shp_path, fed_path, self.mesh_type)


    def on_export_hotstart_file(self):
        # Carpeta del proyecto
        project_path = QgsProject.instance().fileName()
        project_folder = os.path.dirname(project_path)

        self.save_settings()
        case_name = self.case_name.text().strip()
        case_folder = os.path.join(project_folder, case_name)   
        createHOTSTARTfiles(case_name)


    def on_export_obcp_file(self):
        # Carpeta del proyecto
        project_path = QgsProject.instance().fileName()
        project_folder = os.path.dirname(project_path)

        shp_path = os.path.join(project_folder, "mesh.shp")

        self.save_settings()
        case_name = self.case_name.text()
        case_folder = os.path.join(project_folder, case_name) 
        obcp_path = os.path.join(case_folder, f"{case_name}.OBCP")   
        createOBCPfiles(shp_path, obcp_path)        


def createDATfiles(self, dat_path):
    Ttotal = self.Ttotal.text().strip()
    CFL = self.CFL.text().strip()
    Tout = self.Tout.text().strip()
    Tdump = self.Tdump.text().strip()
    nIterInfo = self.nIterInfo.text().strip()

    try:
        with open(dat_path, "w") as f:
            f.write(f"202407\n") #line 1
            f.write(f"1\n") #line 2
            f.write(f"0 0 0 0 0 0 0 0 0 0 0\n")  #line 3
            f.write(f"1\n")  #line 4
            f.write(f"0 0 0 0 0\n")  #line 5
            f.write(f"{nIterInfo} {CFL} {Tdump} {Tout} {Ttotal}\n")  #line 6
            f.write(f"2 0\n")  #line 7
            f.write(f"0\n")  #line 8
            f.write(f"1.0\n")  #line 9
            f.write(f"1\n")  #line 10
            f.write(f"0\n")  #line 11
            f.write(f"0.001\n")  #line 12
            f.write(f"0\n")  #line 13
            f.write(f"0\n")  #line 14
            f.write(f"0\n")  #line 15
            f.write(f"0\n")  #line 16
            f.write(f"1\n")  #line 17
            f.write(f"0\n")  #line 18
            f.write(f"0 0 0 0 0 0 0 0 0 0\n")  #line 19

        msg=f"Create .DAT case file done." 
        log_info(msg)

    except Exception as e:
        msg=f"Create .DAT case file failed." 
        log_error(msg)


def createCLEANfiles(system, clear_path):
    if system == "Windows":
        clean_cmd = "del"
    elif system == "Linux":
        clean_cmd = "rm"

    try:
        with open(clear_path, "w") as f:
            f.write(f"{clean_cmd} *.vtk\n")
            f.write(f"{clean_cmd} *.out\n")
            f.write(f"{clean_cmd} *.log\n")
            f.write(f"{clean_cmd} *.time\n")
            f.write(f"{clean_cmd} *.error\n")
            f.write(f"#{clean_cmd} *.walls\n")
            f.write(f"{clean_cmd} *.probeData\n")
            f.write(f"{clean_cmd} *.frontData\n")
            f.write(f"{clean_cmd} *.massBalance\n")
            f.write(f"{clean_cmd} hotstart.*\n")
            f.write(f"{clean_cmd} *.WEIRI\n")
            f.write(f"{clean_cmd} *.WEIRE\n")
            f.write(f"{clean_cmd} *.ROUT\n")
            f.write(f"#{clean_cmd} *.HOTSTART\n")

        msg=f"Create clear file done." 
        log_info(msg)

    except Exception as e:
        msg=f"Create clear file failed." 
        log_error(msg)


def createFEDfile(msh_path, shp_path, fed_path, mesh_type):
    nodes = {}      # id -> (x,y)
    cells = []      # [[n1,n2,n3]] Triangle - [[n1,n2,n3,n4]] Quad

    with open(msh_path, "r") as f:
        lines = f.readlines()

    i = 0
    while i < len(lines):
        line = lines[i].strip()

        # ---- NODES ----
        if line == "$Nodes":
            n_nodes = int(lines[i+1].strip())
            i += 2

            for _ in range(n_nodes):
                parts = lines[i].split()
                node_id = int(parts[0])
                x = float(parts[1])
                y = float(parts[2])
                nodes[node_id] = (x, y)
                i += 1

        # ---- ELEMENTS ----
        elif line == "$Elements":
            n_elem = int(lines[i+1].strip())
            i += 2

            for _ in range(n_elem):
                parts = lines[i].split()
                elem_type = int(parts[1])
                ntags = int(parts[2])

                # Triangle
                if mesh_type == "triangle" and elem_type == 2:
                    n1 = int(parts[3 + ntags])
                    n2 = int(parts[4 + ntags])
                    n3 = int(parts[5 + ntags])
                    cells.append([n1, n2, n3])

                # Quad
                elif mesh_type == "quad" and elem_type == 3:
                    n1 = int(parts[3 + ntags])
                    n2 = int(parts[4 + ntags])
                    n3 = int(parts[5 + ntags])
                    n4 = int(parts[6 + ntags])
                    cells.append([n1, n2, n3, n4]) 

                i += 1
        else:
            i += 1

    nvertex = len(nodes)
    ncells = len(cells)
    if mesh_type == "triangle":
        vertexXcell = 3
    elif mesh_type == "quad":
        vertexXcell = 4

    # ---- READ TERRAIN FEATURES ----
    field_name = "zbed"
    zbed = readFieldDataFromLayer(shp_path, field_name)

    field_name = "hini"
    hini = readFieldDataFromLayer(shp_path, field_name)    

    field_name = "nman"
    nman = readFieldDataFromLayer(shp_path, field_name)
    
    # ---- WRITE FED ----
    with open(fed_path, "w") as f:
        # Header
        f.write(f"{ncells} {nvertex} {vertexXcell} 0\n")

        # Nodes (ordenados por ID)
        for node_id in sorted(nodes.keys()):
            x, y = nodes[node_id]
            f.write(
                f"{node_id} {x:.6f} {y:.6f} 0.0 0.0 -9999 0 0\n"
            )

        # Cells
        for i, cell_nodes in enumerate(cells, start=1):
            zb = zbed[i-1]
            wsl = zbed[i-1] + hini[i-1]
            nb = nman[i-1]
            if mesh_type == "triangle":
                n1, n2, n3 = cell_nodes
                f.write(f"{i} {n1} {n2} {n3} {nb:.3f} {zb:.3f} {wsl:.3f} 0.0 0.0\n")
            elif mesh_type == "quad":
                n1, n2, n3, n4 = cell_nodes
                f.write(f"{i} {n1} {n2} {n3} {n4} {nb:.3f} {zb:.3f} {wsl:.3f} 0.0 0.0\n")

    msg=f"Export .FED mesh file done." 
    log_info(msg)


def createHOTSTARTfiles(case_name):

    msg=f"Export {case_name}.HOTSTART initial file done." 
    log_info(msg)


def createOBCPfiles(shp_path, obcp_path):
    # OUTLETS -----------------------------------------------------------
    noutlets = 0
    olayer = None
    for lyr in QgsProject.instance().mapLayers().values():
        if lyr.name() == "Outlets":
            olayer = lyr
            break

    if olayer is None:
        msg=f"No outlets defined in project" 
        log_info(msg)
    else:
        outfeatures = list(olayer.getFeatures())
        noutlets = len(outfeatures)

    # INLETS -----------------------------------------------------------
    ninlets = 0
    ilayer = None
    for lyr in QgsProject.instance().mapLayers().values():
        if lyr.name() == "Inlets":
            ilayer = lyr
            break

    if ilayer is None:
        msg=f"No inlets defined in project" 
        log_info(msg)
    else:
        infeatures = list(ilayer.getFeatures())
        ninlets = len(infeatures)

    #Open mesh layer
    mesh_layer = QgsVectorLayer(shp_path, "mesh_tmp", "ogr")
    if not mesh_layer:
        msg=f"Layer {shp_path} not found."
        log_error(msg)

    # Diccionario {id: QgsPointXY} de nodos
    nodes = {f.id(): f.geometry().asPoint() for f in mesh_layer.getFeatures()}
    node_ids = set(nodes.keys())        

    # Create OBCP file
    with open(obcp_path, "w") as f:
        f.write("202407\n")                 # version
        f.write(f"{noutlets+ninlets}\n")    # nobc

        for feat in outfeatures:
            idname = feat["IDname"]
            type = feat["Type"]
            file = feat["File"]
            f.write(f"{idname}\n")
            f.write(f"{type}\n")
            f.write(f"{file}\n")

        for feat in infeatures:
            idname = feat["IDname"]
            type = feat["Type"]
            file = feat["File"]
            f.write(f"{idname}\n")
            f.write(f"{type}\n")
            f.write(f"{file}\n")

    msg=f"Export .OBCP boundary file done." 
    log_info(msg)


def readFieldDataFromLayer(shp_path, field_name):
    layer = QgsVectorLayer(shp_path, "mesh_tmp", "ogr")
    if not layer:
        msg=f"Layer {shp_path} not found."
        log_error(msg)

    data = []
    for feat in layer.getFeatures():
        value = float(feat[field_name])  
        data.append(value)      

    return data

def getBoundaryNodes(feat, nodes, nodes_ids):
    #Boundary polygon
    poly_geom = feat.geometry()
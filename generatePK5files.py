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
    QgsEditorWidgetSetup,
    QgsFeatureRequest 
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
from collections import defaultdict
from . import tools
from .messages import (
    log_info,
    log_error,
    log_warning
)

SETTINGS_GROUP = "gmshMesherPK5/CaseDialog"

# -------------------------------
# Boundary type dict
# -------------------------------
OUTLET_MAP = {
    "HYD_OUTFLOW_GAUGE": 11,
    "HYD_OUTFLOW_HZ": 12,
    "HYD_OUTFLOW_FREE": 13,
    "HYD_OUTFLOW_FR": 14,
    "HYD_OUTFLOW_NORMAL": 15
}

INLET_MAP = {
    "HYD_INFLOW_Q": 1,
    "HYD_INFLOW_HZ": 2,
    "HYD_INFLOW_QHZ": 3
}

def openExportDialog(iface, mesh_type):
    dlg = exportDialog(iface, mesh_type, iface.mainWindow())
    dlg.exec()


class exportDialog(QDialog):

    def __init__(self, iface, mesh_type, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Export PeKa2D-v5 files")
        self.iface = iface
        self.mesh_type = mesh_type

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
        self.nodes, self.cells = createFEDfile(msh_path, shp_path, fed_path, self.mesh_type)


    def on_export_hotstart_file(self):
        # Carpeta del proyecto
        project_path = QgsProject.instance().fileName()
        project_folder = os.path.dirname(project_path)

        shp_path = os.path.join(project_folder, "mesh.shp")

        self.save_settings()
        case_name = self.case_name.text().strip()
        case_folder = os.path.join(project_folder, case_name)
        hotstart_path = os.path.join(case_folder, f"{case_name}.HOTSTART") 
        createHOTSTARTfiles(shp_path, hotstart_path)


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
                f.write(f"{i} {n1} {n2} {n3} {nb:.3f} {zb:.6f} {wsl:.6f} 0.0 0.0\n")
            elif mesh_type == "quad":
                n1, n2, n3, n4 = cell_nodes
                f.write(f"{i} {n1} {n2} {n3} {n4} {nb:.3f} {zb:.6f} {wsl:.6f} 0.0 0.0\n")

    msg=f"Export .FED mesh file done." 
    log_info(msg)

    return nodes, cells


def createHOTSTARTfiles(shp_path, hotstart_path):

    #number of hydrodynamic variables
    nhydro = 4 

    #number of sediments
    settings = QSettings()
    settings.beginGroup("gmshMesherPK5/InitialDialog")
    n_sediments = settings.value("n_sediments", 1, type=int)
    settings.endGroup()

    #Read available hydrodynamic variables
    layer = QgsVectorLayer(shp_path, "mesh_tmp", "ogr")

    field_name = "zbed"
    if layer.fields().indexOf(field_name) != -1:
        zbed = readFieldDataFromLayer(shp_path, field_name)
    else:
        msg = "Terrain elevation must be added to mesh before exporting .HOTSTART file"
        log_error(msg)

    field_name = "hini"
    if layer.fields().indexOf(field_name) != -1:
        hini = readFieldDataFromLayer(shp_path, field_name)
    else:
        hini = None    

    field_name = "uini"
    if layer.fields().indexOf(field_name) != -1:
        uini = readFieldDataFromLayer(shp_path, field_name)
    else:
        uini = None    

    field_name = "vini"
    if layer.fields().indexOf(field_name) != -1:
        vini = readFieldDataFromLayer(shp_path, field_name)
    else:
        vini = None 

    if n_sediments > 0:
        for i in range(n_sediments):
            field_name = f"phi{i+1}"
            if layer.fields().indexOf(field_name) != -1:
                data = readFieldDataFromLayer(shp_path, field_name)
            else:
                data = None
            # Crear variable phi1, phi2, ...
            globals()[f"phi{i+1}"] = data           

    

    # ---- WRITE FED ----
    with open(hotstart_path, "w") as f:
        # Header
        f.write(f"{nhydro} {n_sediments} 0 0\n")

        # Cells
        for i in range( len(zbed) ): #zbed always exists
            #zbed
            var = zbed
            value = var[i]
            f.write(f"{value:.6f} ")

            #hini
            var = hini
            if var is not None:
                value = var[i]
                f.write(f"{value:.6f} ")
            else:
                f.write("0.0 ")

            #uini
            var = uini
            if var is not None:
                value = var[i]
                f.write(f"{value:.6f} ")
            else:
                f.write("0.0 ")

            #vini
            var = vini
            if var is not None:
                value = var[i]
                f.write(f"{value:.6f} ")
            else:
                f.write("0.0 ")

            #n_sediments phi
            if n_sediments > 0:
                for i in range(n_sediments):
                    var = globals().get(f"phi{i+1}", None)
                    if var is not None:
                        value = var[i]
                        f.write(f"{value:.6f} ")
                    else:
                        f.write("0.0 ")
            
            #EOL
            f.write("\n")

    msg=f"Export .HOTSTART mesh file done." 
    log_info(msg)


def createOBCPfiles(shp_path, obcp_path):
    # OUTLETS -----------------------------------------------------------
    noutlets = 0
    olayer = None
    outfeatures = None
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
    infeatures = None
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

    #Domain boundary nodes
    nodes = globalNodesCoordinates(mesh_layer)
    nodes_on_boundary = globalBoundaryNodes(mesh_layer)
    msg=f"Number of boundary nodes in mesh: {len(nodes_on_boundary)}"
    log_info(msg)

    # Create OBCP file
    with open(obcp_path, "w") as f:
        f.write("202407\n")                 # version
        f.write(f"{noutlets+ninlets}\n")    # nobc

        if outfeatures is not None:
            for bound in outfeatures:
                idname = bound["IDname"]
                f.write(f"{idname}\n")

                #type = bound["Type"]
                type_str = bound["Type"]
                type = OUTLET_MAP.get(type_str, 0)  # convert to int, default 0
                f.write(f"{type}\n")

                file = bound["File"]
                f.write(f"{file}\n")

                bound_nodes = getBoundaryNodes(mesh_layer, nodes, nodes_on_boundary, bound)
                nobcnodes = len(bound_nodes)
                f.write(f"{nobcnodes}\n")
                for nid in bound_nodes:
                    f.write(f"    {nid}\n")

        if infeatures is not None:
            for bound in infeatures:
                idname = bound["IDname"]
                f.write(f"{idname}\n")

                #type = bound["Type"]
                type_str = bound["Type"]
                type = INLET_MAP.get(type_str, 0)  # convert to int, default 0
                f.write(f"{type}\n")

                file = bound["File"]
                f.write(f"{file}\n")

                bound_nodes = getBoundaryNodes(mesh_layer, nodes, nodes_on_boundary, bound)
                nobcnodes = len(bound_nodes)
                f.write(f"{nobcnodes}\n")
                for nid in bound_nodes:
                    f.write(f"    {nid}\n")

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


def globalNodesCoordinates(mesh_layer):
    nodes = {}

    for feat in mesh_layer.getFeatures():
        cell_nodes = [feat["n1"], feat["n2"], feat["n3"]]
        if "n4" in feat.fields().names() and feat["n4"] >= 0:
            cell_nodes.append(feat["n4"])

        # Obtener geometría del polígono
        geom = feat.geometry()
        try:
            ring = geom.asPolygon()[0]  # anillo exterior
        except Exception:
            if geom.isMultipart():
                ring = geom.asMultiPolygon()[0][0]
            else:
                continue

        # Asociar cada nodo con su coordenada
        for i, nid in enumerate(cell_nodes):
            if nid not in nodes and i < len(ring):
                nodes[nid] = ring[i]

    return nodes


def globalBoundaryNodes(mesh_layer):
    edge_count = {}

    for feat in mesh_layer.getFeatures():
        nodes = [feat["n1"], feat["n2"], feat["n3"]]
        if "n4" in feat.fields().names():
            n4 = feat["n4"]
            if n4 >= 0:
                nodes.append(n4)

        # generar aristas
        for i in range(len(nodes)):
            e = tuple(sorted((nodes[i], nodes[(i + 1) % len(nodes)])))
            edge_count[e] = edge_count.get(e, 0) + 1

    # nodos de aristas que aparecen una sola vez → borde
    nodes_on_boundary = set()
    for e, count in edge_count.items():
        if count == 1:
            nodes_on_boundary.update(e)

    return nodes_on_boundary


def getBoundaryNodes(mesh_layer, nodes, global_boundary_nodes, bound):
    #Found cells in boundary polygon
    cells = cellsInBoundaryPolygon(mesh_layer, bound)
    #Get boundary edges from cells
    edges = boundaryEdgesFromCells(cells, global_boundary_nodes)
    #Get edges fully included in the bound
    filtered_edges = filterEdgesByPolygon(edges, nodes, bound) 
    #Get ordered nodes
    ordered_nodes = orderBoundaryNodes(filtered_edges)

    return ordered_nodes


def orderBoundaryNodes(edges):
    graph = defaultdict(list)
    for n1, n2 in edges:
        graph[n1].append(n2)
        graph[n2].append(n1)

    # Buscar extremos (grado 1)
    endpoints = [n for n, neigh in graph.items() if len(neigh) == 1]
    
    # nodo inicial (grado 1 o cualquiera)
    if len(endpoints) >= 1:
        start = endpoints[0]
    else: # caso raro: línea cerrada por error → coger cualquiera
        start = next(iter(graph))
    
    ordered = [start]
    prev = None
    curr = start
    while True:
        neigh = graph[curr]
        nxt = None
        for n in neigh:
            if n != prev:
                nxt = n
                break

        if nxt is None:
            break

        ordered.append(nxt)
        prev, curr = curr, nxt

        # si llegamos a otro extremo → parar
        if len(graph[curr]) == 1:
            break

    return ordered


def filterEdgesByPolygon(edges, nodes, bound):
    polygon_geom= bound.geometry()
    filtered = []

    for n1, n2 in edges:
        p1 = QgsGeometry.fromPointXY(nodes[n1])
        p2 = QgsGeometry.fromPointXY(nodes[n2])

        if polygon_geom.contains(p1) and polygon_geom.contains(p2):
            filtered.append((n1, n2))

    return filtered


def boundaryEdgesFromCells(cells,global_boundary_nodes):
    edge_count = {}

    for feat in cells:
        # crear edges de la celda
        for e in cellNodeEdges(feat):
            edge_count[e] = edge_count.get(e, 0) + 1
        
    # aristas que aparecen SOLO una vez
    boundary_edges = [e for e, c in edge_count.items() if c == 1]

    # filtrar solo las aristas cuyos nodos estén en la frontera global
    boundary_edges = [e for e in boundary_edges if e[0] in global_boundary_nodes and e[1] in global_boundary_nodes]

    return boundary_edges


def cellNodeEdges(feat):
    nodes = [feat["n1"], feat["n2"], feat["n3"]]
    if "n4" in feat.fields().names() and feat["n4"] >= 0:
        nodes.append(feat["n4"])  # agrega el cuarto nodo si es un quad

    edges = []
    for i in range(len(nodes)):
        edges.append(tuple(sorted((nodes[i], nodes[(i + 1) % len(nodes)]))))
    return edges


def cellsInBoundaryPolygon(mesh_layer, bound):
    bound_geom = bound.geometry()
    bbox = bound_geom.boundingBox()

    inside = []
    for feat in mesh_layer.getFeatures(QgsFeatureRequest().setFilterRect(bbox)):        
        if bound_geom.contains(feat.geometry().centroid()):
            inside.append(feat)
    
    return inside


######################## PeKa2D-v5 Graphical User Interface (GUI) #########################

# PeKa2D-v5 GUI plugin for QGIS 3
# © 2025 Sergio Martínez-Aranda. License CC BY-NC-SA 4.0 
# To view a copy of this license, visit https://creativecommons.org/licenses/by-nc-sa/4.0/

###########################################################################################

from qgis.PyQt.QtWidgets import QMessageBox
from qgis.core import QgsProject
import os
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.cm as cm
import math
from collections import defaultdict
from .reorderMatrixMethods import applyRCMreordering
from . import tools
from .messages import (
    log_info,
    log_error,
    log_warning
)

def getMeshConnectivity():

    # Obtener carpeta del proyecto
    project_path = QgsProject.instance().fileName()
    if not project_path:
        QMessageBox.critical(None, "Error", "Guarda primero el proyecto")
        return
    project_folder = os.path.dirname(project_path)

    # Tomar CRS del proyecto
    project_crs = QgsProject.instance().crs()  

    # Read de msh file
    filename = os.path.join(project_folder, "mesh.msh")
    elements,nodes = readGmshFile(filename)
    msg=f"Mesh MSH file read"   
    log_info(msg)
    msg=f"Number of nodes: {len(nodes)}"   
    log_info(msg)       
    msg=f"Number of volume elements: {len(elements)}"   
    log_info(msg)      

    # Compute conectivity matrix
    Cmatrix = computeConnectivityMatrix(elements)
    msg=f"Connectivity matrix created"   
    log_info(msg)

    # Show conectivity matrix      
    output_file = os.path.join(project_folder, "cellConnectivity.png")
    plotConnectivityMatrix(Cmatrix, output_file)
    msg=f"Plot connectivity matrix done"   
    log_info(msg)

    QMessageBox.information(None, "ORDERING", "Mesh connectivity computed\n")  


    # Create calclulus wall list
    neighbors = buildNeighbornCells(elements)
    msg=f"Neighbor cells list created: {len(neighbors)} pairs"  
    log_info(msg)     

    output_file = os.path.join(project_folder, "wallConnectivity.png")
    plotNeighbornConnectivity(neighbors, output_file)
    msg=f"Plot calculus walls connectivity done"  
    log_info(msg)

    QMessageBox.information(None, "ORDERING", "Wall connectivity computed\n")


    # Apply RCM for mesh reordering
    newElements = applyRCMreordering(elements,neighbors)
    msg=f"RCM reordering applied"   
    log_info(msg) 

    newCmatrix = computeConnectivityMatrix(newElements)
    output_file = os.path.join(project_folder, "cellConnectivityReordered.png")
    plotConnectivityMatrix(newCmatrix, output_file)

    newNeighbors = buildNeighbornCells(newElements)
    msg=f"Reordered calculus walls created: {len(newNeighbors)} walls"  
    log_info(msg)         

    output_file = os.path.join(project_folder, "wallConnectivityReordered.png")
    plotNeighbornConnectivity(newNeighbors, output_file) 
    msg=f"Plot reordered calculus walls connectivity done"  
    log_info(msg) 

    msh_path = os.path.join(project_folder, "mesh_v2.msh")
    writeMeshReordered(msh_path, nodes, newElements)
    msg=f"Reordered MSH file written"  
    log_info(msg)  

    # Cargar malla en QGIS
    shp_path = os.path.join(project_folder, "mesh_v2.shp")
    tools.showMesh(project_crs,msh_path,shp_path)      

    QMessageBox.information(None, "ORDERING", "Mesh reordering successful\n") 


def readGmshFile(filename):
    """
    Reads a GMSH .msh file (version 2 ASCII) and returns a list of nodes and elements.
    Only considers 2D elements (triangles and quads).
    """
    elements = []
    nodes = []

    with open(filename, 'r', encoding='latin1') as f:
        lines = f.readlines()
    
    reading_nodes = False
    reading_elements = False
    skip_next = False

    for line in lines:
        line = line.strip()

        # --------------------
        # NODES
        # --------------------
        if line == "$Nodes":
            reading_nodes = True
            skip_next = True  # number of nodes
            continue

        if line == "$EndNodes":
            reading_nodes = False
            continue

        if reading_nodes:
            if skip_next:
                skip_next = False
                continue

            parts = line.split()
            if len(parts) >= 4:
                x = float(parts[1])
                y = float(parts[2])
                nodes.append((x, y))
            continue

        # --------------------
        # ELEMENTS
        # --------------------        
        if line == "$Elements":
            reading_elements = True
            skip_next = True  # next line is the number of elements
            continue

        if line == "$EndElements":
            break

        if reading_elements:
            if skip_next:
                skip_next = False
                continue  # skip number of elements line

            parts = line.split()
            if len(parts) < 4:
                continue

            elem_type = int(parts[1])
            num_tags = int(parts[2])
            node_start = 3 + num_tags
            cell_node = list(map(int, parts[node_start:]))

            # 2D elements only
            if elem_type == 2 and len(cell_node) == 3:      # triangle
                elements.append(cell_node)
            elif elem_type == 3 and len(cell_node) == 4:    # quad
                elements.append(cell_node)

    return elements, nodes


def computeConnectivityMatrix(elements):
    """
    Creates the connectivity matrix from a list of elements.
    Two elements are connected if they share at least 2 nodes (2D side).
    """
    N = len(elements)
    C = np.zeros((N, N), dtype=int)
    for i in range(N):
        for j in range(i+1, N):
            if len(set(elements[i]) & set(elements[j])) >= 2:
                C[j, i] = 1
    return C


def plotConnectivityMatrix(matrix, output_file):
    """
    Saves the connectivity matrix as an image file.
    """
    N = matrix.shape[0]
    #size = max(10, N/100)   # escala automática
    size=10
    plt.figure(figsize=(size, size))

    plt.imshow(
        matrix, 
        cmap='gray_r', 
        origin='lower',
        interpolation='nearest',
        vmin=0,vmax=1
    )

    x0=np.array([0,N-1])
    y0=np.array([0,N-1])
    plt.plot(x0,y0,color='red',linewidth=1)
    
    plt.title("Connectivity Matrix")
    plt.colorbar(label='Connection')
    plt.tight_layout()
    
    plt.savefig(output_file, dpi=300)
    plt.close()  # close the figure to free memory


def buildWalls(elements):
    """
    Build wall list for an unstructured 2D mesh.
    """
    wall_map = []

    for icell, inode in enumerate(elements):
        n = len(inode)  # 3 or 4

        for j in range(n):
            p1 = inode[j]
            p2 = inode[(j + 1) % n]

            # orientation-independent wall
            id1, id2 = sorted((p1, p2))

            wall_map.append({
                "id1": id1, "id2": id2,
                "cell": icell,
                "iwall": j
            })

    return wall_map


def countWalls(wall_map):
    """
    Count interior and boundary walls for a list of walls.
    """
    # Primero agrupamos las paredes por (id1, id2)
    wall_groups = defaultdict(list)
    for w in wall_map:
        wall_groups[(w["id1"], w["id2"])].append(w["cell"])

    n_interior = 0
    n_boundary = 0
    for cells in wall_groups.values():
        if len(cells) == 2:
            n_interior += 1
        elif len(cells) == 1:
            n_boundary += 1

    return n_interior, n_boundary


def buildNeighbornCells(elements):
    """
    Find interior walls and build cell adjacency.
    """
    # Create walls
    walls = buildWalls(elements)
    walls.sort(key=lambda w: (w["id1"], w["id2"])) #ordering by node index
    msg=f"Walls map created: {len(walls)} edges"  
    log_info(msg)

    # Count walls
    ncalc, nbound = countWalls(walls)
    msg=f"Calculus walls {ncalc} - Bound walls {nbound}"  
    log_info(msg)

    # Build neighborn pairs
    neighbors = []
    for i in range(len(walls) - 1):
        w1 = walls[i]
        w2 = walls[i + 1]

        if w1["id1"] == w2["id1"] and w1["id2"] == w2["id2"]:
            calc_wall = {
                "c1": w1["cell"],
                "c2": w2["cell"],
                "iw1": w1["iwall"],
                "iw2": w2["iwall"],
                "n1": w1["id1"],
                "n2": w1["id2"]
            }
            
            neighbors.append(calc_wall)

    # Ordering by cell index
    neighbors.sort(key=lambda n: (n["c1"], n["c2"])) 

    return neighbors


def writeNeighbornCells(neighbors,output_file):
    with open(output_file, "w") as f:
        f.write("n1 n2 c1 c2 iw1 iw2\n")
        
        for w in neighbors:
            f.write(f"{w['n1']} {w['n2']} {w['c1']} {w['c2']} {w['iw1']} {w['iw2']}\n") 
  

def plotNeighbornConnectivity(neighbors, output_file):
    """
    Plot idWall vs cell1 and cell2, coloring points by idWall.
    """
    colormap="jet"
    point_size=12

    idwalls = np.arange(len(neighbors))
    cell1 = np.array([w["c1"] for w in neighbors])
    cell2 = np.array([w["c2"] for w in neighbors])

    norm = plt.Normalize(vmin=idwalls.min(), vmax=idwalls.max())
    cmap = cm.get_cmap(colormap)

    plt.figure(figsize=(10,10))
    plt.scatter(idwalls, cell1, c=idwalls, cmap=cmap, norm=norm, s=point_size, label="cell-1", marker='+',linewidths=0.5)
    plt.scatter(idwalls, cell2, c=idwalls, cmap=cmap, norm=norm, s=point_size, label="cell-2", marker='x',linewidths=0.5)

    plt.xlabel("Wall ID")
    plt.ylabel("Cell index")
    plt.title("Wall ID vs Cells (colored by Wall ID)")
    plt.colorbar(cm.ScalarMappable(norm=norm, cmap=cmap), label="Wall ID")
    plt.legend()
    plt.grid(True)
    plt.tight_layout()

    plt.savefig(output_file, dpi=300)
    plt.close()


def writeMeshReordered(filename, nodes, elements):
    """
    Write a GMSH 2.2 ASCII .msh file

    Parameters
    ----------
    filename : str
    nodes : list of (x, y, z)
    elements : list of list[int]
        Node indices start at 0
    """

    with open(filename, "w", encoding="ascii") as f:

        # --- Mesh format ---
        f.write("$MeshFormat\n")
        f.write("2.2 0 8\n")
        f.write("$EndMeshFormat\n")

        # --- Nodes ---
        f.write("$Nodes\n")
        f.write(f"{len(nodes)}\n")

        for i, (x, y) in enumerate(nodes):
            f.write(f"{i+1} {x:.6f} {y:.6f} 0.0\n")

        f.write("$EndNodes\n")

        # --- Elements ---
        f.write("$Elements\n")
        f.write(f"{len(elements)}\n")

        for i, elem in enumerate(elements):

            if len(elem) == 3:
                elem_type = 2   # triangle
            elif len(elem) == 4:
                elem_type = 3   # quad
            else:
                raise ValueError("Unsupported element type")

            # GMSH minimal tags
            num_tags = 2
            phys_tag = 0
            geom_tag = 1

            nodes_str = " ".join(str(n) for n in elem)

            f.write(
                f"{i+1} {elem_type} {num_tags} {phys_tag} {geom_tag} {nodes_str}\n"
            )

        f.write("$EndElements\n")


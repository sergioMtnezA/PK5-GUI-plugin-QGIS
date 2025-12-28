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

    # Read de msh file
    filename = os.path.join(project_folder, "mesh.msh")
    elements = readGmshFile(filename)
    
    msg=f"Mesh MSH file read"   
    log_info(msg)
    msg=f"Number of volume elements: {len(elements)}"   
    log_info(msg)      

    # Compute conectivity matrix
    Cmatrix = computeConnectivityMatrix(elements)
    
    msg=f"Connectivity matrix created"   
    log_info(msg)

    # Show conectivity matrix      
    output_file = os.path.join(project_folder, "connectivity.png")
    showConnectivityMatrix(Cmatrix, output_file)

    msg=f"Connectivity matrix figure created"   
    log_info(msg)

    QMessageBox.information(None, "ORDERING", "Mesh connectivity computed\n")  



    


def readGmshFile(filename):
    """
    Reads a GMSH .msh file (version 2 ASCII) and returns a list of elements.
    Only considers 2D elements (triangles and quads).
    """
    elements = []
    with open(filename, 'r', encoding='latin1') as f:
        lines = f.readlines()
    
    reading_elements = False
    skip_next = False

    for line in lines:
        line = line.strip()

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
            nodes = list(map(int, parts[node_start:]))

            # 2D elements only
            if elem_type == 2 and len(nodes) == 3:      # triangle
                elements.append(nodes)
            elif elem_type == 3 and len(nodes) == 4:    # quad
                elements.append(nodes)

    return elements


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
                C[i, j] = 1
    return C


def showConnectivityMatrix(matrix, output_file):
    """
    Saves the connectivity matrix as an image file.
    """
    n = matrix.shape[0]
    #size = max(10, n/100)   # escala automática
    size=10
    plt.figure(figsize=(size, size))

    plt.imshow(
        matrix, 
        cmap='gray_r', 
        origin='lower',
        interpolation='nearest',
        vmin=0,vmax=1
    )
    
    plt.title("Connectivity Matrix")
    plt.colorbar(label='Connection')
    plt.tight_layout()
    
    plt.savefig(output_file, dpi=300)
    plt.close()  # close the figure to free memory




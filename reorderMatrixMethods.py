######################## PeKa2D-v5 Graphical User Interface (GUI) #########################

# PeKa2D-v5 GUI plugin for QGIS 3
# © 2025 Sergio Martínez-Aranda. License CC BY-NC-SA 4.0 
# To view a copy of this license, visit https://creativecommons.org/licenses/by-nc-sa/4.0/

###########################################################################################

from qgis.PyQt.QtWidgets import QMessageBox
from qgis.core import QgsProject
import os
import numpy as np
import math
from collections import defaultdict
from scipy.sparse import csr_matrix
from scipy.sparse.csgraph import reverse_cuthill_mckee
from .messages import (
    log_info,
    log_error,
    log_warning
)

def buildCellConnectivityFromNeighbors(neighbors, ncells):
    rows = []
    cols = []

    for n in neighbors:
        i = n["c1"]
        j = n["c2"]

        rows.extend([i, j])
        cols.extend([j, i])

    data = [1] * len(rows)
    A = csr_matrix((data, (rows, cols)), shape=(ncells, ncells))

    return A


def computeRCMpermutation(neighbors, ncells):
    A = buildCellConnectivityFromNeighbors(neighbors, ncells)
   
    perm = reverse_cuthill_mckee(A, symmetric_mode=True)
    inv_perm = perm.argsort()
   
    return perm, inv_perm

def reorderRCMelements(elements, perm):
    return [elements[p] for p in perm]


def reorderRCMneighbors(neighbors, inv_perm):
    new_neighbors = []

    for n in neighbors:
        new_neighbors.append({
            "c1": inv_perm[n["c1"]],
            "c2": inv_perm[n["c2"]],
            "iw1": inv_perm[n["iw1"]],
            "iw2": inv_perm[n["iw2"]],
            "n1": inv_perm[n["n1"]],
            "n2": inv_perm[n["n2"]],
        })

    return new_neighbors


def applyRCMreordering(elements, neighbors):
    # --- RCM ---
    ncells = len(elements)
    perm, inv_perm = computeRCMpermutation(neighbors, ncells)

    # --- reordenar elementos ---
    new_elements = reorderRCMelements(elements, perm)
    # neighbors = reorderRCMneighbors(neighbors, inv_perm)

    return new_elements


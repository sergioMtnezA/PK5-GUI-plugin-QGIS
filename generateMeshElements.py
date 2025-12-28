######################## PeKa2D-v5 Graphical User Interface (GUI) #########################

# PeKa2D-v5 GUI plugin for QGIS 3
# © 2025 Sergio Martínez-Aranda. License CC BY-NC-SA 4.0 
# To view a copy of this license, visit https://creativecommons.org/licenses/by-nc-sa/4.0/

###########################################################################################

from qgis.PyQt.QtWidgets import QAction, QMessageBox
from qgis.PyQt.QtGui import QColor
from qgis.core import (
    QgsProject, QgsVectorLayer, QgsField, QgsFields, QgsVectorFileWriter, QgsMeshLayer, QgsPointXY, QgsFeature, QgsGeometry,
    QgsSimpleFillSymbolLayer, QgsFillSymbol, QgsSingleSymbolRenderer, QgsUnitTypes,
    QgsMessageLog, Qgis
)
from PyQt5.QtCore import QVariant
import os
import subprocess
import meshio
from . import tools
from .messages import (
    log_info,
    log_error,
    log_warning,
    log_gmsh
)


def generateMesh(mesh_type):
    # Carpeta del proyecto
    project_path = QgsProject.instance().fileName()
    project_folder = os.path.dirname(project_path)
    geo_path = os.path.join(project_folder, "mesh.geo")

    # Generar domain en geo 
    dom_layer = QgsProject.instance().mapLayersByName("domain")
    if not dom_layer:
        msg=f"Domain layer not found"    
        log_error(msg)
        QMessageBox.critical(None, "Error", "Domain layer not found")
        return

    domain = dom_layer[0]
    if domain.featureCount() == 0:
        msg=f"Domain layer is empty"    
        log_error(msg)
        QMessageBox.critical(None, "Error", "Domain layer is empty")
        return  
    
    if mesh_type == "triangle":
        generateDomainTriangleGeo(domain, geo_path)

        msg=f"Domain GEO file created for triangle mesh"   
        log_info(msg)

        rlines_layer = QgsProject.instance().mapLayersByName("refineLines")
        if rlines_layer:
            rlines = rlines_layer[0]
            if rlines.featureCount() == 0:
                msg=f"Refine lines layer is empty"    
                log_warning(msg)
                #QMessageBox.critical(None, "Error", "La capa 'refineLines' está vacía")
                #return  
        
            addRefineLinesGeo(rlines, geo_path)
            msg=f"Refinement features added to GEO file for triangle mesh"    
            log_info(msg)   

    elif mesh_type == "quad":
        generateDomainQuadGeo(domain, geo_path)
        
        msg=f"Domain GEO file created for quad mesh"   
        log_info(msg)

    else:
        msg=f"Non supported mesh type: {mesh_type}"   
        log_error(msg)
        raise ValueError(f"Non supported mesh type: {mesh_type}")    
    

    # Ejecutar Gmsh
    msh_path = os.path.join(project_folder, "mesh.msh")
    generateMeshFromGeo(geo_path, msh_path)

    msg=f"Mesh MSH file generated correctly"   
    log_info(msg)   
    QMessageBox.information(None, "MESHING", "Mesh MSH file generated correctly")
    
    # Cargar malla en QGIS
    shp_path = os.path.join(project_folder, "mesh.shp")
    showMesh(domain,msh_path,shp_path)
    
    msg=f"Mesh layer added to project"   
    log_info(msg)     


def generateDomainTriangleGeo(domain, geo_path):
    """
    Genera un archivo .geo a partir de la capa domain triangle
    Soporta Polygon y MultiPolygon
    Usa mesh_size por polígono
    """
    with open(geo_path, "w") as f:
        f.write("// Peka2D-v5 mesh geofile for GMSH \n")
        f.write("// TRIANGLE mesh topology \n\n")

        point_id = 1
        line_id = 1
        loop_id = 1
        surface_id = 1

        for feat in domain.getFeatures():
            geom = feat.geometry()
            mesh_size = feat["mesh_size"]

            # Determinar si es Polygon o MultiPolygon
            if geom.isMultipart():
                polygons = geom.asMultiPolygon()
            else:
                polygons = [geom.asPolygon()]

            for poly in polygons:
                if not poly:
                    continue
        
                # --- PUNTOS ---
                ring = poly[0]  # anillo exterior
                point_ids = []
                for i,p in enumerate(ring):
                    if i == len(ring) - 1 and p == ring[0]:
                        continue
                    f.write(f"Point({point_id}) = {{{p.x()}, {p.y()}, 0, {mesh_size}}};\n")
                    point_ids.append(point_id)
                    point_id += 1

                # --- LÍNEAS ---
                line_ids = []
                n = len(point_ids)
                for i in range(n):
                    start = point_ids[i]
                    end = point_ids[(i + 1) % n]  # cerrar automáticamente
                    f.write(f"Line({line_id}) = {{{start},{end}}};\n")
                    line_ids.append(line_id)
                    line_id += 1

                # --- SUPERFICIE ---
                f.write(f"Line Loop({loop_id}) = {{{','.join(map(str, line_ids))}}};\n")
                f.write(f"Plane Surface({surface_id}) = {{{loop_id}}};\n\n")

                loop_id += 1
                surface_id += 1


                
def addRefineLinesGeo(refineLines,geo_path):
    """
    Añade refinamiento por líneas leyendo parámetros desde atributos QGIS

    Campos requeridos en la capa:
      - size_min
      - size_max
      - dist_min
      - dist_max
    """

    pid = 10000
    lid = 10000
    fid = 1

    threshold_fields = []

    with open(geo_path, "a") as f:
        f.write("\n// --- REFINAMIENTO POR LÍNEAS (ATRIBUTOS) ---\n")

        for feat in refineLines.getFeatures():
            geom = feat.geometry()

            try:
                size_min = float(feat["size_min"])
                dist_min = float(feat["dist_min"])
                size_max = float(feat["size_max"])
                dist_max = float(feat["dist_max"])
            except Exception:
                continue  # feature mal definida

            if geom.isMultipart():
                lines = geom.asMultiPolyline()
            else:
                lines = [geom.asPolyline()]

            curve_ids = []

            for line in lines:
                if len(line) < 2:
                    continue

                pids = []

                # ---- PUNTOS ----
                for p in line:
                    f.write(
                        f"Point({pid}) = {{{p.x()}, {p.y()}, 0, 1.0}};\n"
                    )
                    pids.append(pid)
                    pid += 1

                # ---- SEGMENTOS ----
                for i in range(len(pids) - 1):
                    f.write(
                        f"Line({lid}) = {{{pids[i]}, {pids[i+1]}}};\n"
                    )
                    curve_ids.append(lid)
                    lid += 1

            if not curve_ids:
                continue

            # ---- FIELD DISTANCE ----
            f.write(f"""
                Field[{fid}] = Distance;
                Field[{fid}].CurvesList = {{{','.join(map(str, curve_ids))}}};
                """)

            # ---- FIELD THRESHOLD ----
            f.write(f"""
                Field[{fid + 1}] = Threshold;
                Field[{fid + 1}].InField = {fid};
                Field[{fid + 1}].SizeMin = {size_min};
                Field[{fid + 1}].SizeMax = {size_max};
                Field[{fid + 1}].DistMin = {dist_min};
                Field[{fid + 1}].DistMax = {dist_max};
                """)

            threshold_fields.append(fid + 1)
            fid += 2

        # ---- COMBINAR TODOS LOS REFINAMIENTOS ----
        if threshold_fields:
            f.write(f"""
                Field[{fid}] = Min;
                Field[{fid}].FieldsList = {{{','.join(map(str, threshold_fields))}}};
                Background Field = {fid};
                """)



def generateDomainQuadGeo(domain, geo_path):
    """
    Genera un archivo .geo a partir de la capa domain quad
    """
    with open(geo_path, "w") as f:
        f.write("// Peka2D-v5 mesh geofile for GMSH\n")
        f.write("// QUAD mesh topology \n\n")

        point_id = 1
        line_id = 1
        loop_id = 1
        surface_id = 1

        all_point_coords = []
        line_point_ids = []

        # Crear puntos y líneas
        for feat in domain.getFeatures():
            geom = feat.geometry()
            ns = feat["nseg"] if feat["nseg"] else 1
            gr = feat["gratio"] if feat["gratio"] else 1.0

            if geom.isMultipart():
                polylines = geom.asMultiPolyline()
            else:
                polylines = [geom.asPolyline()]

            for polyline in polylines:
                if len(polyline) < 2:
                    continue

                current_line_ids = []
                for i in range(len(polyline)):
                    p = polyline[i]

                    # Verificar si el punto ya existe (misma coordenada)
                    tol = 1e-6
                    found = False
                    for idx, coord in enumerate(all_point_coords):
                        if abs(coord[0]-p.x()) < tol and abs(coord[1]-p.y()) < tol:
                            pid = idx + 1
                            found = True
                            break
                    if not found:
                        f.write(f"Point({point_id}) = {{{p.x()}, {p.y()}, 0, {gr}}};\n")
                        all_point_coords.append((p.x(), p.y()))
                        pid = point_id
                        point_id += 1

                    current_line_ids.append(pid)

                # Crear línea(s) de esta feature
                for i in range(len(current_line_ids)-1):
                    start = current_line_ids[i]
                    end = current_line_ids[i+1]
                    f.write(f"Line({line_id}) = {{{start},{end}}};\n")
                    f.write(f"Transfinite Line {{ {line_id} }} = {ns} Using Progression {gr};\n")
                    line_point_ids.append(line_id)
                    line_id += 1

        # Crear Line Loop y Plane Surface
        f.write(f"Line Loop({loop_id}) = {{{','.join(map(str, line_point_ids))}}};\n")
        f.write(f"Plane Surface({surface_id}) = {{{loop_id}}};\n")

        f.write(f"Transfinite Surface {{ {surface_id} }};\n")
        f.write(f"Recombine Surface {{ {surface_id} }};\n\n")


def generateMeshFromGeo(geo_path, msh_path):
    gmsh_exe = r"C:\Users\marti\Documents\gmsh\gmsh.exe"
    cmd = [
        gmsh_exe, 
        geo_path, 
        "-2", 
        "-format", "msh2",
        "-o", msh_path
    ]          

    process = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        bufsize=1
    )

    #stdout, stderr = process.communicate()
    #if stdout:
    #    QgsMessageLog.logMessage(stdout, "Gmsh", Qgis.Info)
    #if stderr:
    #    QgsMessageLog.logMessage(stderr, "Gmsh", Qgis.Critical)

    for line in process.stdout:
        #QgsMessageLog.logMessage(line.rstrip(),"Gmsh",Qgis.Info)
        msg=line.rstrip()    
        log_gmsh(msg)        
    process.wait() 

    for line in process.stderr:
        #QgsMessageLog.logMessage(line.rstrip(),"Gmsh",Qgis.Info)
        msg=line.rstrip()    
        log_gmsh(msg)         
    process.wait()  

    if process.returncode != 0:
        raise RuntimeError("Gmsh fails. Check log file")      



def showMesh(layer,msh_path,shp_path):

    tools.remove_layer_by_name("mesh")

    mesh = meshio.read(msh_path)

    points = mesh.points[:, :2]  # XY
    triangles = mesh.cells_dict.get("triangle", [])
    quads = mesh.cells_dict.get("quad", [])

    shp_layer = QgsVectorLayer(f"Polygon?crs={layer.crs().authid()}","temp_mesh","memory")
    pr = shp_layer.dataProvider()
    pr.addAttributes([QgsField("id", QVariant.Int)])
    shp_layer.updateFields()

    fid = 1
    # --- TRIÁNGULOS ---
    for tri in triangles:
        pts = [QgsPointXY(*points[idx]) for idx in tri]
        feat = QgsFeature()
        feat.setGeometry(QgsGeometry.fromPolygonXY([pts]))
        feat.setAttributes([fid])
        pr.addFeature(feat)
        fid += 1

    # --- QUADS ---
    for quad in quads:
        pts = [QgsPointXY(*points[idx]) for idx in quad]
        feat = QgsFeature()
        feat.setGeometry(QgsGeometry.fromPolygonXY([pts]))
        feat.setAttributes([fid])
        pr.addFeature(feat)
        fid += 1

    QgsVectorFileWriter.writeAsVectorFormat(
        shp_layer,
        shp_path,
        "UTF-8",
        layer.crs(),
        "ESRI Shapefile"
    )

    # Esperar a que el SHP esté completo
    #if not tools.wait_for_shapefile(shp_path):
    #    raise RuntimeError("Shapefile incompleto (.shp, .shx o .dbf)")    

    mesh_layer = QgsVectorLayer(shp_path, "mesh", "ogr")
    applyMeshStyle(mesh_layer)
    QgsProject.instance().addMapLayer(mesh_layer)


def applyMeshStyle(mesh_layer):
    """
    Aplica estilo:
      - Sin relleno
      - Bordes verdes
    """

    # Crear símbolo base para polígonos
    symbol = QgsFillSymbol.createSimple({})

    # Capa de relleno simple
    fill_layer = QgsSimpleFillSymbolLayer()
    fill_layer.setFillColor(QColor(0, 0, 0, 0))  # Transparente
    fill_layer.setStrokeColor(QColor(245, 245, 245))  # Blanco
    fill_layer.setStrokeWidth(0.2)  # Ancho borde
    fill_layer.setStrokeWidthUnit(QgsUnitTypes.RenderMillimeters)

    symbol.changeSymbolLayer(0, fill_layer)

    # Renderer
    renderer = QgsSingleSymbolRenderer(symbol)
    mesh_layer.setRenderer(renderer)

    # Refrescar
    mesh_layer.triggerRepaint()





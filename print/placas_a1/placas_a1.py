"""Orienta las piezas del ODM v2 para imprimir y las arma en placas para la cama de 256 x 256 del A1.

Orientación: prueba como base las 10 caras planas más grandes y la orientación original, y elige la
que deja menos voladizo (caras con más de 45° hacia abajo fuera de la cama) menos un 20 % del área
apoyada; si empatan, la más baja.
Uso: python placas_a1.py <carpeta print/> <carpeta salida>
"""
import os
import sys

import numpy as np
import trimesh
from PIL import Image, ImageDraw
from scipy.spatial import ConvexHull

ESC = 2.0          # px por mm en la imagen
COLORES = [(230, 159, 0), (86, 180, 233), (0, 158, 115), (213, 94, 0), (204, 121, 167),
           (0, 114, 178), (240, 228, 66), (120, 120, 120)]

CAMA = 256.0
MARGEN = 12.0      # borde libre de la cama
SEP = 8.0          # separación entre piezas

PLACAS = {
    "1_cuello": {"head_roll_mount": 1, "head_yaw_to_roll": 1, "head_pitch_to_yaw": 1,
                 "neck_left_sheet": 1, "neck_right_sheet": 1},
    "2_tronco": {"trunk_bottom": 1, "trunk_top": 1},
    "3_caderas": {"roll_motor_bottom": 2, "roll_motor_top": 2, "left_roll_to_pitch": 1,
                  "right_roll_to_pitch": 1, "leg_spacer": 4},
    "4_rodillas": {"knee_to_ankle_left_sheet": 4, "knee_to_ankle_right_sheet": 4},
    "5_pies": {"foot_top": 2, "foot_side": 2, "foot_bottom_pla": 2},
    "6_suelas_tpu": {"foot_bottom_tpu": 2},
    "7_tapas_rodilla": {"left_cache": 1, "right_cache": 1},
}


def puntaje(m):
    fn, c, a = m.face_normals, m.triangles_center, m.area_faces
    apoyo = a[(fn[:, 2] < -0.99) & (c[:, 2] < 0.05)].sum()
    voladizo = a[(fn[:, 2] < -0.7071) & (c[:, 2] > 0.3)].sum()
    return voladizo, apoyo


def orientar(m):
    normales = [m.facets_normal[i] for i in np.argsort(m.facets_area)[::-1][:10]]
    normales.append(np.array([0.0, 0.0, -1.0]))
    mejor = None
    for n in normales:
        mm = m.copy()
        mm.apply_transform(trimesh.geometry.align_vectors(n, [0.0, 0.0, -1.0]))
        mm.apply_translation(-mm.bounds[0])
        vol, apo = puntaje(mm)
        clave = (vol - 0.2 * apo, mm.extents[2])
        if mejor is None or clave < mejor[0]:
            mejor = (clave, mm, vol, apo)
    _, mm, vol, apo = mejor
    # girar en Z para que la huella quede alineada con los ejes (rectángulo mínimo)
    xy = mm.vertices[:, :2]
    hull = xy[ConvexHull(xy).vertices]
    mejor_ang, mejor_area = 0.0, None
    for i in range(len(hull)):
        e = hull[(i + 1) % len(hull)] - hull[i]
        ang = -np.arctan2(e[1], e[0])
        r = np.array([[np.cos(ang), -np.sin(ang)], [np.sin(ang), np.cos(ang)]])
        p = hull @ r.T
        area = np.ptp(p[:, 0]) * np.ptp(p[:, 1])
        if mejor_area is None or area < mejor_area:
            mejor_ang, mejor_area = ang, area
    mm.apply_transform(trimesh.transformations.rotation_matrix(mejor_ang, [0, 0, 1]))
    if mm.extents[0] < mm.extents[1]:
        mm.apply_transform(trimesh.transformations.rotation_matrix(np.pi / 2, [0, 0, 1]))
    mm.apply_translation(-mm.bounds[0])
    return mm, vol, apo


def armar(piezas):
    """Estantes: de mayor a menor profundidad, izquierda a derecha."""
    piezas = sorted(piezas, key=lambda p: -p[1].extents[1])
    util = CAMA - 2 * MARGEN
    x = y = 0.0
    alto_estante = 0.0
    colocadas = []
    for nombre, m in piezas:
        w, d = m.extents[0], m.extents[1]
        if x > 0 and x + w > util:
            x, y = 0.0, y + alto_estante + SEP
            alto_estante = 0.0
        mm = m.copy()
        mm.apply_translation([x, y, 0.0])
        colocadas.append((nombre, mm))
        x += w + SEP
        alto_estante = max(alto_estante, d)
    todo = trimesh.util.concatenate([m for _, m in colocadas])
    # centrar en la cama
    centro = (todo.bounds[0][:2] + todo.bounds[1][:2]) / 2
    mover = [CAMA / 2 - centro[0], CAMA / 2 - centro[1], 0.0]
    for _, m in colocadas:
        m.apply_translation(mover)
    todo.apply_translation(mover)
    return colocadas, todo


def main(carpeta, salida):
    os.makedirs(salida, exist_ok=True)
    lado = int(CAMA * ESC) + 40
    lienzo = Image.new("RGB", (4 * lado, 2 * lado), "white")
    for k, (placa, contenido) in enumerate(PLACAS.items()):
        piezas = []
        for nombre, cant in contenido.items():
            m, vol, apo = orientar(trimesh.load(os.path.join(carpeta, nombre + ".stl")))
            print(f"  {nombre:26s} {m.extents[0]:5.1f} x {m.extents[1]:5.1f} x {m.extents[2]:5.1f}"
                  f"  apoyo {apo:5.0f} mm2  voladizo {vol:5.0f} mm2")
            piezas += [(nombre if cant == 1 else f"{nombre}#{i + 1}", m) for i in range(cant)]
        colocadas, todo = armar(piezas)
        lo, hi = todo.bounds
        entra = lo[0] >= 0 and lo[1] >= 0 and hi[0] <= CAMA and hi[1] <= CAMA
        print(f"{placa}: {len(colocadas)} piezas, huella {hi[0]-lo[0]:.0f} x {hi[1]-lo[1]:.0f} mm,"
              f" alto {hi[2]:.0f} mm, entra={entra}, vol {todo.volume/1000:.0f} cm3")
        todo.export(os.path.join(salida, placa + ".stl"))
        ox, oy = (k % 4) * lado + 20, (k // 4) * lado + 30
        d = ImageDraw.Draw(lienzo)

        def px(p):
            return (ox + p[0] * ESC, oy + (CAMA - p[1]) * ESC)

        d.rectangle([px((0, CAMA)), px((CAMA, 0))], outline="black", width=2)
        d.text((ox, oy - 22), f"{placa}  (alto {hi[2]:.0f} mm)", fill="black")
        for i, (nombre, m) in enumerate(colocadas):
            xy = m.vertices[:, :2]
            h = xy[ConvexHull(xy).vertices]
            d.polygon([px(p) for p in h], fill=COLORES[i % len(COLORES)], outline="black")
            cx, cy = px(h.mean(axis=0))
            d.text((cx - 30, cy - 6), f"{nombre[:14]}\n{m.extents[2]:.0f} mm", fill="black")
    lienzo.save(os.path.join(salida, "placas.png"))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])

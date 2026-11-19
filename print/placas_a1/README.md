# Placas para la Bambu Lab A1

Las piezas del cuerpo del Open Duck Mini v2 que están en [`print/`](..), orientadas para imprimir y
acomodadas en placas para la cama de 256 × 256 mm de la A1. Cada STL es una placa completa, lista para
laminar.

| Placa | Piezas | Material |
|---|---|---|
| `1_cuello.stl` | `head_roll_mount`, `head_yaw_to_roll`, `head_pitch_to_yaw`, `neck_left_sheet`, `neck_right_sheet` | PLA |
| `2_tronco.stl` | `trunk_bottom`, `trunk_top` | PLA |
| `3_caderas.stl` | 2 `roll_motor_bottom`, 2 `roll_motor_top`, `left_roll_to_pitch`, `right_roll_to_pitch`, 4 `leg_spacer` | PLA |
| `4_rodillas.stl` | 4 `knee_to_ankle_left_sheet`, 4 `knee_to_ankle_right_sheet` | PLA |
| `5_pies.stl` | 2 `foot_top`, 2 `foot_side`, 2 `foot_bottom_pla` | PLA |
| `6_suelas_tpu.stl` | 2 `foot_bottom_tpu` | TPU |
| `7_tapas_rodilla.stl` | `left_cache`, `right_cache` | PLA |

Faltan a propósito la cabeza (con las antenas, los ojos, el proyector y el parlante) y la carcasa del
cuerpo (`body_*` y `battery_pack_lid`), porque en este robot se reemplazan.

Relleno según [`docs/print_guide.md`](../../docs/print_guide.md): 15 % en PLA y 40 % en TPU. Conviene
laminar con soportes en árbol (la pieza con más voladizo es `trunk_top`) y con brim de 5 mm alrededor de
cada pieza (`brim_type` en `outer_only`). El brim automático de Bambu casi no agrega nada en PLA, y la
placa de caderas se despegó en la capa 6: ocho de sus piezas miden ~30 mm de alto y apoyan 186–269 mm².
Si igual se levantan los bordes, lavá la placa con agua y detergente y bajá la primera capa a 30 mm/s.

`placas.png` muestra las placas vistas desde arriba, con la altura de cada pieza en mm.

## Cómo se generan

`placas_a1.py` prueba como base de cada pieza sus 10 caras planas más grandes y la orientación original.
Se queda con la que deja menos voladizo (caras inclinadas más de 45° hacia abajo que no tocan la cama),
con un pequeño premio por el área apoyada. Después gira cada pieza para que ocupe el menor rectángulo
posible y las acomoda en filas, con 12 mm de borde y 8 mm entre piezas.

Las tapas de rodilla (`left_cache`, `right_cache`) se orientan a mano, con `BASE_FIJA`. Con el puntaje
quedaban paradas: 153 mm de alto y la primera capa sin tocar la cama. Acostadas sobre la cara exterior
plana apoyan 6250 mm² y miden 40 mm de alto.

Para regenerarlas, desde esta carpeta:

```bash
pip install trimesh scipy pillow
python placas_a1.py .. .
```

Son las mismas piezas de `print/`, con la licencia del repo (Apache-2.0).

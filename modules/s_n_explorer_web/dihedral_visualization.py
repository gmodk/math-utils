"""Authoritative geometry for the existing engine's dihedral permutations.

Coordinate convention: vertex i has (x,z)=(sin(2πi/n),cos(2πi/n));
the SVG uses (x,-z), preserving the original clockwise polygon ordering.
The prism uses +y as its vertical axis. No group operations live in JS.
"""
from math import cos, sin, pi, sqrt

GREEK = list("αβγδεζηθικλμνξοπρστυφχψω")
NAMES = {
    3: ("Triangle", "Triangular prism"), 4: ("Square", "Cube / square prism"),
    5: ("Pentagon", "Pentagonal prism"), 6: ("Hexagon", "Hexagonal prism"),
    7: ("Heptagon", "Heptagonal prism"), 8: ("Octagon", "Octagonal prism"),
    9: ("Nonagon", "Nonagonal prism"), 10: ("Decagon", "Decagonal prism"),
    11: ("Hendecagon", "Hendecagonal prism"), 12: ("Dodecagon", "Dodecagonal prism"),
}


def geometry(n):
    """Regular unit-circumradius prism, with an actual cube at n=4."""
    height = sqrt(2) if n == 4 else 1.25
    ring = [[sin(2*pi*i/n), cos(2*pi*i/n)] for i in range(n)]
    vertices = [[x, y, z] for y in (height/2, -height/2) for x, z in ring]
    faces = [list(range(n-1, -1, -1)), list(range(n, 2*n))]
    faces += [[i, (i+1) % n, (i+1) % n+n, i+n] for i in range(n)]
    edges = [[i, (i+1) % n] for i in range(n)]
    edges += [[i+n, (i+1) % n+n] for i in range(n)] + [[i, i+n] for i in range(n)]
    return {"polygon": [[x, -z] for x, z in ring], "prism_vertices": vertices,
            "faces": faces, "edges": edges, "height": height,
            "labels": {"numbers": [str(i+1) for i in range(n)], "greek": GREEK[:n]},
            "vertex_classes": [{"index": i, "pair": [i, i+n]} for i in range(n)],
            "names": dict(zip(("polygon", "prism"), NAMES.get(n, (f"{n}-gon", f"{n}-gonal prism"))))}


def animation_metadata(item, n, k):
    """Derive targets from the engine's permutation, and axes from its convention.

    sr^k(i)=-i-k. Reflection of polar angle φ about α gives 2α-φ,
    hence α=-πk/n modulo π, measured from +z towards +x.
    """
    shape = geometry(n)
    p = item["permutation"]
    rotation = item["type"] == "rotation"
    angle = 2*pi*k/n if rotation else pi
    alpha = None if rotation else -pi*k/n
    axis = [0, 1, 0] if rotation else [sin(alpha), 0, cos(alpha)]
    prism_p = [p[i] + (layer if rotation else n-layer) for layer in (0, n) for i in range(n)]
    formula = ("e = r^0" if k == 0 else f"r^{k}") if rotation else f"s r^{k}"
    description = (f"Rotation by {360*k/n:g}° about the vertical axis." if rotation else
                   f"Reflection axis {(-180*k/n):g}° from vertex 1's radial direction (mod 180°); prism: 180° horizontal half-turn.")
    return {"k": k, "formula": formula, "angle_rad": angle,
            "rotation_angle_rad": angle if rotation else None,
            "axis_angle_rad": alpha, "axis_vector": axis,
            "description": description,
            "polygon_targets": [shape["polygon"][j] for j in p],
            "prism_permutation": prism_p,
            "prism_targets": [shape["prism_vertices"][j] for j in prism_p]}

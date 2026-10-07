#!/usr/bin/env python3
"""Auditoría: compara las figuras versionadas con las regeneradas por make_all_figures.py.

Renderiza la primera página de cada PDF a 150 dpi y compara píxel a píxel y el texto incrustado.
Requiere PyMuPDF y Pillow.

Solo lectura sobre ambas carpetas.
Uso:  python 09_compare_figures.py <carpeta_figuras_versionadas> <carpeta_figuras_regeneradas>"""
import sys
from pathlib import Path

import numpy as np
import pymupdf
from PIL import Image


def render(path: Path):
    page = pymupdf.open(path)[0]
    pm = page.get_pixmap(dpi=150)
    return Image.frombytes("RGB", (pm.width, pm.height), pm.samples), page.get_text().split()


def main() -> None:
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    old, new = Path(sys.argv[1]), Path(sys.argv[2])
    for f in sorted(old.glob("*.pdf")):
        g = new / f.name
        if not g.exists():
            print(f"{f.name:40s} NO REGENERADA")
            continue
        (i1, t1), (i2, t2) = render(f), render(g)
        if i1.size != i2.size:
            print(f"{f.name:40s} tamaño distinto {i1.size} vs {i2.size}")
            continue
        diff = np.abs(np.asarray(i1, dtype=int) - np.asarray(i2, dtype=int)).max(axis=2)
        print(f"{f.name:40s} píxeles distintos {100 * float((diff > 24).mean()):.3f}% | texto idéntico {t1 == t2}")


if __name__ == "__main__":
    main()

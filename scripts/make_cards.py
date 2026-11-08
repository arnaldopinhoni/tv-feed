#!/usr/bin/env python3
"""Gera os cards PNG do tv-feed a partir de data/terms.json.

Substitui o gerador em .NET quando ele nao esta disponivel: desenha o mesmo
layout 480x640 com ImageMagick. So cria o que esta faltando, a menos que
receba --force.
"""
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CARDS = ROOT / "cards"

W, H = 480, 640
MARGIN = 48
TOP_LEFT, TOP_RIGHT, BOTTOM_LEFT = "#1b2f5b", "#333165", "#49336d"

FONT_TERM = "Carlito-Bold"
FONT_BODY = "Carlito-Regular"
FONT_EX = "Carlito-Italic"

PT_TERM, PT_BODY, PT_EX = 46, 23, 20
LH_BODY, LH_EX = 38, 32

COL_TERM = "#ffffff"
COL_BODY = "#f0eef6"
COL_EX = "#b9b2cc"
COL_RULE = "#9a93b0"


def slugify(term):
    """Mesma regra do scripts/build.js, senao o feed aponta para um arquivo que nao existe."""
    return re.sub(r"\s+", "-", re.sub(r"[^\w\s-]", "", term)).lower()


def wrap(text, limit):
    linhas, atual = [], ""
    for palavra in text.split():
        teste = f"{atual} {palavra}".strip()
        if len(teste) <= limit:
            atual = teste
        else:
            if atual:
                linhas.append(atual)
            atual = palavra
    if atual:
        linhas.append(atual)
    return linhas


def build(term, definition, example, destino):
    cmd = [
        "convert", "-size", f"{W}x{H}", "xc:",
        "-sparse-color", "barycentric",
        f"0,0 {TOP_LEFT} {W-1},0 {TOP_RIGHT} 0,{H-1} {BOTTOM_LEFT}",
    ]

    y = 118
    cmd += ["-font", FONT_TERM, "-pointsize", str(PT_TERM), "-fill", COL_TERM,
            "-annotate", f"+{MARGIN}+{y}", term]

    y += 38
    cmd += ["-fill", COL_RULE, "-draw", f"rectangle {MARGIN-8},{y} {MARGIN+52},{y+2}"]

    y += 52
    cmd += ["-font", FONT_BODY, "-pointsize", str(PT_BODY), "-fill", COL_BODY]
    for linha in wrap(definition, 36):
        cmd += ["-annotate", f"+{MARGIN}+{y}", linha]
        y += LH_BODY

    if example:
        y += 20
        cmd += ["-font", FONT_EX, "-pointsize", str(PT_EX), "-fill", COL_EX]
        for linha in wrap(f'"{example}"', 40):
            cmd += ["-annotate", f"+{MARGIN}+{y}", linha]
            y += LH_EX

    cmd.append(str(destino))
    subprocess.run(cmd, check=True)


def main():
    force = "--force" in sys.argv
    termos = json.loads((ROOT / "data" / "terms.json").read_text(encoding="utf-8").lstrip("﻿"))
    feitos = 0
    for t in termos:
        destino = CARDS / f"{slugify(t['term'])}.png"
        if destino.exists() and not force:
            continue
        build(t["term"], t.get("definition", ""), t.get("example", ""), destino)
        print(f"  {destino.name}")
        feitos += 1
    print(f"{feitos} card(s) gerado(s)")


if __name__ == "__main__":
    main()

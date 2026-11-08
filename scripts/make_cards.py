#!/usr/bin/env python3
"""Gera os cards PNG do tv-feed a partir de data/terms.json.

Layout 480x640: faixa de foto no topo, com esmaecimento para o gradiente, e
embaixo o termo, a pronuncia em IPA, a definicao e o exemplo.

As fotos vem do vault (Static/Attachment/vocab). Um termo sem foto rende um
card so de texto, com o bloco deslocado para cima.

Desenha com ImageMagick, para rodar onde o gerador em .NET nao existe. So
cria o que falta, a menos que receba --force.
"""
import json
import os
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CARDS = ROOT / "cards"
# Onde estao as fotos. O padrao serve para o vault clonado ao lado deste repo;
# VAULT_DIR aponta para outro lugar (no PC, ou no runner do GitHub Actions).
VAULT_DIR = Path(os.environ.get("VAULT_DIR", ROOT.parent / "Personal-sync"))
VAULT_VOCAB = VAULT_DIR / "Static" / "Attachment" / "vocab"

W, H = 480, 640
MARGIN = 48
PHOTO_H, FADE_H = 210, 80
TOP_LEFT, TOP_RIGHT, BOTTOM_LEFT = "#1b2f5b", "#333165", "#49336d"

F_TERM, F_BODY, F_EX = "Carlito-Bold", "Carlito-Regular", "Carlito-Italic"
C_TERM, C_IPA, C_BODY, C_EX, C_RULE = "#ffffff", "#9f98b8", "#f0eef6", "#b9b2cc", "#8a83a0"

BOTTOM_PAD = 24  # respiro minimo abaixo da ultima linha


def slugify(term):
    """Mesma regra do scripts/build.js, senao o feed aponta para um arquivo inexistente."""
    return re.sub(r"\s+", "-", re.sub(r"[^\w\s-]", "", term)).lower()


def wrap(text, limit):
    linhas, atual = [], ""
    for p in text.split():
        teste = f"{atual} {p}".strip()
        if len(teste) <= limit:
            atual = teste
        else:
            if atual:
                linhas.append(atual)
            atual = p
    if atual:
        linhas.append(atual)
    return linhas


def layout(definition, example, pt_body, pt_ex, y0):
    """Monta as linhas e devolve onde elas terminam, para saber se coube."""
    # a largura em caracteres acompanha o corpo: fonte menor, mais cabe na linha
    body = wrap(definition, int(36 * 23 / pt_body))
    ex = wrap(f'"{example}"', int(40 * 20 / pt_ex)) if example else []
    lh_body, lh_ex = int(pt_body * 1.65), int(pt_ex * 1.6)
    y = y0 + len(body) * lh_body
    if ex:
        y += 18 + len(ex) * lh_ex
    return body, ex, lh_body, lh_ex, y


def build(term, ipa, definition, example, photo, destino):
    tem_foto = photo is not None
    base_y = PHOTO_H + 42 if tem_foto else 104

    # encolhe o texto ate caber na altura do card
    for pt_body, pt_ex in ((23, 20), (21, 18), (19, 17), (18, 16)):
        y_term = base_y
        y_ipa = y_term + 50          # altura da caixa do termo em 40pt
        y_rule = y_ipa + (40 if ipa else 10)
        y0 = y_rule + 34
        body, ex, lh_body, lh_ex, fim = layout(definition, example, pt_body, pt_ex, y0)
        if fim <= H - BOTTOM_PAD:
            break

    cmd = ["convert", "-size", f"{W}x{H}", "xc:", "-sparse-color", "barycentric",
           f"0,0 {TOP_LEFT} {W-1},0 {TOP_RIGHT} 0,{H-1} {BOTTOM_LEFT}"]

    if tem_foto:
        # foto cortada para preencher a faixa, esmaecendo no pe para o gradiente
        cmd += ["(", str(photo), "-resize", f"{W}x{PHOTO_H}^",
                "-gravity", "center", "-extent", f"{W}x{PHOTO_H}", ")",
                "(", "-size", f"{W}x{PHOTO_H - FADE_H}", "xc:white",
                "-size", f"{W}x{FADE_H}", "gradient:white-black",
                "-append", ")",
                "-gravity", "northwest", "-composite"]

    cmd += ["-gravity", "northwest",
            "-font", F_TERM, "-pointsize", "40", "-fill", C_TERM,
            "-annotate", f"+{MARGIN}+{y_term}", term]

    if ipa:
        cmd += ["-font", F_BODY, "-pointsize", "20", "-fill", C_IPA,
                "-annotate", f"+{MARGIN}+{y_ipa}", ipa]

    cmd += ["-fill", C_RULE, "-draw", f"rectangle {MARGIN},{y_rule} {MARGIN+60},{y_rule+2}"]

    y = y0
    cmd += ["-font", F_BODY, "-pointsize", str(pt_body), "-fill", C_BODY]
    for linha in body:
        cmd += ["-annotate", f"+{MARGIN}+{y}", linha]
        y += lh_body

    if ex:
        y += 18
        cmd += ["-font", F_EX, "-pointsize", str(pt_ex), "-fill", C_EX]
        for linha in ex:
            cmd += ["-annotate", f"+{MARGIN}+{y}", linha]
            y += lh_ex

    cmd.append(str(destino))
    subprocess.run(cmd, check=True)


def main():
    force = "--force" in sys.argv
    termos = json.loads((ROOT / "data" / "terms.json").read_text(encoding="utf-8").lstrip("﻿"))
    feitos, sem_foto = 0, []
    for t in termos:
        slug = slugify(t["term"])
        destino = CARDS / f"{slug}.png"
        if destino.exists() and not force:
            continue
        foto = VAULT_VOCAB / f"vocab-{slug}.jpg"
        if not foto.exists():
            foto, _ = None, sem_foto.append(t["term"])
        build(t["term"], t.get("ipa", ""), t.get("definition", ""),
              t.get("example", ""), foto, destino)
        print(f"  {destino.name}{'' if foto else '  (sem foto)'}")
        feitos += 1
    print(f"{feitos} card(s) gerado(s)")
    if sem_foto:
        print(f"sem foto no vault: {', '.join(sem_foto)}")


if __name__ == "__main__":
    main()

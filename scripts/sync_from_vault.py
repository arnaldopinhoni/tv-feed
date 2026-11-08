#!/usr/bin/env python3
"""Traz para o feed as palavras que a newsletter manda nesta semana.

A fila é a mesma do .github/scripts/send_words.py no vault: nunca revisada
primeiro, depois menor level, depois a mais antiga. Os POOL_SIZE primeiros
formam o pool, e como são dois envios de WORDS_PER_DAY por semana, o pool
inteiro é exatamente o que sai por e-mail na semana.

Só acrescenta o que falta — nada é removido, então o feed vai acumulando um
acervo para a TV girar.

    VAULT_DIR=~/Personal-sync python3 scripts/sync_from_vault.py

Sem VAULT_DIR, procura o vault em ../Personal-sync.
"""
import json
import os
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
VAULT_DIR = Path(os.environ.get("VAULT_DIR", ROOT.parent / "Personal-sync"))
INBOX = VAULT_DIR / "Static" / "_Inbox.md"
TERMS = ROOT / "data" / "terms.json"

# iguais aos do send_words.py — se mudarem lá, mudam aqui
POOL_SIZE = 8
WORDS_PER_DAY = 4
SEND_WEEKDAYS = (0, 3)

FIELD = r"\[(\w+)::\s*(.*?)\]"


def ler_vault():
    if not INBOX.exists():
        sys.exit(f"Não achei o _Inbox.md em {INBOX}. Defina VAULT_DIR.")
    palavras = []
    for linha in INBOX.read_text(encoding="utf-8").splitlines():
        if not linha.lstrip().startswith("- [term::"):
            continue
        campos = dict(re.findall(FIELD, linha))
        if not campos.get("term"):
            continue
        campos["level"] = int(campos.get("level", 0))
        palavras.append(campos)
    return palavras


def fila(palavras):
    """Mesma ordenação do send_words.py."""
    return sorted(palavras, key=lambda w: ("reviewed" in w,
                                           w["level"],
                                           w.get("reviewed", w.get("added", ""))))


def main():
    palavras = ler_vault()
    pool = fila(palavras)[:POOL_SIZE]
    if not pool:
        sys.exit("Nenhuma palavra no _Inbox.md.")

    termos = json.loads(TERMS.read_text(encoding="utf-8").lstrip("﻿"))
    existentes = {t["term"] for t in termos}

    novos = []
    for w in pool:
        if w["term"] in existentes:
            continue
        termos.append({
            "term": w["term"],
            "ipa": w.get("ipa", ""),
            "definition": w.get("translation", ""),
            "theme": w.get("theme", "general"),
            "level": str(w["level"]),
            "added": w.get("added", ""),
            "example": w.get("example", ""),
        })
        novos.append(w["term"])

    envios = len(pool) // WORDS_PER_DAY or 1
    print(f"pool da semana ({len(pool)} palavras, {envios} envio(s)):")
    for w in pool:
        marca = "novo" if w["term"] in novos else "já estava"
        print(f"  {w['term']:<22} {marca}")

    if not novos:
        print("\nNada a fazer — o feed já tem todas.")
        return

    TERMS.write_text(json.dumps(termos, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"\n{len(novos)} termo(s) no terms.json — total {len(termos)}")

    env = {**os.environ, "VAULT_DIR": str(VAULT_DIR)}
    subprocess.run([sys.executable, str(ROOT / "scripts" / "make_cards.py")], check=True, env=env)
    subprocess.run(["node", str(ROOT / "scripts" / "build.js")], check=True)


if __name__ == "__main__":
    main()

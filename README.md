# tv-feed

Feed RSS de vocabulário de inglês para o widget de um launcher de Android TV.

Cada item traz um card PNG com a palavra, a tradução e um exemplo de uso —
porque o widget da TV só desenha imagem e título, ignorando a descrição.

## Endereço

```
https://arnaldopinhoni.github.io/tv-feed/vocabulary.xml
```

## Como funciona

| Caminho | O quê |
|---|---|
| `data/terms.json` | os termos (fonte) |
| `cards/*.png` | um card desenhado por termo |
| `vocabulary.xml` | o feed, gerado a partir dos dois acima |
| `scripts/build.js` | gera o feed |
| `scripts/make_cards.py` | desenha os cards |
| `scripts/sync_from_vault.py` | traz as palavras novas do vault |

O widget da TV busca o feed quando o launcher abre e mostra **sempre o primeiro
item**. Por isso uma GitHub Action gira a ordem a cada 20 minutos: assim cada vez
que a home abre, aparece outra palavra.

Os cards são gerados no PC (precisam do System.Drawing do .NET); a Action só
reordena o que já está publicado.

## Os cards

480x640: foto no topo, depois o termo, a pronúncia em IPA, a definição e o
exemplo. A foto e o IPA vêm do vault — as mesmas que vão na newsletter.

Dois geradores, mesmo layout:

- no PC, o original em .NET (`System.Drawing`)
- `scripts/make_cards.py`, que desenha com ImageMagick e roda em qualquer
  lugar, inclusive no GitHub Actions

Os dois só criam o que falta; `--force` redesenha tudo. Se a definição não
couber nos 640px, o corpo encolhe em degraus até caber. Termo sem foto rende
card só de texto.

## Sincronização com o vault

`scripts/sync_from_vault.py` lê o `Static/_Inbox.md` do vault, repete a fila
do `send_words.py` (nunca revisada → menor level → mais antiga) e traz os
`POOL_SIZE` primeiros — que são exatamente as palavras da newsletter da
semana, já que são dois envios de quatro.

Só acrescenta: nada sai do feed, então o acervo da TV vai crescendo.

```bash
VAULT_DIR=~/Personal-sync python3 scripts/sync_from_vault.py
```

A Action `sync.yml` faz isso toda segunda às 04:40 UTC, depois do envio da
newsletter.

> [!IMPORTANT]
> O vault é um repositório **privado**, então a Action precisa de um token
> para lê-lo. Crie um fine-grained PAT com acesso de leitura de conteúdo a
> `arnaldopinhoni/personal-sync` e salve em
> *tv-feed → Settings → Secrets and variables → Actions* como **`VAULT_TOKEN`**.
> Sem ele, o passo "Baixar o vault" falha.

Se `POOL_SIZE`, `WORDS_PER_DAY` ou `SEND_WEEKDAYS` mudarem no `send_words.py`,
mude também no topo do `sync_from_vault.py` — as duas pontas precisam
concordar sobre o que é "a semana".

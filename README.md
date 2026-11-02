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
| `scripts/build.js` | o gerador |

O widget da TV busca o feed quando o launcher abre e mostra **sempre o primeiro
item**. Por isso uma GitHub Action gira a ordem a cada 20 minutos: assim cada vez
que a home abre, aparece outra palavra.

Os cards são gerados no PC (precisam do System.Drawing do .NET); a Action só
reordena o que já está publicado.

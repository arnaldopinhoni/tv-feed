#!/usr/bin/env node
/**
 * Gera o vocabulary.xml a partir de data/terms.json.
 *
 * Roda em dois lugares:
 *   - no PC, quando há palavras novas (junto com os cards)
 *   - no GitHub Actions, de tempos em tempos, só para girar a ordem
 *
 * A rotação existe porque o widget da TV mostra sempre o primeiro item e só
 * busca o feed quando o launcher abre. Girando a lista, cada abertura traz
 * outra palavra.
 */

const fs = require('fs');
const path = require('path');

const ROOT = path.resolve(__dirname, '..');
const BASE = process.env.FEED_BASE || 'https://arnaldopinhoni.github.io/tv-feed';
const ROTATE_MS = 20 * 60 * 1000; // um giro a cada 20 min

function esc(s) {
  return String(s)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}

function slugify(term) {
  return term
    .replace(/[^\w\s-]/g, '')
    .replace(/\s+/g, '-')
    .toLowerCase();
}

function rotate(list) {
  if (list.length < 2) return list;
  const shift = Math.floor(Date.now() / ROTATE_MS) % list.length;
  return list.slice(shift).concat(list.slice(0, shift));
}

// Alguns editores (e o PowerShell) gravam BOM, que o JSON.parse rejeita.
const raw = fs.readFileSync(path.join(ROOT, 'data', 'terms.json'), 'utf8').replace(/^﻿/, '');
const terms = JSON.parse(raw);
const rotated = rotate(terms);
const now = Date.now();

const items = rotated
  .map((t, i) => {
    const img = `${BASE}/cards/${encodeURIComponent(slugify(t.term))}.png`;
    // datas decrescentes: quem está na frente é o "mais novo", então a rotação
    // vale também para leitores que ordenam por data em vez da ordem do arquivo
    const when = new Date(now - i * 60000);
    const body = [t.definition, t.example ? `\n\n"${t.example}"` : '', t.theme ? `\n\n[${t.theme}]` : ''].join('');
    return `    <item>
      <title>${esc(t.term)}</title>
      <description>${esc(body)}</description>
      <enclosure url="${esc(img)}" type="image/png" length="0"/>
      <media:thumbnail url="${esc(img)}"/>
      <media:content url="${esc(img)}" medium="image"/>
      <pubDate>${when.toUTCString()}</pubDate>
      <guid isPermaLink="false">vocab-${esc(slugify(t.term))}</guid>
    </item>`;
  })
  .join('\n');

const rss = `<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:media="http://search.yahoo.com/mrss/">
  <channel>
    <title>Minhas Palavras</title>
    <link>${esc(BASE)}/vocabulary.xml</link>
    <description>Vocabulário de inglês</description>
    <language>pt-BR</language>
    <lastBuildDate>${new Date().toUTCString()}</lastBuildDate>
${items}
  </channel>
</rss>
`;

fs.writeFileSync(path.join(ROOT, 'vocabulary.xml'), rss, 'utf8');
console.log(`vocabulary.xml gerado — ${terms.length} termos, primeiro: ${rotated[0].term}`);

// Build-time data readers for the briefing. Everything here derives
// from repo state (the wiki, the inbox) — the briefing introduces no
// store of its own (presentation-layer ADR).
import fs from 'node:fs';
import path from 'node:path';
import url from 'node:url';

const HERE = path.dirname(url.fileURLToPath(import.meta.url));
const REPO = path.resolve(HERE, '..', '..', '..');
const WIKI = path.join(REPO, 'wiki');

export function inboxItems() {
  const dir = path.join(WIKI, '_state', 'inbox');
  if (!fs.existsSync(dir)) return [];
  return fs
    .readdirSync(dir)
    .filter((f) => f.endsWith('.json'))
    .map((f) => {
      try {
        return JSON.parse(fs.readFileSync(path.join(dir, f), 'utf8'));
      } catch {
        return null;
      }
    })
    .filter(Boolean);
}

// First `max` top-level bullets of a `## <section>` in a wiki page,
// markdown links stripped to their text.
export function sectionBullets(relPage, section, max = 3) {
  const file = path.join(WIKI, relPage);
  if (!fs.existsSync(file)) return [];
  const text = fs.readFileSync(file, 'utf8');
  const m = text.match(new RegExp(`^## ${section}\\s*$`, 'm'));
  if (!m) return [];
  const rest = text.slice(m.index + m[0].length);
  const end = rest.search(/^## /m);
  const body = end === -1 ? rest : rest.slice(0, end);
  const bullets = [];
  for (const chunk of body.split(/^- /m).slice(1)) {
    const flat = chunk
      .split(/\n(?=- )/)[0]
      .replace(/\n\s+/g, ' ')
      .replace(/\[([^\]]+)\]\([^)]*\)/g, '$1')
      .replace(/\*\*/g, '')
      .trim();
    if (flat) bullets.push(flat.length > 220 ? flat.slice(0, 217) + '…' : flat);
    if (bullets.length >= max) break;
  }
  return bullets;
}

export function version() {
  const f = path.join(REPO, 'VERSION');
  return fs.existsSync(f) ? fs.readFileSync(f, 'utf8').trim() : '';
}

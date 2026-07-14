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

// The conversation surface: channels (topics) + pending posts. Reads
// the channels.json view brain.py emits; the pending posts are inbox
// channel-post items awaiting an in-thread reply on the next tend.
export function channels() {
  const p = path.join(WIKI, '_views', 'channels.json');
  if (!fs.existsSync(p)) return { channels: [], activity: { pending_posts: 0 } };
  try {
    return JSON.parse(fs.readFileSync(p, 'utf8'));
  } catch {
    return { channels: [], activity: { pending_posts: 0 } };
  }
}

// Pending (un-replied) posts for one thread slug, oldest first — what a
// channel view shows below the topic thread until the agent replies.
export function channelPosts(slug) {
  return inboxItems()
    .filter((i) => i.channel_post && i.thread === slug)
    .sort((a, b) => (a.produced_at || '').localeCompare(b.produced_at || ''));
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

// ---- link graph (computed from page bodies at build time) -----------

const SKIP_PREFIXES = ['_'];

function wikiFiles(dir = WIKI, out = []) {
  for (const name of fs.readdirSync(dir)) {
    const full = path.join(dir, name);
    const rel = path.relative(WIKI, full);
    if (SKIP_PREFIXES.some((p) => rel.startsWith(p))) continue;
    const stat = fs.statSync(full);
    if (stat.isDirectory()) wikiFiles(full, out);
    else if (name.endsWith('.md')) out.push(rel);
  }
  return out;
}

export function linkGraph() {
  const files = wikiFiles();
  // Read the provenance-tagged edge list brain.py emits (single source
  // of truth); fall back to deriving authored links if it's absent.
  const graphPath = path.join(WIKI, '_views', 'graph.json');
  let edges;
  let ambiguous = new Set();
  if (fs.existsSync(graphPath)) {
    const g = JSON.parse(fs.readFileSync(graphPath, 'utf8'));
    const set = new Set(files);
    edges = (g.edges || [])
      .filter((e) => set.has(e.source) && set.has(e.target))
      .map((e) => [e.source, e.target, e.provenance]);
    ambiguous = new Set((g.ambiguous_nodes || []).filter((n) => set.has(n)));
  } else {
    const set = new Set(files);
    edges = [];
    for (const rel of files) {
      const text = fs.readFileSync(path.join(WIKI, rel), 'utf8');
      for (const m of text.matchAll(/\]\(([^)]+\.md)(#[^)]*)?\)/g)) {
        const target = m[1];
        if (/^(https?|mailto):/.test(target) || target.startsWith('~')) continue;
        const resolved = path
          .normalize(path.join(path.dirname(rel), target))
          .replaceAll('\\', '/');
        if (set.has(resolved) && resolved !== rel) {
          edges.push([rel, resolved, 'extracted']);
        }
      }
    }
  }
  // Inbound counts only from EXTRACTED (authored) edges — an inferred
  // suggestion shouldn't inflate a hub's degree.
  const inbound = Object.fromEntries(files.map((f) => [f, 0]));
  for (const [, dst, prov] of edges) if (prov === 'extracted') inbound[dst]++;
  return { files, edges, inbound, ambiguous };
}

// ---- audit-log activity (ops per day, last N days) -------------------

export function logActivity(days = 30) {
  const file = path.join(REPO, 'log', 'log.md');
  if (!fs.existsSync(file)) return { series: [], total: 0 };
  const counts = new Map();
  for (const m of fs
    .readFileSync(file, 'utf8')
    .matchAll(/^(\d{4}-\d{2}-\d{2}) (mine|ingest|merge|commit)/gm)) {
    counts.set(m[1], (counts.get(m[1]) ?? 0) + 1);
  }
  const series = [];
  const today = new Date();
  for (let i = days - 1; i >= 0; i--) {
    const d = new Date(today.getTime() - i * 86400000)
      .toISOString()
      .slice(0, 10);
    series.push({ date: d, n: counts.get(d) ?? 0 });
  }
  return { series, total: [...counts.values()].reduce((a, b) => a + b, 0) };
}

// ---- attention-grade calibration -------------------------------------

export function gradeStats() {
  const file = path.join(WIKI, '_state', 'attention-grades.json');
  if (!fs.existsSync(file)) return { useful: 0, noise: 0 };
  const grades = JSON.parse(fs.readFileSync(file, 'utf8')).grades ?? [];
  return {
    useful: grades.filter((g) => g.grade === 'useful').length,
    noise: grades.filter((g) => g.grade === 'noise').length,
    ids: grades.map((g) => g.id),
  };
}

// Receives correction reports from /corrections.html and stores each as a private JSON file in Vercel Blob.
// Nothing is published automatically: the author reviews each report against its source (D265).
// Requires a Blob store connected to the project (environment variable BLOB_READ_WRITE_TOKEN).
import { put } from '@vercel/blob';

const LIMITS = { page: 200, figure: 300, detail: 2000, source: 500, email: 200 };

export default async function handler(req, res) {
  if (req.method !== 'POST') { res.setHeader('Allow', 'POST'); return res.status(405).json({ error: 'POST only' }); }
  const b = typeof req.body === 'string' ? JSON.parse(req.body || '{}') : (req.body || {});
  const r = {};
  for (const [k, n] of Object.entries(LIMITS)) r[k] = String(b[k] || '').slice(0, n).trim();
  if (!r.page || !r.figure || !r.detail || !r.source) return res.status(400).json({ error: 'page, figure, detail and source are required' });
  r.received = new Date().toISOString();
  const id = `${r.received.replace(/[:.]/g, '-')}-${Math.random().toString(36).slice(2, 8)}`;
  await put(`corrections/${id}.json`, JSON.stringify(r, null, 1), { access: 'private', contentType: 'application/json', addRandomSuffix: false });
  return res.status(200).json({ ok: true });
}

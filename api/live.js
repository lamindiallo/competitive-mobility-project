// This season's tables (D293, D299). Primary source: football-data.org (free tier; token in FOOTBALL_DATA_TOKEN).
// Fallback: openfootball/football.json (public domain), which can run weeks behind. Cached for 30 minutes.
// Club crests in the API response are deliberately dropped: the site uses no club badges (D292).
const COMPS = { ENG: { 1: 'PL', 2: 'ELC' }, ESP: { 1: 'PD' }, ITA: { 1: 'SA' }, GER: { 1: 'BL1' }, FRA: { 1: 'FL1' } };
const OF = { ENG: 'en', ESP: 'es', ITA: 'it', GER: 'de', FRA: 'fr' };
const SEASON = process.env.LIVE_SEASON || '2026-27';

async function footballData(token) {
  const out = {}; let matchdays = {};
  const jobs = [];
  for (const [c, tiers] of Object.entries(COMPS)) for (const [t, code] of Object.entries(tiers)) {
    jobs.push((async () => {
      const r = await fetch(`https://api.football-data.org/v4/competitions/${code}/standings`, { headers: { 'X-Auth-Token': token } });
      if (!r.ok) throw new Error(`${code} ${r.status}`);
      const j = await r.json();
      const total = (j.standings || []).find(s => s.type === 'TOTAL') || (j.standings || [])[0];
      if (!total) return;
      (out[c] = out[c] || {})[t] = {
        matchday: j.season && j.season.currentMatchday,
        rows: total.table.map(x => [x.position, x.team.name, x.team.shortName || x.team.name, x.playedGames, x.goalsFor, x.goalsAgainst, x.points])
      };
    })());
  }
  const res = await Promise.allSettled(jobs);
  if (!Object.keys(out).length) throw new Error(res.map(x => x.reason && x.reason.message).join('; '));
  return out;
}

async function openfootball() {
  const leagues = {};
  await Promise.all(Object.entries(COMPS).flatMap(([c, tiers]) => Object.keys(tiers).map(async (t) => {
    try {
      const r = await fetch(`https://raw.githubusercontent.com/openfootball/football.json/master/${SEASON}/${OF[c]}.${t}.json`); if (!r.ok) return;
      const j = await r.json(); const ms = [];
      for (const m of j.matches || []) {
        const s = Array.isArray(m.score) ? m.score : (m.score && m.score.ft);
        if (!s || s.length !== 2 || !(m.round || '').startsWith('Matchday')) continue;
        ms.push([m.date, m.team1, m.team2, +s[0], +s[1]]);
      }
      (leagues[c] = leagues[c] || {})[t] = ms;
    } catch (e) { /* leave this league out */ }
  })));
  return leagues;
}

export default async function handler(req, res) {
  const now = new Date().toISOString();
  const token = process.env.FOOTBALL_DATA_TOKEN;
  let body = null, note = '';
  if (token) {
    try { body = { season: SEASON, fetched: now, source: 'football-data.org', standings: await footballData(token) }; }
    catch (e) { note = 'football-data.org unavailable: ' + String(e.message || e).slice(0, 200); }
  }
  if (!body) {
    const leagues = await openfootball();
    if (!Object.keys(leagues).length) { res.status(502).json({ error: 'results unavailable', note }); return; }
    body = { season: SEASON, fetched: now, source: 'openfootball/football.json (CC0)', leagues, note };
  }
  res.setHeader('Cache-Control', 'public, s-maxage=1800, stale-while-revalidate=21600');
  res.status(200).json(body);
}

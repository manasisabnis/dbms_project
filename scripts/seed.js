require('dotenv').config({ path: '.env.local' });
const mysql = require('mysql2/promise');
const { MongoClient } = require('mongodb');
const bcrypt = require('bcryptjs');

const rnd = (a, b) => Math.floor(Math.random() * (b - a + 1)) + a;
const pick = a => a[rnd(0, a.length - 1)];
const DAY = 864e5, today = new Date();
const fmt = d => d.toISOString().slice(0, 10);
const daysAgo = n => new Date(today.getTime() - n * DAY);

const FIRST = ['Ramesh','Sunita','Arjun','Meera','Vikram','Anita','Rahul','Kavya','Suresh','Lakshmi','Imran','Priya','Gopal','Farida','Harish'];
const LAST = ['Sharma','Iyer','Nair','Reddy','Khan','Das','Patel','Menon','Gupta','Rao','Singh','Bose'];
const RESP = ['State of Karnataka','Union of India','State of Maharashtra','Municipal Corporation of Delhi','Reliable Finance Ltd','State of Kerala','Bharat Textiles Pvt Ltd','State of Tamil Nadu','Commissioner of Income Tax','Metro Rail Authority'];
const TOPICS = ['breach of contract','right to privacy','property inheritance','wrongful termination','bail and personal liberty','tax assessment','environmental clearance','consumer protection','freedom of speech','land acquisition compensation','cheque dishonour','custodial rights'];
const TYPES = ['Constitutional','Criminal','Civil','Contract','Property','Tax','Labour','Family'];
const ACTS = [['Indian Contract Act','73',1872],['Indian Penal Code','302',1860],['Constitution of India','Article 21',1950],['Transfer of Property Act','54',1882],['Income Tax Act','143',1961],['Industrial Disputes Act','25F',1947],['Consumer Protection Act','35',2019],['Negotiable Instruments Act','138',1881]];
const TREAT = ['followed','followed','followed','referred','referred','distinguished','overruled'];
const SNIPPETS = ['The ratio of the cited judgment was applied.','The principle laid down earlier was relied upon.','The bench distinguished the earlier ruling on facts.','The earlier view was reaffirmed by this Court.'];

(async () => {
  const pool = await mysql.createPool({ host: process.env.MYSQL_HOST, port: +process.env.MYSQL_PORT || 3306, user: process.env.MYSQL_USER, password: process.env.MYSQL_PASSWORD, database: process.env.MYSQL_DATABASE });
  const mongo = await new MongoClient(process.env.MONGO_URI).connect();
  const events = mongo.db(process.env.MONGO_DB).collection('citation_events');

  await pool.query('SET FOREIGN_KEY_CHECKS=0');
  for (const t of ['Audit_Log','Citation','Statute','Case_Judge','Judge','Legal_Case','Court','App_User']) await pool.query(`TRUNCATE TABLE ${t}`);
  await pool.query('SET FOREIGN_KEY_CHECKS=1');
  await events.deleteMany({});

  // Users (passwords hashed with bcrypt)
  for (const [u, p, r] of [['admin','Admin@123','admin'],['analyst','Analyst@123','analyst']])
    await pool.query('INSERT INTO App_User(username,password_hash,role) VALUES (?,?,?)', [u, await bcrypt.hash(p, 10), r]);

  // Courts
  const courts = [['Supreme Court of India','Supreme Court','New Delhi',1950],['Karnataka High Court','High Court','Bengaluru',1884],['Delhi High Court','High Court','New Delhi',1966],['Bombay High Court','High Court','Mumbai',1862],['Bengaluru Urban District Court','District Court','Bengaluru',1900],['NCLT Mumbai Bench','Tribunal','Mumbai',2016]];
  const courtIds = [];
  for (const c of courts) courtIds.push((await pool.query('INSERT INTO Court(court_name,court_level,location,established_year) VALUES (?,?,?,?)', c))[0].insertId);

  // Judges
  const judgeIds = [];
  for (let i = 0; i < 10; i++) {
    const app = new Date(1985 + rnd(0, 25), rnd(0, 11), rnd(1, 28));
    const ret = new Date(app.getFullYear() + rnd(8, 20), rnd(0, 11), rnd(1, 28));
    judgeIds.push((await pool.query('INSERT INTO Judge(judge_name,designation,appointed_date,retired_date) VALUES (?,?,?,?)', [`Justice ${pick(FIRST)} ${pick(LAST)}`, pick(['Judge','Chief Justice','Senior Judge']), fmt(app), i % 4 === 0 ? null : fmt(ret)]))[0].insertId);
  }

  async function addCase(date, courtId, idx) {
    const topic = pick(TOPICS);
    const name = `${pick(FIRST)} ${pick(LAST)} v. ${pick(RESP)}`;
    const dec = `The Court examined ${topic} and held that the principle of ${pick(TOPICS)} must be read with ${pick(ACTS)[0]}. Appeal ${pick(['allowed','dismissed','partly allowed'])}.`;
    const [r] = await pool.query('INSERT INTO Legal_Case(case_name,case_number,judgment_date,case_type,decision,court_id) VALUES (?,?,?,?,?,?)', [name, `CA-${idx}/${date.getFullYear()}`, fmt(date), pick(TYPES), dec, courtId]);
    const id = r.insertId;
    const js = [...judgeIds].sort(() => Math.random() - 0.5).slice(0, rnd(1, 3));
    for (let k = 0; k < js.length; k++) await pool.query('INSERT INTO Case_Judge VALUES (?,?,?)', [id, js[k], ['Presiding','Concurring','Dissenting'][k]]);
    const sts = [...ACTS].sort(() => Math.random() - 0.5).slice(0, rnd(1, 2));
    for (let k = 0; k < sts.length; k++) await pool.query('INSERT INTO Statute VALUES (?,?,?,?,?,?)', [id, k + 1, sts[k][0], sts[k][1], `Provision relied upon in ${topic}`, sts[k][2]]);
    return { id, date };
  }

  // 20 foundational (older) cases and 100 later cases spread over the last 3 years
  const F = [], L = [];
  for (let i = 0; i < 8; i++) F.push(await addCase(new Date(rnd(1955, 2021), rnd(0, 11), rnd(1, 28)), i < 5 ? courtIds[0] : pick(courtIds), i + 1));
  for (let i = 0; i < 40; i++) L.push(await addCase(daysAgo(rnd(0, Math.random() < 0.5 ? 365 : 1090)), pick(courtIds), i + 9));

  // Citation behaviour: F[0-3] emerging, F[4-7] declining, F[8-11] steady, rest rarely cited
  // F[0-1] emerging, F[2-3] declining (cited heavily until ~6 months ago), F[4-5] steady, F[6-7] rarely cited
  const weight = (fi, age) => fi < 2 ? (age < 180 ? 8 : 0.6) : fi < 4 ? (age > 180 ? 5 : 0.3) : fi < 6 ? 2 : 0.4;
  const docs = [];
  for (const lc of L) {
    const age = Math.round((today - lc.date) / DAY);
    const chosen = new Set();
    const k = rnd(2, 4);
    while (chosen.size < k) {
      const ws = F.map((_, i) => weight(i, age)), tot = ws.reduce((a, b) => a + b, 0);
      let r = Math.random() * tot, i = 0;
      while (i < ws.length - 1 && (r -= ws[i]) > 0) i++;
      chosen.add(i);
    }
    for (const fi of chosen) {
      const text = pick(SNIPPETS), page = rnd(1, 60);
      const [r] = await pool.query('INSERT INTO Citation(citing_case_id,cited_case_id,citation_date,context_text,page_number) VALUES (?,?,?,?,?)', [lc.id, F[fi].id, fmt(lc.date), text, page]);
      docs.push({ citation_id: r.insertId, cited_case_id: F[fi].id, citing_case_id: lc.id, event_type: 'CITED', event_date: new Date(fmt(lc.date)), treatment: pick(TREAT), context: { text, page }, tags: [] });
    }
  }
  await events.insertMany(docs);
  await events.createIndex({ cited_case_id: 1, event_date: -1 });
  await events.createIndex({ event_date: -1 });
  await events.createIndex({ treatment: 1 });
  await events.createIndex({ citation_id: 1 });
  console.log(`Seeded: ${courts.length} courts, ${judgeIds.length} judges, ${F.length + L.length} cases, ${docs.length} citations (+ Mongo events).`);
  console.log('Logins -> admin / Admin@123  |  analyst / Analyst@123');
  await pool.end(); await mongo.close();
})().catch(e => { console.error(e); process.exit(1); });

require('dotenv').config({ path: '.env.local' });
const mysql = require('mysql2/promise');
const fs = require('fs');
(async () => {
  const base = { host: process.env.MYSQL_HOST, port: +process.env.MYSQL_PORT || 3306, user: process.env.MYSQL_USER, password: process.env.MYSQL_PASSWORD };
  const db = process.env.MYSQL_DATABASE;
  const root = await mysql.createConnection(base);
  await root.query(`CREATE DATABASE IF NOT EXISTS \`${db}\``);
  await root.end();
  const c = await mysql.createConnection({ ...base, database: db, multipleStatements: true });
  await c.query(fs.readFileSync('db/schema.sql', 'utf8'));
  for (const s of fs.readFileSync('db/routines.sql', 'utf8').split('-- SPLIT')) if (s.trim()) await c.query(s);
  console.log('MySQL schema, view, procedure, function and triggers created in', db);
  await c.end();
})().catch(e => { console.error(e.message); process.exit(1); });

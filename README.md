# Legal Case Citation Evolution Analyzer
DBMS Level 3 Project — M.B. Divyadharshini (PES2UG24CS252), Manasi Sabnis (PES2UG24CS261), Section E

Analyses how Indian legal precedents gain or lose influence over time.
**MySQL** stores structured legal data; **MongoDB** stores evolving citation events and powers time-window trend aggregation.
**Stack:** Next.js 14 (UI + Route Handlers API) · MySQL 8 · MongoDB · JWT auth (httpOnly cookie) · bcrypt.

## Prerequisites
Node.js 18+, MySQL 8+, MongoDB 6+ (local, or `docker run -d -p 27017:27017 --name mongo mongo:7`).

## Setup & run (bash)
```bash
cd legal-citation-analyzer
npm install
cp .env.example .env.local        # then edit .env.local: set MYSQL_PASSWORD and JWT_SECRET
npm run setup-db                  # creates DB, tables, indexes, views, procedure, function, triggers
npm run seed                      # fabricated data: 6 courts, 10 judges, 48 cases, ~130 citations + Mongo events
npm run dev                       # open http://localhost:3000
```
Logins: **admin / Admin@123** (full access) · **analyst / Analyst@123** (read-only).

## Requirement coverage
| Requirement | Where |
|---|---|
| SQL + NoSQL | MySQL (`db/schema.sql`) + MongoDB `citation_events` (`scripts/seed.js`, `app/api/trends`) |
| ER diagram, relational schema | `docs/DOCUMENTATION.md` |
| DDL: CREATE/ALTER/DROP, PK/FK, constraints, indexes, views | `db/schema.sql`, `db/demo_ddl.sql` |
| DML + JOIN/GROUP BY/HAVING/ORDER BY/aggregates/subqueries | `db/queries.sql`, `app/api/*` |
| Advanced features (7) | Transaction + stored procedure (`sp_add_citation`), triggers (`trg_citation_*`), stored function, views, indexes, full-text search, Mongo aggregation |
| Next.js UI + API layer | `app/` (dashboard, cases, citations) |
| Env vars | `.env.local` (git-ignored) |
| Auth + 2 roles | `admin`, `analyst` — JWT, `middleware.js`, `lib/auth.js` |
| DB-level validation | CHECK, UNIQUE, FK, NOT NULL, ENUM, triggers |
| Security | bcrypt hashes, parameterised queries, httpOnly cookie, login rate limit, server-side role checks, no hard-coded secrets |

## Guides
See `docs/USER_GUIDE.md` (how to navigate/use) and `docs/DOCUMENTATION.md` (project report).

## Git
```bash
git init && git add . && git commit -m "Initial commit"
git remote add origin <your-repo-url> && git push -u origin main
```
Each member should commit their own parts (see contribution split in docs).

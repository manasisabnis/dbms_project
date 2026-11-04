# ⚖️ Legal Case Citation Evolution Analyzer

**DBMS Experiential Learning – Level 3 Project** · PES University · Section E

A database-driven web application that analyses how Indian legal precedents **gain or lose influence over time**. It stores courts, judges, cases, statutes and case-to-case citations, then compares citation activity across time windows to identify **emerging**, **declining** and **frequently cited** precedents.

##  Team

| Name | SRN |
|---|---|
| Manasi Sabnis | PES2UG24CS261 |
| M.B. Divyadharshini | PES2UG24CS252 |

##  Tech Stack

| Layer | Technology |
|---|---|
| Frontend | Next.js 14 (React) |
| Backend / API | Next.js Route Handlers |
| SQL database | MySQL 8 |
| NoSQL database | MongoDB (citation events) |
| Authentication | JWT (httpOnly cookie), bcrypt password hashing |
| Version control | Git + GitHub |

##  Why two databases?

- **MySQL** – legal data is structured and relational (courts → cases → judges / statutes / citations). We need foreign keys, CHECK constraints, transactions, triggers and views.
- **MongoDB** – citation events keep growing and carry flexible metadata (treatment, context, tags). Aggregation pipelines suit the time-window trend analysis.

##  Features

- Role-based login (**Admin** – full access, **Analyst** – read-only)
- Dashboard: coloured KPIs, 12-month citation activity, emerging / declining precedents (30/90/180/365-day windows), most-cited cases, citations by court level and case type, landmark cases
- Case search (full-text + filters) with pagination
- Case detail page: Overview, Citation Analysis (1/3/5 years), Judges, Full Text
- Citation management with database-level validation
- Transactional case deletion with its citations

## 🔧 Advanced Database Features

1. Transactions (`sp_add_citation`, cascade delete of a case)
2. Stored procedure and stored function (`sp_add_citation`, `fn_citations_between`)
3. Triggers (citation date validation, citation-count maintenance, audit log)
4. Views (`Landmark_Cases`, `v_case_details`)
5. Indexes and full-text index
6. MongoDB aggregation pipelines (`$group`, `$cond`, `$facet`)

##  Work Division

### Manasi Sabnis — PES2UG24CS261
- Database design: ER diagram and relational schema.
- MySQL tables, constraints and indexes.
- Citation management: add, update and delete citation functionality.
- Citation triggers and audit logging.
- Citation analysis API and trend calculations.
- Corresponding frontend citation-management and analysis screens.
- Test citation chronology and citation-count updates.

### M.B. Divyadharshini — PES2UG24CS252
- Case and court database operations.
- Stored procedures and stored functions.
- MongoDB citation-event integration.
- Login, authentication and RBAC.
- Dashboard analytics API and visualisations.
- Case search, filtering and case-detail screens.
- Test authentication, case operations and dashboard metrics.

##  Setup and Run

**Prerequisites:** Node.js 18+, MySQL 8+, MongoDB 6+ (or Docker: `docker run -d -p 27017:27017 --name mongo mongo:7`)

```bash
git clone https://github.com/manasisabnis/dbms_project.git
cd dbms_project
npm install
cp .env.example .env.local     # then edit .env.local (MySQL password, JWT secret)
npm run setup-db               # creates tables, indexes, views, procedure, function, triggers
npm run seed                   # loads fabricated sample data
npm run dev                    # open http://localhost:3000
```

### Environment variables (`.env.local`)

```
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=your_mysql_password
MYSQL_DATABASE=legal_precedent
MONGO_URI=mongodb://localhost:27017
MONGO_DB=legal_precedent
JWT_SECRET=a-long-random-string-of-at-least-32-characters
```

`.env.local` is git-ignored. Never commit real credentials.

### Demo logins

| Role | Username | Password |
|---|---|---|
| Admin | `admin` | `Admin@123` |
| Analyst | `analyst` | `Analyst@123` |

##  Project Structure

```
app/          Next.js pages and API route handlers
components/   Navigation and chart components
lib/          Database connections, auth and helpers
db/           schema.sql, routines.sql (procedure, function, triggers), queries.sql, demo_ddl.sql
scripts/      setup-db.js and seed.js
docs/         DOCUMENTATION.md (project report) and USER_GUIDE.md
```

##  Security

- Passwords stored as bcrypt hashes
- JWT in an httpOnly, SameSite cookie
- Role checks in every write API; middleware protects all pages
- Parameterised queries (no SQL injection)
- Credentials only in environment variables
- Login rate limiting

##  Documentation

- [Project report](docs/DOCUMENTATION.md) – problem statement, ER diagram, relational schema, data dictionary, test cases
- [User guide](docs/USER_GUIDE.md) – how to navigate and use the application

## 🔮 Future Enhancements

Semantic search over judgments using vector embeddings, real data import, and a citation network graph (Neo4j).

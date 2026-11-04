# User Guide — Legal Case Citation Evolution Analyzer

## 1. Run the application (Git Bash / terminal)
```bash
cd legal-citation-analyzer
npm install
cp .env.example .env.local     # first time only; then edit .env.local (MySQL password, JWT_SECRET)
npm run setup-db               # create tables, views, triggers, procedure, function
npm run seed                   # load fabricated data (6 courts, 10 judges, 48 cases, ~130 citations)
npm run dev                    # open http://localhost:3000
```
MySQL and MongoDB must be running. To reset the data any time: `npm run setup-db && npm run seed`.

## 2. Logging in
| Role | Username | Password | Can do |
|---|---|---|---|
| Admin | `admin` | `Admin@123` | Everything: view, add, edit, delete cases and citations |
| Analyst | `analyst` | `Analyst@123` | View, search and analyse only (read-only) |

Tip: use a normal window for admin and an incognito window for analyst to show both roles side by side. The top-right badge shows who is logged in. Five wrong passwords in a minute locks login for a minute.

## 3. Navigation
The top bar has **Dashboard**, **Cases**, **Citations** and **Logout**. The highlighted link is your current page.

### Dashboard
| Section | What it tells you |
|---|---|
| Coloured cards | Total cases, citations, courts, judges, and never-cited cases |
| Citation activity (12 months) | Area chart of citations per month (MongoDB) |
| How cases treat precedents | Donut: followed / referred / distinguished / overruled |
| **Trend window** (30/90/180/365 days) | Click to change the period. Compares the last N days with the N days before |
| Emerging precedents (green) | Recent citations ≥ 2 and ≥ 1.5× the previous window |
| Declining precedents (red) | Previous ≥ 2 and recent ≤ half of previous |
| Most cited / court level / case type | Bar and donut charts from SQL GROUP BY queries |
| Landmark cases | SQL view of cases with ≥ 5 citations |
| Above-average cited | SQL subquery |

Click any case name to open its detail page. Some windows may show "No emerging/declining" – try another window.

### Cases
- **Search** by name or decision text (full-text search); filter by court or type; **Reset** clears filters.
- Results are paged (10 per page). Click **Analyze** or the case name for details.
- **Admin only:** *Edit* (changes the decision text), *Delete* (removes the case and its citations in one transaction, after confirming), and the **Add a case** form at the bottom.
- Validation messages (for example a future judgment date or duplicate case number) appear in red above the table.

### Case detail page (tabs)
1. **Overview** – case number, court, date, statutes referred to.
2. **Citation Analysis** – choose **1 / 3 / 5 years**. Shows total, recent window, previous window, % change, status badge, running-total trend line, year-wise bars, citations by court level, how later cases treated it, and recent citing cases.
3. **Judges** – bench with role, designation and service dates.
4. **Full Text** – decision text.

### Citations (admin can add/delete)
1. Pick the **citing** case and the **cited** case, the date, optional page, treatment and context.
2. Click **Add citation**. The stored procedure runs a transaction; a trigger rejects a case citing a *later* judgment and keeps `citation_count` correct; a MongoDB event is stored for trend analysis.
3. Use **Delete** on a row to remove a citation (counts update automatically).

## 4. Suggested demo flow (viva)
1. Login as analyst → show read-only UI → try `curl` write → 403.
2. Login as admin → Dashboard: change the trend window, explain emerging vs declining.
3. Cases: search "contract", filter, open a case, switch 1/3/5 years.
4. Add a citation (valid) → show count +1 → try an invalid one (older case citing newer) → trigger error.
5. Delete a case → citations removed, counts recalculated.
6. Show MySQL: `SHOW TRIGGERS; SELECT * FROM Landmark_Cases;` and Mongo: `db.citation_events.find().limit(3)`.

## 5. Troubleshooting
| Problem | Fix |
|---|---|
| Access denied for root | Correct `MYSQL_PASSWORD` in `.env.local` |
| Invalid credentials | Run `npm run seed` (needs MongoDB running) |
| Mongo connection refused | Start MongoDB (`docker start mongo` or `net start MongoDB`) |
| Charts empty | Re-run `npm run seed`; data is relative to today's date |

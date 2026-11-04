-- Important queries (also used by the app)
-- 1. JOIN + ORDER BY
SELECT lc.case_name, co.court_name FROM Legal_Case lc JOIN Court co ON co.court_id = lc.court_id ORDER BY lc.judgment_date DESC LIMIT 10;
-- 2. GROUP BY + HAVING + aggregate
SELECT co.court_name, COUNT(*) AS cases, SUM(lc.citation_count) AS total_citations
FROM Court co JOIN Legal_Case lc ON co.court_id = lc.court_id
GROUP BY co.court_id, co.court_name HAVING COUNT(*) > 1 ORDER BY total_citations DESC;
-- 3. Subquery: above-average cited cases
SELECT case_name, citation_count FROM Legal_Case WHERE citation_count > (SELECT AVG(citation_count) FROM Legal_Case) ORDER BY citation_count DESC;
-- 4. Subquery NOT IN: never-cited cases
SELECT case_id, case_name FROM Legal_Case WHERE case_id NOT IN (SELECT cited_case_id FROM Citation);
-- 5. Full-text search
SELECT case_name FROM Legal_Case WHERE MATCH(case_name, decision) AGAINST ('contract breach' IN NATURAL LANGUAGE MODE);
-- 6. Stored function: citations in last year vs the year before
SELECT case_id, fn_citations_between(case_id, CURDATE() - INTERVAL 1 YEAR, CURDATE()) AS last_year,
       fn_citations_between(case_id, CURDATE() - INTERVAL 2 YEAR, CURDATE() - INTERVAL 1 YEAR) AS prev_year
FROM Legal_Case ORDER BY last_year DESC LIMIT 10;
-- 7. Stored procedure (transaction inside)
CALL sp_add_citation(120, 1, CURDATE(), 'Followed the ratio in para 12', 14);
-- 8. View
SELECT * FROM Landmark_Cases ORDER BY citation_count DESC;
-- 9. Update / Delete
UPDATE Legal_Case SET decision = 'Appeal allowed' WHERE case_id = 1;
DELETE FROM Citation WHERE citation_id = 1;   -- trigger decrements citation_count

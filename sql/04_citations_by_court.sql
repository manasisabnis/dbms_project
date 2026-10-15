USE legal_citation_analyzer;

SELECT
    court.court_name,
    court.court_level,
    COUNT(c.citation_id) AS citations_received,
    COUNT(DISTINCT c.cited_case_id) AS distinct_cases_cited
FROM COURT AS court
JOIN LEGAL_CASE AS lc
    ON lc.court_id = court.court_id
JOIN CITATION AS c
    ON c.cited_case_id = lc.case_id
GROUP BY
    court.court_id,
    court.court_name,
    court.court_level
ORDER BY citations_received DESC;

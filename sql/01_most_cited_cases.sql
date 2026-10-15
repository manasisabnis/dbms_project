USE legal_citation_analyzer;

SELECT
    lc.case_id,
    lc.case_name,
    lc.case_number,
    lc.judgment_date,
    COUNT(c.citation_id) AS citation_count
FROM LEGAL_CASE AS lc
JOIN CITATION AS c
    ON lc.case_id = c.cited_case_id
GROUP BY
    lc.case_id,
    lc.case_name,
    lc.case_number,
    lc.judgment_date
ORDER BY citation_count DESC, lc.case_name
LIMIT 20;

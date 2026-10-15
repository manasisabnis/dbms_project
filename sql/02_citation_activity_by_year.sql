USE legal_citation_analyzer;

SELECT
    cited.case_id,
    cited.case_name,
    YEAR(c.citation_date) AS citation_year,
    COUNT(*) AS citations_received
FROM CITATION AS c
JOIN LEGAL_CASE AS cited
    ON c.cited_case_id = cited.case_id
WHERE c.citation_date IS NOT NULL
GROUP BY
    cited.case_id,
    cited.case_name,
    YEAR(c.citation_date)
ORDER BY
    citation_year,
    citations_received DESC;

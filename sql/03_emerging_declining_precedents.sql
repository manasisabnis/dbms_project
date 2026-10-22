USE legal_citation_analyzer;

WITH yearly_citations AS (
    SELECT
        cited_case_id,
        YEAR(citation_date) AS citation_year,
        COUNT(*) AS citation_count
    FROM CITATION
    WHERE citation_date IS NOT NULL
    GROUP BY cited_case_id, YEAR(citation_date)
),
latest_year AS (
    SELECT MAX(citation_year) AS max_year
    FROM yearly_citations
),
comparison AS (
    SELECT
        yc.cited_case_id,
        SUM(
            CASE
                WHEN yc.citation_year = ly.max_year
                THEN yc.citation_count
                ELSE 0
            END
        ) AS recent_citations,
        SUM(
            CASE
                WHEN yc.citation_year = ly.max_year - 1
                THEN yc.citation_count
                ELSE 0
            END
        ) AS previous_citations
    FROM yearly_citations AS yc
    CROSS JOIN latest_year AS ly
    WHERE yc.citation_year IN (ly.max_year, ly.max_year - 1)
    GROUP BY yc.cited_case_id
)
SELECT
    lc.case_id,
    lc.case_name,
    cmp.recent_citations,
    cmp.previous_citations,
    cmp.recent_citations - cmp.previous_citations AS citation_change,
    CASE
        WHEN cmp.previous_citations = 0 AND cmp.recent_citations > 0
            THEN 'EMERGING'
        WHEN cmp.recent_citations > cmp.previous_citations
            THEN 'INCREASING'
        WHEN cmp.recent_citations < cmp.previous_citations
            THEN 'DECLINING'
        ELSE 'STABLE'
    END AS citation_trend
FROM comparison AS cmp
JOIN LEGAL_CASE AS lc
    ON lc.case_id = cmp.cited_case_id
ORDER BY citation_change DESC;

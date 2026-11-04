-- Each block is executed separately by scripts/setup-db.js (split on the SPLIT marker)
DROP PROCEDURE IF EXISTS sp_add_citation;
-- SPLIT
CREATE PROCEDURE sp_add_citation(IN p_citing INT, IN p_cited INT, IN p_date DATE, IN p_text TEXT, IN p_page INT)
BEGIN
  DECLARE v_id INT;
  DECLARE EXIT HANDLER FOR SQLEXCEPTION
  BEGIN
    ROLLBACK;
    RESIGNAL;
  END;
  START TRANSACTION;
    INSERT INTO Citation(citing_case_id, cited_case_id, citation_date, context_text, page_number)
    VALUES (p_citing, p_cited, p_date, p_text, p_page);
    SET v_id = LAST_INSERT_ID();
  COMMIT;
  SELECT v_id AS citation_id;
END
-- SPLIT
DROP FUNCTION IF EXISTS fn_citations_between;
-- SPLIT
CREATE FUNCTION fn_citations_between(p_case INT, p_from DATE, p_to DATE) RETURNS INT
READS SQL DATA
BEGIN
  DECLARE n INT;
  SELECT COUNT(*) INTO n FROM Citation
  WHERE cited_case_id = p_case AND citation_date BETWEEN p_from AND p_to;
  RETURN n;
END
-- SPLIT
DROP TRIGGER IF EXISTS trg_citation_bi;
-- SPLIT
CREATE TRIGGER trg_citation_bi BEFORE INSERT ON Citation FOR EACH ROW
BEGIN
  DECLARE d_citing DATE;
  DECLARE d_cited DATE;
  SELECT judgment_date INTO d_citing FROM Legal_Case WHERE case_id = NEW.citing_case_id;
  SELECT judgment_date INTO d_cited  FROM Legal_Case WHERE case_id = NEW.cited_case_id;
  IF d_cited > d_citing THEN
    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Invalid citation: a case cannot cite a later judgment';
  END IF;
  IF NEW.citation_date < d_citing THEN
    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Invalid citation: citation date precedes the citing judgment date';
  END IF;
END
-- SPLIT
DROP TRIGGER IF EXISTS trg_citation_ai;
-- SPLIT
CREATE TRIGGER trg_citation_ai AFTER INSERT ON Citation FOR EACH ROW
BEGIN
  UPDATE Legal_Case SET citation_count = citation_count + 1 WHERE case_id = NEW.cited_case_id;
  INSERT INTO Audit_Log(action, entity, entity_id) VALUES ('INSERT', 'Citation', NEW.citation_id);
END
-- SPLIT
DROP TRIGGER IF EXISTS trg_citation_ad;
-- SPLIT
CREATE TRIGGER trg_citation_ad AFTER DELETE ON Citation FOR EACH ROW
BEGIN
  UPDATE Legal_Case SET citation_count = citation_count - 1 WHERE case_id = OLD.cited_case_id;
  INSERT INTO Audit_Log(action, entity, entity_id) VALUES ('DELETE', 'Citation', OLD.citation_id);
END

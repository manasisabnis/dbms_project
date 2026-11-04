-- ===== DDL: CREATE / DROP / constraints / indexes / views =====
SET FOREIGN_KEY_CHECKS = 0;
DROP VIEW  IF EXISTS Landmark_Cases;
DROP VIEW  IF EXISTS v_case_details;
DROP TABLE IF EXISTS Audit_Log;
DROP TABLE IF EXISTS App_User;
DROP TABLE IF EXISTS Citation;
DROP TABLE IF EXISTS Statute;
DROP TABLE IF EXISTS Case_Judge;
DROP TABLE IF EXISTS Judge;
DROP TABLE IF EXISTS Legal_Case;
DROP TABLE IF EXISTS Court;
SET FOREIGN_KEY_CHECKS = 1;

CREATE TABLE Court (
  court_id INT AUTO_INCREMENT PRIMARY KEY,
  court_name VARCHAR(200) NOT NULL UNIQUE,
  court_level ENUM('Supreme Court','High Court','District Court','Tribunal') NOT NULL,
  location VARCHAR(100),
  established_year INT,
  CONSTRAINT chk_court_year CHECK (established_year IS NULL OR established_year BETWEEN 1600 AND 2100)
);

CREATE TABLE Legal_Case (
  case_id INT AUTO_INCREMENT PRIMARY KEY,
  case_name VARCHAR(500) NOT NULL,
  case_number VARCHAR(100) UNIQUE,
  judgment_date DATE NOT NULL,
  case_type VARCHAR(100),
  decision TEXT,
  citation_count INT NOT NULL DEFAULT 0,      -- maintained by triggers
  court_id INT NOT NULL,
  CONSTRAINT fk_case_court FOREIGN KEY (court_id) REFERENCES Court(court_id) ON UPDATE CASCADE,
  CONSTRAINT chk_case_name CHECK (CHAR_LENGTH(TRIM(case_name)) >= 3),
  CONSTRAINT chk_citation_count CHECK (citation_count >= 0)
);

CREATE TABLE Judge (
  judge_id INT AUTO_INCREMENT PRIMARY KEY,
  judge_name VARCHAR(200) NOT NULL,
  designation VARCHAR(100),
  appointed_date DATE,
  retired_date DATE,
  CONSTRAINT chk_judge_dates CHECK (retired_date IS NULL OR appointed_date IS NULL OR retired_date >= appointed_date)
);

CREATE TABLE Case_Judge (
  case_id INT NOT NULL,
  judge_id INT NOT NULL,
  role_in_case VARCHAR(100),
  CONSTRAINT pk_case_judge PRIMARY KEY (case_id, judge_id),
  CONSTRAINT fk_case_judge_case  FOREIGN KEY (case_id)  REFERENCES Legal_Case(case_id) ON DELETE CASCADE,
  CONSTRAINT fk_case_judge_judge FOREIGN KEY (judge_id) REFERENCES Judge(judge_id) ON DELETE CASCADE
);

-- Statute is a weak entity of Legal_Case (as in the ER diagram)
CREATE TABLE Statute (
  case_id INT NOT NULL,
  statute_id INT NOT NULL,
  act_name VARCHAR(300) NOT NULL,
  section VARCHAR(100),
  description TEXT,
  enactment_year INT,
  CONSTRAINT pk_statute PRIMARY KEY (case_id, statute_id),
  CONSTRAINT fk_statute_case FOREIGN KEY (case_id) REFERENCES Legal_Case(case_id) ON DELETE CASCADE,
  CONSTRAINT chk_enactment_year CHECK (enactment_year IS NULL OR enactment_year > 0)
);

CREATE TABLE Citation (
  citation_id INT AUTO_INCREMENT PRIMARY KEY,
  citing_case_id INT NOT NULL,
  cited_case_id INT NOT NULL,
  citation_date DATE NOT NULL,
  context_text TEXT,
  page_number INT,
  CONSTRAINT fk_citing_case FOREIGN KEY (citing_case_id) REFERENCES Legal_Case(case_id),
  CONSTRAINT fk_cited_case  FOREIGN KEY (cited_case_id)  REFERENCES Legal_Case(case_id),
  CONSTRAINT uq_citation_pair UNIQUE (citing_case_id, cited_case_id),
  CONSTRAINT chk_no_self_citation CHECK (citing_case_id <> cited_case_id),
  CONSTRAINT chk_page_number CHECK (page_number IS NULL OR page_number > 0)
);

CREATE TABLE App_User (
  user_id INT AUTO_INCREMENT PRIMARY KEY,
  username VARCHAR(50) NOT NULL UNIQUE,
  password_hash VARCHAR(100) NOT NULL,         -- bcrypt hash, never plain text
  role ENUM('admin','analyst') NOT NULL DEFAULT 'analyst',
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT chk_username CHECK (CHAR_LENGTH(username) >= 3)
);

CREATE TABLE Audit_Log (
  log_id INT AUTO_INCREMENT PRIMARY KEY,
  action VARCHAR(50) NOT NULL,
  entity VARCHAR(50) NOT NULL,
  entity_id INT,
  performed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ===== Indexes =====
CREATE INDEX idx_citation_cited  ON Citation(cited_case_id);
CREATE INDEX idx_citation_citing ON Citation(citing_case_id);
CREATE INDEX idx_citation_date   ON Citation(citation_date);
CREATE INDEX idx_case_judgment_date ON Legal_Case(judgment_date);
CREATE INDEX idx_case_type ON Legal_Case(case_type);
CREATE FULLTEXT INDEX ft_case_text ON Legal_Case(case_name, decision);   -- full-text search

-- ===== Views =====
CREATE VIEW Landmark_Cases AS
SELECT lc.case_id, lc.case_name, lc.judgment_date, COUNT(c.citation_id) AS citation_count
FROM Legal_Case lc JOIN Citation c ON lc.case_id = c.cited_case_id
GROUP BY lc.case_id, lc.case_name, lc.judgment_date
HAVING COUNT(c.citation_id) >= 5;

CREATE VIEW v_case_details AS
SELECT lc.case_id, lc.case_name, lc.case_number, lc.judgment_date, lc.case_type, lc.citation_count,
       co.court_name, co.court_level
FROM Legal_Case lc JOIN Court co ON co.court_id = lc.court_id;

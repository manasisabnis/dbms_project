CREATE DATABASE IF NOT EXISTS legal_citation_analyzer;
USE legal_citation_analyzer;

CREATE TABLE IF NOT EXISTS COURT (
    court_id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
    court_name VARCHAR(255) NOT NULL,
    location VARCHAR(255),
    court_level VARCHAR(100)
);

CREATE TABLE IF NOT EXISTS LEGAL_CASE (
    case_id BIGINT NOT NULL AUTO_INCREMENT PRIMARY KEY,
    case_name TEXT NOT NULL,
    case_number VARCHAR(255) UNIQUE,
    judgment_date DATE,
    court_id INT,
    case_type VARCHAR(255),
    decision TEXT,
    FOREIGN KEY (court_id) REFERENCES COURT(court_id)
);

CREATE TABLE IF NOT EXISTS JUDGE (
    judge_id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
    judge_name VARCHAR(255) NOT NULL,
    designation VARCHAR(100),
    appointed_date DATE,
    retired_date DATE
);

CREATE TABLE IF NOT EXISTS CASE_JUDGE (
    case_id BIGINT NOT NULL,
    judge_id INT NOT NULL,
    role_in_case VARCHAR(100),
    PRIMARY KEY (case_id, judge_id),
    FOREIGN KEY (case_id) REFERENCES LEGAL_CASE(case_id),
    FOREIGN KEY (judge_id) REFERENCES JUDGE(judge_id)
);

CREATE TABLE IF NOT EXISTS STATUTE (
    case_id BIGINT NOT NULL,
    statute_id INT NOT NULL AUTO_INCREMENT,
    act_name VARCHAR(255),
    section VARCHAR(100),
    description TEXT,
    enactment_year YEAR,
    PRIMARY KEY (case_id, statute_id),
    UNIQUE KEY uq_statute_id (statute_id),
    FOREIGN KEY (case_id) REFERENCES LEGAL_CASE(case_id)
);

CREATE TABLE IF NOT EXISTS CITATION (
    citation_id BIGINT NOT NULL AUTO_INCREMENT PRIMARY KEY,
    citing_case_id BIGINT NOT NULL,
    cited_case_id BIGINT NOT NULL,
    citation_date DATE,
    context_text TEXT,
    page_number INT,
    FOREIGN KEY (citing_case_id) REFERENCES LEGAL_CASE(case_id),
    FOREIGN KEY (cited_case_id) REFERENCES LEGAL_CASE(case_id),
    INDEX idx_citing_case (citing_case_id),
    INDEX idx_cited_case (cited_case_id)
);

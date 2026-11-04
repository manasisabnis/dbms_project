-- DDL demo for the viva: ALTER and DROP (run manually in mysql client)
ALTER TABLE Legal_Case ADD COLUMN language VARCHAR(50);
DESCRIBE Legal_Case;
ALTER TABLE Legal_Case DROP COLUMN language;
CREATE TABLE DDL_Test (test_id INT PRIMARY KEY, test_name VARCHAR(100));
DROP TABLE DDL_Test;
SHOW INDEX FROM Citation;
SHOW FULL TABLES WHERE TABLE_TYPE = 'VIEW';

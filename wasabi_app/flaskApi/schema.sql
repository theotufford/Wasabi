DROP TABLE IF EXISTS experiments;
DROP TABLE IF EXISTS experiments_fts;
DROP TABLE IF EXISTS pumpMap;
DROP TABLE IF EXISTS reagentLib;
DROP TABLE IF EXISTS authors;

CREATE TABLE reagentLib (
  name TEXT,
  metadata TEXT
);

CREATE TABLE authors (
  name TEXT,
  id INT,
  experiments TEXT
);

CREATE TABLE pumpMap (
  pumpID INT,
  reagent TEXT DEFAULT "empty"
);

CREATE TABLE experiments (
  ID TEXT,
  created TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  version INT DEFAULT 0,
  data TEXT,
  pastRunData TEXT
);

CREATE VIRTUAL TABLE experiments_fts USING fts5(
  ID,
  data,
  version,
  content='experiments'
);

CREATE TRIGGER experiments_ai AFTER INSERT ON experiments BEGIN
    INSERT INTO experiments_fts(rowid, ID, data, version)
    VALUES (new.rowid, new.ID, new.data, new.version);
END;

CREATE TRIGGER experiments_ad AFTER DELETE ON experiments BEGIN
    INSERT INTO experiments_fts(experiments_fts, rowid, ID, data, version)
    VALUES ('delete', old.rowid, old.ID, old.data, old.version);
END;

CREATE TRIGGER experiments_au AFTER UPDATE ON experiments BEGIN
    INSERT INTO experiments_fts(experiments_fts, rowid, ID, data, version)
    VALUES ('delete', old.rowid, old.ID, old.data, old.version);
    INSERT INTO experiments_fts(rowid, ID, data, version)
    VALUES (new.rowid, new.ID, new.data, old.version);
END;

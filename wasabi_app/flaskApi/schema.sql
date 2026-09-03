DROP TABLE IF EXISTS experiments;
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
  title TEXT,
  created TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  version INT DEFAULT 0,
  pastRunData TEXT,
  data TEXT
);

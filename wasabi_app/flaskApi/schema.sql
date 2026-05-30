DROP TABLE IF EXISTS experiments;
DROP TABLE IF EXISTS pumpMap;
DROP TABLE IF EXISTS reagentLib;
DROP TABLE IF EXISTS users;

CREATE TABLE reagentLib (
  name TEXT,
  json_data TEXT
);

CREATE TABLE authors (
  name TEXT,
  id INT,
  experiments TEXT
);

CREATE TABLE pumpMap (
  pumpID TEXT,
  reagent TEXT DEFAULT "empty"
);

CREATE TABLE experiments (
  title TEXT,
  experimentID INT,
  created TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  version INT DEFAULT 0,
  pastRunData TEXT,
  data TEXT, 
  machineCode TEXT,
  pastMachineCode TEXT,
  runcount INTEGER
);

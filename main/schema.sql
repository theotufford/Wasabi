DROP TABLE IF EXISTS experiments;
DROP TABLE IF EXISTS pumpMap;
DROP TABLE IF EXISTS reagentLib;

CREATE TABLE reagentLib (
  reagent TEXT
);

CREATE TABLE pumpMap (
  pumpID TEXT,
  reagent TEXT DEFAULT "empty",
  previousReagents TEXT
);

CREATE TABLE experiments (
  title TEXT,
  created TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  version INT DEFAULT 0,
  pastRunData TEXT,
  data TEXT, 
  machineCode TEXT,
  pastMachineCode TEXT,
  runcount INTEGER
);

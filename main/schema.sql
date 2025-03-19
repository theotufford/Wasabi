DROP TABLE IF EXISTS experiments;
DROP TABLE IF EXISTS plateatlas;
DROP TABLE IF EXISTS pumpatlas;

CREATE TABLE pumpatlas (
  pumpData TEXT
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
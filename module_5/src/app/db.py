# pylint: disable=missing-function-docstring
"""Database helper for ensuring the applicants table exists.

This module provides a global PostgreSQL connection pool and a
utility to create the ``applicants`` table if it does not already exist.

Schema
------

.. code-block:: sql

   CREATE TABLE IF NOT EXISTS applicants(
       p_id SERIAL PRIMARY KEY,
       program TEXT,
       comments TEXT,
       date_added DATE,
       url TEXT,
       status TEXT,
       term TEXT,
       us_or_international TEXT,
       gpa FLOAT,
       gre FLOAT,
       gre_v FLOAT,
       gre_aw FLOAT,
       degree TEXT,
       llm_generated_program TEXT,
       llm_generated_university TEXT
   );
"""

import os

from psycopg import sql
from psycopg_pool import ConnectionPool


PGHOST = os.getenv("PGHOST", "localhost")
PGDATABASE = os.getenv("PGDATABASE", "gradcafe")
PGUSER = os.getenv("PGUSER", "postgres")
PGPASSWORD = os.getenv("PGPASSWORD", "postgres")

DSN = f"postgresql://{PGUSER}:{PGPASSWORD}@{PGHOST}:5432/{PGDATABASE}"
pool = ConnectionPool(DSN, min_size=1, max_size=5)

CREATE_TABLE = sql.SQL("""
CREATE TABLE IF NOT EXISTS {tbl}(
  p_id SERIAL PRIMARY KEY,
  program TEXT,
  comments TEXT,
  date_added DATE,
  url TEXT UNIQUE,
  status TEXT,
  term TEXT,
  us_or_international TEXT,
  gpa FLOAT,
  gre FLOAT,
  gre_v FLOAT,
  gre_aw FLOAT,
  degree TEXT,
  llm_generated_program TEXT,
  llm_generated_university TEXT
)
""").format(tbl=sql.Identifier("applicants"))

def ensure_table() -> None:
    with pool.connection() as conn, conn.cursor() as cur:
        cur.execute(CREATE_TABLE)
        conn.commit()

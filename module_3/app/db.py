import psycopg_pool

# Configuration
DSN = "postgresql://postgres:postgres@localhost:5432/gradcafe"


# Global connection pool for the app
pool = psycopg_pool.ConnectionPool(DSN, min_size=1, max_size=5)

def ensure_table():
    ddl = """
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

    with pool.connection() as conn:
       with conn.cursor() as cur:
          cur.execute(ddl)
          conn.commit()
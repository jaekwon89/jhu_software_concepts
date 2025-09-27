"""Predefined database queries for applicant statistics.

This module provides query functions for the ``applicants`` table
in PostgreSQL. Each function opens a pooled connection, executes
a SELECT, and returns a Python value or structure.
"""

import psycopg_pool
import os
from psycopg import sql

PGHOST = os.getenv("PGHOST", "localhost")
PGDATABASE = os.getenv("PGDATABASE", "gradcafe")
PGUSER = os.getenv("PGUSER", "postgres")
PGPASSWORD = os.getenv("PGPASSWORD", "postgres")
DSN = f"postgresql://{PGUSER}:{PGPASSWORD}@{PGHOST}:5432/{PGDATABASE}"
pool = psycopg_pool.ConnectionPool(DSN, min_size=1, max_size=5)


def count_fall_2025() -> int:
    """Count the number of applicants for Fall 2025.

    :return: Number of Fall 2025 applicants.
    :rtype: int
    """
    stmt = sql.SQL("SELECT COUNT(*) FROM {tbl} WHERE term = {term}").format(
        tbl=sql.Identifier("applicants"), term=sql.Literal("Fall 2025")
    )
    with pool.connection() as conn, conn.cursor() as cur:
        cur.execute(stmt)
        return cur.fetchone()[0]


def percent_international() -> dict[str, int]:
    """Count applicants by citizenship type.

    :return: A dictionary with counts for international, US, and other.
    :rtype: dict[str, int]
    """
    stmt = sql.SQL("""
        SELECT
            COUNT(*) FILTER (WHERE us_or_international = 'International') AS int_c,
            COUNT(*) FILTER (WHERE us_or_international = 'American') AS us_c,
            COUNT(*) FILTER (WHERE us_or_international NOT IN ('International', 'American')) AS other_c
        FROM {tbl}
    """).format(tbl=sql.Identifier("applicants"))
    with pool.connection() as conn, conn.cursor() as cur:
        cur.execute(stmt)
        row = cur.fetchone()
    return {"international_count": row[0], "us_count": row[1], "other_count": row[2]}


def avg_scores() -> dict[str, float]:
    """Compute average GPA and GRE scores, handling NULLs.

    :return: Dictionary of averages.
    :rtype: dict[str, float]
    """
    stmt = sql.SQL("""
        SELECT
            COALESCE(AVG(gpa)    FILTER (WHERE gpa    BETWEEN 0.01 AND 4.3), 0.0),
            COALESCE(AVG(gre)    FILTER (WHERE gre    BETWEEN 130  AND 170), 0.0),
            COALESCE(AVG(gre_v)  FILTER (WHERE gre_v  BETWEEN 130  AND 170), 0.0),
            COALESCE(AVG(gre_aw) FILTER (WHERE gre_aw BETWEEN 0.01 AND 6.0), 0.0)
        FROM {tbl}
    """).format(tbl=sql.Identifier("applicants"))
    with pool.connection() as conn, conn.cursor() as cur:
        cur.execute(stmt)
        scores = cur.fetchone()
    return {"avg_gpa": scores[0], "avg_gre": scores[1], "avg_gre_v": scores[2], "avg_gre_aw": scores[3]}


def avg_gpa_american_fall2025() -> float:
    """Calculate average GPA for American applicants in Fall 2025.

    :return: Average GPA. Returns 0.0 if no valid records.
    :rtype: float
    """
    stmt = sql.SQL("""
        SELECT COALESCE(AVG(gpa), 0.0) FROM {tbl}
        WHERE us_or_international = 'American' AND term = 'Fall 2025'
        AND gpa BETWEEN 0.01 AND 4.3
    """).format(tbl=sql.Identifier("applicants"))
    with pool.connection() as conn, conn.cursor() as cur:
        cur.execute(stmt)
        return cur.fetchone()[0]


def acceptance_rate_fall2025() -> float:
    """Compute acceptance rate for Fall 2025.

    :return: Acceptance rate as a percentage. Returns 0.0 if no records.
    :rtype: float
    """
    stmt = sql.SQL("""
        SELECT COALESCE(
            (COUNT(*) FILTER (WHERE status LIKE '%Accepted%')::numeric * 100)
            / NULLIF(COUNT(*)::numeric, 0),
        0.0)
        FROM {tbl} WHERE term = 'Fall 2025'
    """).format(tbl=sql.Identifier("applicants"))
    with pool.connection() as conn, conn.cursor() as cur:
        cur.execute(stmt)
        return cur.fetchone()[0]


def avg_gpa_fall2025_acceptances() -> float:
    """Compute average GPA of accepted Fall 2025 applicants.

    :return: Average GPA. Returns 0.0 if no valid records.
    :rtype: float
    """
    stmt = sql.SQL("""
        SELECT COALESCE(AVG(gpa), 0.0) FROM {tbl}
        WHERE term = 'Fall 2025' AND status LIKE '%Accepted%'
        AND gpa BETWEEN 0.01 AND 4.3
    """).format(tbl=sql.Identifier("applicants"))
    with pool.connection() as conn, conn.cursor() as cur:
        cur.execute(stmt)
        return cur.fetchone()[0]


def count_jhu_masters_cs() -> int:
    """Count JHU Masters in Computer Science applicants.

    :return: Count of applicants.
    :rtype: int
    """
    stmt = sql.SQL("""
        SELECT COUNT(*) FROM {tbl}
        WHERE llm_generated_university = 'Johns Hopkins University'
        AND llm_generated_program = 'Computer Science' AND degree = 'Masters'
    """).format(tbl=sql.Identifier("applicants"))
    with pool.connection() as conn, conn.cursor() as cur:
        cur.execute(stmt)
        return cur.fetchone()[0]


def count_gt_phd_accept() -> int:
    """Count Georgetown PhD Computer Science acceptances in 2025.

    :return: Count of accepted applicants.
    :rtype: int
    """
    stmt = sql.SQL("""
        SELECT COUNT(*) FROM {tbl}
        WHERE term LIKE '%2025%' AND status LIKE '%Accepted%'
        AND llm_generated_university = 'Georgetown University'
        AND llm_generated_program = 'Computer Science' AND degree = 'PhD'
    """).format(tbl=sql.Identifier("applicants"))
    with pool.connection() as conn, conn.cursor() as cur:
        cur.execute(stmt)
        return cur.fetchone()[0]


def degree_counts_2025() -> list[tuple[str, int]]:
    """Return counts of applicants by degree for 2025.

    :return: List of (degree, count) tuples.
    :rtype: list[tuple[str, int]]
    """
    stmt = sql.SQL("""
        SELECT degree, COUNT(*) AS num_entries FROM {tbl}
        WHERE term LIKE '%2025%' GROUP BY degree ORDER BY num_entries DESC
    """).format(tbl=sql.Identifier("applicants"))
    with pool.connection() as conn, conn.cursor() as cur:
        cur.execute(stmt)
        return cur.fetchall()


def top_5_programs() -> list[tuple[str, int]]:
    """Return top 5 programs by number of 2025 applicants.

    :return: List of (program, count) tuples.
    :rtype: list[tuple[str, int]]
    """
    stmt = sql.SQL("""
        SELECT llm_generated_program AS program, COUNT(*) AS num_entries
        FROM {tbl} WHERE term LIKE '%2025%' GROUP BY llm_generated_program
        ORDER BY num_entries DESC LIMIT 5
    """).format(tbl=sql.Identifier("applicants"))
    with pool.connection() as conn, conn.cursor() as cur:
        cur.execute(stmt)
        return cur.fetchall()
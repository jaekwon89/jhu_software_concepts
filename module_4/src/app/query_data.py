"""Predefined database queries for applicant statistics.

This module provides query functions for the ``applicants`` table
in PostgreSQL. Each function opens a pooled connection, executes
a SELECT, and returns a Python value or structure.

Queries include:
1. Applicant count (Fall 2025)
2. Citizenship counts
3. Average GPA/GRE scores
4. Avg GPA for Americans in Fall 2025
5. Acceptance rate in Fall 2025
6. Avg GPA of accepted applicants in Fall 2025
7. Count of JHU Masters in CS
8. Count of Georgetown PhD CS acceptances (2025)
9. Degree counts in 2025
10. Top 5 programs in 2025
"""
import psycopg_pool


# Configuration
DSN = "postgresql://postgres:postgres@localhost:5432/gradcafe"
pool = psycopg_pool.ConnectionPool(DSN, min_size=1, max_size=5)

# 1. Applicant count (Fall 2025)
def count_fall_2025():
    """Count the number of applicants for Fall 2025.

    :return: Number of Fall 2025 applicants.
    :rtype: int
    """
    with pool.connection() as conn:
        with conn.cursor() as cur:      
            cur.execute(
                """
                SELECT COUNT(*)
                FROM applicants
                WHERE term = 'Fall 2025'
                """
            )
            applicant_count = cur.fetchone()[0]
    return applicant_count

# 2. Counts by citizenship (International / American / Other)
def percent_international():
    """Count applicants by citizenship type.

    Categories: International, American, Other.

    :return: Counts by category.
    :rtype: dict[str, int]
    """
    with pool.connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT 
                    COUNT(*) FILTER (
                        WHERE us_or_international = 'International'
                    ) AS international_count,
                    COUNT(*) FILTER (
                        WHERE us_or_international = 'American'
                    ) AS us_count,
                    COUNT(*) FILTER (
                        WHERE us_or_international 
                        NOT IN ('International', 'American')
                    ) AS other_count
                FROM applicants;
                """
            )
            row = cur.fetchone()
    return {
        "international_count": row[0],
        "us_count": row[1],
        "other_count": row[2]
    }

# 3. Average GPA/GREs with range filters (0 treated as missing)
def avg_scores():
    """Compute average GPA and GRE scores.

    GPA is valid if between 0.01 and 4.3.  
    GRE/GRE_V are valid if between 130 and 170.  
    GRE_AW is valid if between 0.01 and 6.

    :return: Dictionary of averages.
    :rtype: dict[str, float]
    """
    with pool.connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT
                    COALESCE(AVG(gpa)    FILTER (WHERE gpa    BETWEEN 0.01 AND 4.3), 0.0),
                    COALESCE(AVG(gre)    FILTER (WHERE gre    BETWEEN 130   AND 170), 0.0),
                    COALESCE(AVG(gre_v)  FILTER (WHERE gre_v  BETWEEN 130   AND 170), 0.0),
                    COALESCE(AVG(gre_aw) FILTER (WHERE gre_aw BETWEEN 0.01  AND 6),   0.0)
                FROM applicants;
                """
            )
            scores = cur.fetchone()
    return {
        "avg_gpa": scores[0],
        "avg_gre": scores[1],
        "avg_gre_v": scores[2],
        "avg_gre_aw": scores[3]
    }

# 4. Average GPA of American students in Fall 2025
def avg_gpa_american_fall2025():
    """Calculate average GPA for American applicants in Fall 2025.

    :return: Average GPA (or None if no valid records).
    :rtype: float or None
    """
    with pool.connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT AVG(gpa)
                FROM applicants
                WHERE us_or_international = 'American'
                    AND term = 'Fall 2025'
                    AND gpa BETWEEN 0.01 AND 4.3;
                """
            )
            us_gpa_2025 = cur.fetchone()[0]
    return us_gpa_2025

# 5. Acceptance rate in Fall 2025
def acceptance_rate_fall2025():
    """Compute acceptance rate for Fall 2025.

    :return: Acceptance rate (percentage).
    :rtype: float or None
    """
    with pool.connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT 
                    (COUNT(*) FILTER (WHERE status LIKE '%Accepted%')::numeric * 100)
                         / NULLIF(COUNT(*)::numeric, 0)
                    FROM applicants
                    WHERE term = 'Fall 2025';
                """
            )
            accept_rate_fa2025 = cur.fetchone()[0]
    return accept_rate_fa2025

# 6. Avg GPA of accepted applicants in Fall 2025
def avg_gpa_fall2025_acceptances():
    """Compute average GPA of accepted Fall 2025 applicants.

    :return: Average GPA or None.
    :rtype: float or None
    """
    with pool.connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT AVG(gpa)
                FROM applicants
                WHERE term = 'Fall 2025'
                    AND status LIKE '%Accepted%'
                    AND gpa BETWEEN 0.01 AND 4.3;
                """
            )
            avg_gpa_fa2025_accept = cur.fetchone()[0]
    return avg_gpa_fa2025_accept

# 7. Count: JHU Masters in Computer Science
def count_jhu_masters_cs():
    """Count JHU Masters in Computer Science applicants.

    :return: Count of applicants.
    :rtype: int
    """
    with pool.connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT COUNT(*)
                FROM applicants
                WHERE llm_generated_university = 'Johns Hopkins University'
                    AND llm_generated_program = 'Computer Science'
                    AND degree = 'Masters';
                """
            )
            result = cur.fetchone()[0]
    return result

# 8. Count: Georgetown PhD in CS acceptances in 2025
def count_gt_phd_accept():
    """Count Georgetown PhD Computer Science acceptances in 2025.

    :return: Count of accepted applicants.
    :rtype: int
    """
    with pool.connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT COUNT(*)
                FROM applicants
                WHERE term LIKE '%2025%'
                    AND status LIKE '%Accepted%'
                    AND llm_generated_university = 'Georgetown University'
                    AND llm_generated_program = 'Computer Science'
                    AND degree = 'PhD';
                """
            )
            result = cur.fetchone()[0]
    return result

# 9. Degree counts in 2025
def degree_counts_2025():
    """Return counts of applicants by degree for 2025.

    :return: List of (degree, count) tuples.
    :rtype: list[tuple[str, int]]
    """
    with pool.connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT 
                    degree, 
                    COUNT(*) AS num_entries
                FROM applicants
                WHERE term LIKE '%2025%'
                GROUP BY degree
                ORDER BY num_entries DESC;
                """
            )
            results = cur.fetchall()
    return results

# 10. Top 5 programs by entries in 2025
def top_5_programs():
    """Return top 5 programs by number of 2025 applicants.

    :return: List of (program, count) tuples.
    :rtype: list[tuple[str, int]]
    """
    with pool.connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT 
                    llm_generated_program AS program,
                    COUNT(*) AS num_entries
                FROM applicants
                WHERE term LIKE '%2025%'
                GROUP BY llm_generated_program
                ORDER BY num_entries DESC
                LIMIT 5;
                """
            )
            results = cur.fetchall()
    return results


def main():  # pragma: no cover
    """Run all queries and print formatted results.

    :return: None
    :rtype: NoneType
    """
    # Q1
    q1 = count_fall_2025()

    # Q2
    q2 = percent_international()
    q2_total = q2["international_count"] + q2["us_count"] + q2["other_count"]
    q2_pct = (q2["international_count"] / q2_total) * 100

    # Q3-Q10
    q3 = avg_scores()
    q4 = avg_gpa_american_fall2025()
    q5 = acceptance_rate_fall2025()
    q6 = avg_gpa_fall2025_acceptances()
    q7 = count_jhu_masters_cs()
    q8 = count_gt_phd_accept()
    q9 = degree_counts_2025()
    q10 = top_5_programs()

    print(f"Applicant count: {q1}")
    print(f"International count: {q2['international_count']}")
    print(f"US count: {q2['us_count']}")
    print(f"Other count: {q2['other_count']}")
    print(f"Percent International {q2_pct:.2f}")
    print(
        f"Average GPA: {q3['avg_gpa']}, "
        f"Average GRE: {q3['avg_gre']}, \n\t"
        f"Average GRE V: {q3['avg_gre_v']}, "
        f"Average GRE AW: {q3['avg_gre_aw']}"
        )
    print(f"Average GPA American: {q4}")
    print(f"Acceptance rate: {q5:.2f}")
    print(f"Average GPA for accpeted applicants in Fall 2025: {q6}")
    print(f"JHU Masters Computer Science count: {q7}")
    print(f"Accepted Georgetown PhD CS applicants in 2025: {q8}")

    print("Entries by degree in 2025:")
    for degree, num in q9:
        print(f"\t{degree}: {num}")
    print("Top 5 Programs by number of applicants in 2025:")
    for program, count in q10:
        print(f"\t{program}: {count}")

if __name__ == "__main__":  # pragma: no cover
    main()

import psycopg_pool


# Configuration
DSN = "postgresql://postgres:postgres@localhost:5432/gradcafe"
pool = psycopg_pool.ConnectionPool(DSN, min_size=1, max_size=5)

# ---------------------------------------------------------------------
# 1. Applicant count
# Number of entires applied for Fall 2025 in the database
# ---------------------------------------------------------------------
def count_fall_2025():
    with pool.connection() as conn:
        with conn.cursor() as cur:      
            cur.execute("""
                SELECT 
                    COUNT(*)
                    FROM applicants
                    WHERE term = 'Fall 2025'
            """)
            applicant_count = cur.fetchone()[0]
    return applicant_count

# ---------------------------------------------------------------------
# 2. Percent International
# A percentage of entries from international students 
# Getting a count for each feature value
# ---------------------------------------------------------------------
def percent_international():
    with pool.connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT 
                    COUNT(*) 
                        FILTER (WHERE us_or_international = 'International') 
                        AS international_count,
                    COUNT(*) 
                        FILTER (WHERE us_or_international = 'American')      
                        AS us_count,
                    COUNT(*) 
                        FILTER (WHERE us_or_international NOT IN ('International', 'American')) 
                        AS other_count
                FROM applicants;
            """)
            row = cur.fetchone()
    return {
        "international_count": row[0],
        "us_count": row[1],
        "other_count": row[2]
    }

# ---------------------------------------------------------------------
# 3. Average GPA and GRE scores
# Disregard data for out of range
# ---------------------------------------------------------------------
def avg_scores():
    with pool.connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT
                    AVG(gpa) 
                        FILTER (WHERE gpa BETWEEN 0.01 AND 4.3) 
                        AS avg_gpa,
                    AVG(gre) 
                        FILTER (WHERE gre BETWEEN 130 AND 170) 
                        AS avg_gre,
                    AVG(gre_v) 
                        FILTER (WHERE gre_v BETWEEN 130 AND 170) 
                        AS avg_gre_v,
                    AVG(gre_aw) 
                        FILTER (WHERE gre_aw BETWEEN 0.01 AND 6) 
                        AS avg_gre_aw
                FROM applicants;
            """)
            scores = cur.fetchone()
    return {
        "avg_gpa": scores[0],
        "avg_gre": scores[1],
        "avg_gre_v": scores[2],
        "avg_gre_aw": scores[3]
    }

# ---------------------------------------------------------------------
# 4. Average GPA for American in 2025
# Disregard data for out of range
# ---------------------------------------------------------------------
def avg_gpa_american_fall2025():
    with pool.connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT 
                    AVG(gpa)
                    FROM applicants
                    WHERE us_or_international = 'American'
                        AND term = 'Fall 2025'
                        AND gpa BETWEEN 0.01 AND 4.3;
            """)
            us_gpa_2025 = cur.fetchone()[0]
    return us_gpa_2025

# ---------------------------------------------------------------------
# 5. Acceptance rate in Fall 2025
# ---------------------------------------------------------------------
def acceptance_rate_fall2025():
    with pool.connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT 
                    COUNT(*) FILTER (WHERE status LIKE '%Accepted%')::numeric 
                         / COUNT(*)::numeric * 100
                    FROM applicants
                    WHERE term = 'Fall 2025';
            """)
            accept_rate_fa2025 = cur.fetchone()[0]
    return accept_rate_fa2025

# ---------------------------------------------------------------------
# 6. Average GPA of applicants accepted in Fall 2025
# ---------------------------------------------------------------------
def avg_gpa_fall2025_acceptances():
    with pool.connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT 
                    AVG(gpa)
                    FROM applicants
                    WHERE term = 'Fall 2025'
                        AND status LIKE '%Accepted%'
                        AND gpa BETWEEN 0.01 AND 4.3;
            """)
            avg_gpa_fa2025_accept = cur.fetchone()[0]
    return avg_gpa_fa2025_accept

# ---------------------------------------------------------------------
# 7. A number of entries - applied JHU for masters in CS
# ---------------------------------------------------------------------
def count_jhu_masters_cs():
    with pool.connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT
                    COUNT(*)
                    FROM applicants
                    WHERE llm_generated_university = 'Johns Hopkins University'
                        AND llm_generated_program = 'Computer Science'
                        AND degree = 'Masters'
                        AND status LIKE '%Accepted%';
            """)
            result = cur.fetchone()[0]
    return result

# ---------------------------------------------------------------------
# 8. Georgetown PhD in CS acceptances in 2025
# A number of 
# ---------------------------------------------------------------------
def count_gt_phd_aceept():
    with pool.connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT COUNT(*)
                FROM applicants
                WHERE term LIKE '%2025%'
                    AND status LIKE '%Accepted%'
                    AND llm_generated_university = 'Georgetown University'
                    AND llm_generated_program = 'Computer Science'
                    AND degree = 'PhD';
            """)
            result = cur.fetchone()[0]
    return result

def main():
    # Q1
    q1 = count_fall_2025()

    # Q2
    q2 = percent_international()
    q2_total = q2["international_count"] + q2["us_count"] + q2["other_count"]
    q2_pct = (q2["international_count"] / q2_total) * 100

    # Q3
    q3 = avg_scores()

    # Q4
    q4 = avg_gpa_american_fall2025()

    # Q5
    q5 = acceptance_rate_fall2025()

    # Q6
    q6 = avg_gpa_fall2025_acceptances()

    # Q7
    q7 = count_jhu_masters_cs()

    # Q8
    q8 = count_gt_phd_aceept()
    

    # Q9: additional question1

    # Q10: additional question2

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
    print(f"Acceptance percent: {q6}")
    print(f"JHU Masters Computer Science count: {q7}")
    print(f"Accepted Georgetown PhD CS applicants in 2025: {q8}")

if __name__ == "__main__":
    main()
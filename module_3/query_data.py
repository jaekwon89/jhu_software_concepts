
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
                SELECT COUNT(*)
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
            # A count for 'International'
            cur.execute("""
                SELECT COUNT(*)
                FROM applicants
                WHERE us_or_international = 'International'
            """)
            international_count = cur.fetchone()[0]

            # A count for 'American'
            cur.execute("""
                SELECT COUNT(*)
                FROM applicants
                WHERE us_or_international = 'American'
            """)
            us_count = cur.fetchone()[0]

            # A coutn for NOT 'International' and 'American'
            cur.execute("""
                SELECT COUNT(*)
                FROM applicants
                WHERE us_or_international NOT IN ('International', 'American')
            """)
            other_count = cur.fetchone()[0]

    return international_count, us_count, other_count




def main():
    q1 = count_fall_2025()
    q2_1, q2_2, q2_3 = percent_international()
    q2_4 = q2_1 / (q2_1 + q2_2 + q2_3) * 100

    print(f"Applicant count: {q1}")
    print(f"International count: {q2_1}")
    print(f"US count: {q2_2}")
    print(f"Other count: {q2_3}")
    print(f"Percent International {q2_4:.2f}")

if __name__ == "__main__":
    main()
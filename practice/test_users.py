# test_users.py
def test_user_creation(db_conn):
    assert db_conn == "fake_database_connection"

# test_orders.py
def test_order(db_conn):
    assert isinstance(db_conn, str)
# test_orders.py
def test_order(db_conn):
    assert isinstance(db_conn, str)
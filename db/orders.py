import sqlite3

def insert_order(order: dict, cursor) -> bool:
    """Add an order to the database.

    Parameters
    ----------
    order: a dictionary
        The order: order["order_id"], order["date"], order["refunded"],
        order["customer_id"], order["video_id"] and order["username"].
    cursor:
        The object used to query the database.

    Returns
    -------
    bool
        True if no error occurs, False otherwise.
    """
    try:
        query = """
            INSERT INTO "Order" (order_id,date,refunded,customer_id,video_id,username) VALUES(?,?,?,?,?,?);
        """
        cursor.execute(query, tuple(order.values()))
    except (sqlite3.Error, OSError) as error:
        print(error)
        return False

    return True

def insert_order_line(line: dict, cursor) -> bool:
    """Add a line to an existing order.

    Parameters
    ----------
    line: a dictionary
        The line: line["order_id"], line["product_id"], line["quantity"]
        and line["final_price"].
    cursor:
        The object used to query the database.

    Returns
    -------
    bool
        True if no error occurs, False otherwise.
    """
    try:
        query = """
            INSERT INTO Contains
            (order_id, product_id, quantity, final_price)
            VALUES (?, ?, ?, ?);
        """

        cursor.execute(query, tuple(line.values()))

        return True
    except (sqlite3.Error, OSError) as error:
        print(error)
        return False


def get_order(order_id: str, cursor) -> dict | None:
    """Return the order of specified id from the database.

    Returns the order, an EMPTY dictionary if no order has this id, or None
    if the query to the database failed.
    """
    try:
        query = """
            SELECT * FROM "Order" WHERE order_id = ?;
        """
        cursor.execute(query, (order_id,))

        order_info = cursor.fetchone()

        if order_info is None:
            return {}
        else:
            return dict(order_info)
    except (sqlite3.Error, OSError) as error:
        print(error)
        return None


def get_orders(cursor) -> list[dict] | None:
    """Return all orders from the database, or None if the query failed."""
    try:
        query = """
            SELECT * FROM "Order";
        """

        cursor.execute(query)

        return [dict(arg) for arg in cursor.fetchall()]
    except (sqlite3.Error, OSError) as error:
        print(error)
        return None


def get_orders_by_customer(customer_id: str, cursor) -> list[dict] | None:
    """Return every order of one customer, or None if the query failed."""
    try:
        query = """
            SELECT *
            FROM "Order"
            WHERE customer_id = ?;
        """

        cursor.execute(query, (customer_id,))
        orders = cursor.fetchall()

        return [dict(order) for order in orders]

    except (sqlite3.Error, OSError) as error:
        print(error)
        return None


def get_order_lines(order_id: str, cursor) -> list[dict] | None:
    """Return the lines of an order, with the category of each product.

    Returns the list of lines (possibly empty), or None if the query failed.
    """
    try:
        query = """
            SELECT Contains.order_id, Contains.product_id, Contains.quantity, Contains.final_price, Product.category FROM Contains JOIN Product ON Contains.product_id = Product.product_id WHERE Contains.order_id = ?;
        """

        cursor.execute(query, (order_id,))
        lines = cursor.fetchall()

        return [dict(line) for line in lines]

    except (sqlite3.Error, OSError) as error:
        print(error)
        return None


def get_order_total(order_id: str, cursor) -> float | None:
    """Return the total price of an order (0 if the order has no line).

    Returns None if the query to the database failed.
    """
    try:
        query = """
            SELECT SUM(quantity * final_price) FROM Contains WHERE order_id = ?;
        """

        cursor.execute(query, (order_id,))
        result = cursor.fetchone()

        if result[0] is None:
            return 0.0

        return float(result[0])

    except (sqlite3.Error, OSError) as error:
        print(error)
        return None

import sqlite3

def insert_customer(customer: dict, cursor) -> bool:
    """Add a customer to the database.

    Parameters
    ----------
    customer: a dictionary
        The customer: customer["customer_id"] and customer["country"].
    cursor:
        The object used to query the database.

    Returns
    -------
    bool
        True if no error occurs, False otherwise.
    """
    try:
        query = """
            INSERT INTO "Customer" (customer_id, country) VALUES(?,?);
        """
        cursor.execute(query, tuple(customer.values()))
    except (sqlite3.Error, OSError) as error:
        print(error)
        return False

    return True


def get_customer(customer_id: str, cursor) -> dict | None:
    """Return the customer of specified id from the database.

    Returns the customer, an EMPTY dictionary if no customer has this id, or
    None if the query to the database failed.
    """
    try:
        query = """
            SELECT * FROM "Customer" WHERE customer_id = ?;
        """
        cursor.execute(query, (customer_id,))

        customer_info = cursor.fetchone()

        if customer_info is None:
            return {}
        else:
            return dict(customer_info)
    except (sqlite3.Error, OSError) as error:
        print(error)
        return None


def get_customers(cursor) -> list[dict] | None:
    """Return all customers from the database, or None if the query failed."""
    try:
        query = """
            SELECT * FROM "Customer";
        """

        cursor.execute(query)

        return [dict(arg) for arg in cursor.fetchall()]
    except (sqlite3.Error, OSError) as error:
        print(error)
        return None


def update_customer_country(customer_id: str, country: str, cursor) -> bool:
    """Update the country of a customer. True if no error occurs."""
    try:
        query = """
            UPDATE "Customer" SET country = ? WHERE customer_id = ?;
        """

        cursor.execute(query, (country, customer_id,))

        return True
    except (sqlite3.Error, OSError) as error:
        print(error)
        return False


def get_products_bought_by_customer(customer_id: str, cursor) -> list[dict] | None:
    """Return every product the customer ordered at least once.

    A product bought in two orders is returned once. None if the query failed.
    """
    try:
        query = """
            SELECT order_id FROM "Order" WHERE customer_id = ?;
        """

        cursor.execute(query, (customer_id,))
        order_list = cursor.fetchall()

        product_list = []
        product_id_list = []

        for order_info in order_list:
            query = """
                SELECT * FROM "Contains" WHERE order_id = ?;
            """

            cursor.execute(query, (order_info["order_id"],))
            order_list = cursor.fetchall()

            for order_info2 in order_list:
                if not (order_info2["product_id"] in product_id_list):
                    product_id_list.append(order_info2["product_id"])
                    product_list.append(dict(order_info2))

        return product_list
    except (sqlite3.Error, OSError) as error:
        print(error)
        return None

def get_total_spent_by_customer(customer_id: str, cursor) -> float | None:
    """Return the total amount a customer has spent, refunds ignored.

    Returns 0 for a customer who never ordered, None if the query failed.
    """
    try:
        query = """
            SELECT order_id, refunded
            FROM "Order"
            WHERE customer_id = ?;
        """

        cursor.execute(query, (customer_id,))
        order_list = cursor.fetchall()

        total = 0.0

        for order_info in order_list:

            if order_info["refunded"] == 1:
                continue

            query = """
                SELECT SUM(quantity * final_price)
                FROM Contains
                WHERE order_id = ?;
            """

            cursor.execute(query, (order_info["order_id"],))
            result = cursor.fetchone()

            if result[0] is not None:
                total += float(result[0])

        return total

    except (sqlite3.Error, OSError) as error:
        print(error)
        return None

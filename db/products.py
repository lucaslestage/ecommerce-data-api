import sqlite3


def insert_product(product: dict, cursor) -> bool:
    """Add a product to the database."""
    try:
        query = """
            INSERT INTO Product
            (product_id, category, price, cost, stock)
            VALUES (?, ?, ?, ?, ?);
        """

        cursor.execute(
            query,
            (
                product["product_id"],
                product["category"],
                product["price"],
                product["cost"],
                product["stock"],
            )
        )

        return True

    except (sqlite3.Error, OSError) as error:
        print(error)
        return False


def get_product(product_id: str, cursor) -> dict | None:
    """Return one product."""
    try:
        query = """
            SELECT *
            FROM Product
            WHERE product_id = ?;
        """

        cursor.execute(query, (product_id,))
        product = cursor.fetchone()

        if product is None:
            return {}

        return dict(product)

    except (sqlite3.Error, OSError) as error:
        print(error)
        return None


def get_products(cursor) -> list[dict] | None:
    """Return all products."""
    try:
        query = """
            SELECT *
            FROM Product;
        """

        cursor.execute(query)
        products = cursor.fetchall()

        return [dict(product) for product in products]

    except (sqlite3.Error, OSError) as error:
        print(error)
        return None


def get_products_by_category(category: str, cursor) -> list[dict] | None:
    """Return all products of one category."""
    try:
        query = """
            SELECT *
            FROM Product
            WHERE category = ?;
        """

        cursor.execute(query, (category,))
        products = cursor.fetchall()

        return [dict(product) for product in products]

    except (sqlite3.Error, OSError) as error:
        print(error)
        return None


def update_product_stock(product_id: str, stock: int, cursor) -> bool:
    """Set the stock of a product."""
    try:
        query = """
            UPDATE Product SET stock = ? WHERE product_id = ?;
        """

        cursor.execute(query, (stock, product_id))

        return True

    except (sqlite3.Error, OSError) as error:
        print(error)
        return False


def decrease_product_stock(product_id: str, quantity: int, cursor) -> bool:
    """Decrease product stock without allowing a negative stock."""
    try:
        query = """
            SELECT stock
            FROM Product
            WHERE product_id = ?;
        """

        cursor.execute(query, (product_id,))
        product = cursor.fetchone()

        if product is None:
            return False

        if product["stock"] < quantity:
            return False

        query = """
            UPDATE Product
            SET stock = stock - ?
            WHERE product_id = ?;
        """

        cursor.execute(query, (quantity, product_id))

        return True

    except (sqlite3.Error, OSError) as error:
        print(error)
        return False


def get_low_stock_products(threshold: int, cursor) -> list[dict] | None:
    """Return products whose stock is strictly below threshold."""
    try:
        query = """
            SELECT *
            FROM Product
            WHERE stock < ?
            ORDER BY stock ASC;
        """

        cursor.execute(query, (threshold,))
        products = cursor.fetchall()

        return [dict(product) for product in products]

    except (sqlite3.Error, OSError) as error:
        print(error)
        return None


def get_quantity_sold(product_id: str, cursor) -> int | None:
    """Return the total quantity sold for a product."""
    try:
        query = """
            SELECT SUM(quantity)
            FROM Contains
            WHERE product_id = ?;
        """

        cursor.execute(query, (product_id,))
        result = cursor.fetchone()

        if result[0] is None:
            return 0

        return int(result[0])

    except (sqlite3.Error, OSError) as error:
        print(error)
        return None
from flask import Blueprint, request, jsonify

from db import get_db_connection, close_db_connection

import db.customers
import db.orders
import db.products


orders_bp = Blueprint("orders", __name__)


@orders_bp.route("/<order_id>")
def get_order(order_id):
    """Get an order, its lines and its total price.

    200 with the order, its "lines" and its "total"; 404 if no order has
    this id; 500 on error.
    """
    conn = get_db_connection()

    if conn is None:
        return "Error", 500

    cursor = conn.cursor()

    order = db.orders.get_order(order_id, cursor)

    if order is None:
        close_db_connection(cursor, conn)
        return jsonify({"error": "database error"}), 500

    if order == {}:
        close_db_connection(cursor, conn)
        return jsonify({"error": "order not found"}), 404

    lines = db.orders.get_order_lines(order_id, cursor)

    if lines is None:
        close_db_connection(cursor, conn)
        return jsonify({"error": "database error"}), 500

    total = db.orders.get_order_total(order_id, cursor)

    if total is None:
        close_db_connection(cursor, conn)
        return jsonify({"error": "database error"}), 500

    order["lines"] = lines
    order["total"] = total

    close_db_connection(cursor, conn)

    return jsonify(order), 200


@orders_bp.route("/", methods=["POST"])
def add_order_line():
    """Add a line to an existing order, and take the items out of the stock.

    The body of the POST request holds order_id, product_id, quantity and
    final_price.

    200 if the line is added, 400 if a field is missing, 404 if no order or
    no product has this id, 409 if the stock of the product is too low,
    500 on error.
    """
    data = request.get_json()

    if data is None:
        return jsonify({"error": "missing field"}), 400

    required = ("order_id", "product_id", "quantity", "final_price")

    if any(field not in data for field in required):
        return jsonify({"error": "missing field"}), 400

    conn = get_db_connection()

    if conn is None:
        return "Error", 500

    cursor = conn.cursor()

    order = db.orders.get_order(data["order_id"], cursor)

    if order is None:
        close_db_connection(cursor, conn)
        return jsonify({"error": "database error"}), 500

    if order == {}:
        close_db_connection(cursor, conn)
        return jsonify({"error": "order not found"}), 404

    product = db.products.get_product(data["product_id"], cursor)

    if product is None:
        close_db_connection(cursor, conn)
        return jsonify({"error": "database error"}), 500

    if product == {}:
        close_db_connection(cursor, conn)
        return jsonify({"error": "product not found"}), 404

    if product["stock"] < data["quantity"]:
        close_db_connection(cursor, conn)
        return jsonify({"error": "not enough stock"}), 409

    line = {
        "order_id": data["order_id"],
        "product_id": data["product_id"],
        "quantity": data["quantity"],
        "final_price": data["final_price"]
    }

    ok_line = db.orders.insert_order_line(line, cursor)

    if not ok_line:
        conn.rollback()
        close_db_connection(cursor, conn)
        return jsonify({"error": "database error"}), 500

    ok_stock = db.products.decrease_product_stock(
        data["product_id"],
        data["quantity"],
        cursor
    )

    if not ok_stock:
        conn.rollback()
        close_db_connection(cursor, conn)
        return jsonify({"error": "database error"}), 500

    conn.commit()

    close_db_connection(cursor, conn)

    return jsonify({"message": "line added"}), 200


@orders_bp.route("/customers/<customer_id>")
def get_customer(customer_id):
    """Get a customer, with what they ordered and what they spent.

    200 with the customer, its "products" and its "total_spent"; 404 if no
    customer has this id; 500 on error.
    """
    conn = get_db_connection()

    if conn is None:
        return "Error", 500

    cursor = conn.cursor()

    customer = db.customers.get_customer(customer_id, cursor)

    if customer is None:
        close_db_connection(cursor, conn)
        return jsonify({"error": "database error"}), 500

    if customer == {}:
        close_db_connection(cursor, conn)
        return jsonify({"error": "no customer has this id"}), 404

    products = db.customers.get_products_bought_by_customer(
        customer_id,
        cursor
    )

    if products is None:
        close_db_connection(cursor, conn)
        return jsonify({"error": "database error"}), 500

    total_spent = db.customers.get_total_spent_by_customer(
        customer_id,
        cursor
    )

    if total_spent is None:
        close_db_connection(cursor, conn)
        return jsonify({"error": "database error"}), 500

    customer["products"] = products
    customer["total_spent"] = total_spent

    close_db_connection(cursor, conn)

    return jsonify(customer), 200


@orders_bp.route("/customers/<customer_id>/orders")
def get_customer_orders(customer_id):
    """Get every order of one customer.

    200 with {"orders": [...]}, 404 if no customer has this id, 500 on error.
    """
    conn = get_db_connection()

    if conn is None:
        return "Error", 500

    cursor = conn.cursor()

    customer = db.customers.get_customer(customer_id, cursor)

    if customer is None:
        close_db_connection(cursor, conn)
        return jsonify({"error": "database error"}), 500

    if customer == {}:
        close_db_connection(cursor, conn)
        return jsonify({"error": "no customer has this id"}), 404

    orders = db.orders.get_orders_by_customer(
        customer_id,
        cursor
    )

    if orders is None:
        close_db_connection(cursor, conn)
        return jsonify({"error": "database error"}), 500

    close_db_connection(cursor, conn)

    return jsonify({"orders": orders}), 200
from flask import Blueprint, request, jsonify

from db import get_db_connection, close_db_connection

import db.products

products_bp = Blueprint("products", __name__)

@products_bp.route("/<product_id>")
def get_product(product_id):
    """Get a product in the database.

    200 with the product, 404 if no product has this id, 500 on error.
    """
    conn = get_db_connection()

    if conn is None:
        return "Error", 500

    cursor = conn.cursor()

    product = db.products.get_product(product_id, cursor)

    close_db_connection(cursor, conn)

    if product is None:
        return "Error", 500

    if product == {}:
        return "Product not found", 404

    return jsonify(product), 200


@products_bp.route("/<product_id>", methods=["PATCH"])
def update_product(product_id):
    """Set the stock of a product.
    The new stock must be passed in the data of the PATCH request.

    200 if the stock is updated, 400 if no stock is given in the request,
    404 if no product has this id, 500 on error.
    """
    conn = get_db_connection()

    if conn is None:
        return "Error", 500

    cursor = conn.cursor()

    product = db.products.get_product(product_id, cursor)

    if product is None:
        close_db_connection(cursor, conn)
        return "Error", 500

    if product == {}:
        close_db_connection(cursor, conn)
        return "Product not found", 404

    data = request.get_json()

    if data is None or "stock" not in data:
        close_db_connection(cursor, conn)
        return "No stock given", 400

    success = db.products.update_product_stock(
        product_id,
        data["stock"],
        cursor
    )

    if not success:
        close_db_connection(cursor, conn)
        return "Error", 500

    cursor.connection.commit()

    close_db_connection(cursor, conn)

    return jsonify({"message": "Stock updated"}), 200


@products_bp.route("/category/<category>")
def get_products_by_category(category):
    """Get every product of one category.

    200 with {"products": [...]}, 500 on error.
    """
    conn = get_db_connection()

    if conn is None:
        return "Error", 500

    cursor = conn.cursor()

    products = db.products.get_products_by_category(category, cursor)

    close_db_connection(cursor, conn)

    if products is None:
        return "Error", 500

    return jsonify({"products": products}), 200


@products_bp.route("/low_stock/<int:threshold>")
def get_low_stock_products(threshold):
    """Get every product whose stock is strictly below the threshold, the
    emptiest first.

    200 with {"products": [...]}, 500 on error.
    """
    conn = get_db_connection()

    if conn is None:
        return "Error", 500

    cursor = conn.cursor()

    products = db.products.get_low_stock_products(threshold, cursor)

    close_db_connection(cursor, conn)

    if products is None:
        return "Error", 500

    return jsonify({"products": products}), 200


@products_bp.route("/sold/<product_id>")
def get_quantity_sold(product_id):
    """Get the total number of items sold for a product.

    200 with {"quantity": n}, 404 if no product has this id, 500 on error.
    """
    conn = get_db_connection()

    if conn is None:
        return "Error", 500

    cursor = conn.cursor()

    product = db.products.get_product(product_id, cursor)

    if product is None:
        close_db_connection(cursor, conn)
        return "Error", 500

    if product == {}:
        close_db_connection(cursor, conn)
        return "Product not found", 404

    quantity = db.products.get_quantity_sold(product_id, cursor)

    close_db_connection(cursor, conn)

    if quantity is None:
        return "Error", 500

    return jsonify({"quantity": quantity}), 200
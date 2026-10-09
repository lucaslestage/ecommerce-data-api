from flask import Blueprint, jsonify

from db import get_db_connection, close_db_connection

import db.creators
import db.customers
import db.orders
import db.products
import db.videos

data_bp = Blueprint("data", __name__)


@data_bp.route("/creators")
def get_creators():
    """Get all creators in the database.

    200 with the list of creators, 500 on error.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    try :
        creators = db.creators.get_creators(cursor)
        if creators == None :
            return  jsonify({"error" : "database error"}), 500
        return  jsonify(creators), 200
    finally :
        conn.close()

@data_bp.route("/videos")
def get_videos():
    """Get all videos in the database.

    200 with the list of videos, 500 on error.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    try :
        videos = db.videos.get_videos(cursor)
        if videos == None :
            return  jsonify({"error" : "database error"}), 500
        return  jsonify(videos), 200
    finally:
        conn.close()


@data_bp.route("/products")
def get_products():
    """Get all products in the database.

    200 with the list of products, 500 on error.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    try :
        products = db.products.get_products(cursor)
        if products == None :
            return  jsonify({"error" : "database error"}), 500
        return  jsonify(products), 200
    finally :
        conn.close()


@data_bp.route("/customers")
def get_customers():
    """Get all customers in the database.

    200 with the list of customers, 500 on error.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    try :
        customers = db.customers.get_customers(cursor)
        if customers == None :
            return  jsonify({"error" : "database error"}), 500
        return  jsonify(customers), 200
    finally :
        conn.close()


@data_bp.route("/orders")
def get_orders():
    """Get all orders in the database.

    200 with the list of orders, 500 on error.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    try :
        orders = db.orders.get_orders(cursor)
        if orders == None :
            return  jsonify({"error" : "database error"}), 500
        return  jsonify(orders), 200
    finally :
        conn.close()

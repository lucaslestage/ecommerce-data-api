from flask import Flask

from db import init_database

from routes.users import users_bp

# TODO - import the other blueprints as you write them:
from routes.creators import creators_bp
from routes.products import products_bp
from routes.orders import orders_bp
from routes.data import data_bp
from routes.auth import auth_bp


def create_app():
    """Create a Flask application and add blueprints with all routes.

    Returns
    -------
    app
        the application created
    """
    # Create the default app
    app = Flask(__name__)

    # Add the first blueprint with all routes for the API
    # Take a look at the file ./routes/users.py to have more
    # details about the routes you have access to.
    app.register_blueprint(users_bp, url_prefix="/users")

    # TODO - ADD OTHER BLUEPRINTS
    #
    # Uncomment each line below once you have written the routes of that file,
    # and add the matching import at the top of this file.
    #
    # The url_prefix is prepended to every route of the blueprint:
    # get_product() is declared @products_bp.route("/<product_id>") and
    # products_bp is registered under "/products", so the full address is
    # /products/PROD_1. USE THESE PREFIXES: they are the addresses of the API
    # you are asked to build.
    #
    # Note that auth_bp is registered with NO url_prefix, so its route
    # "/login" is reached at /login and not at /auth/login.
    #
    # A blueprint you forget to register here answers 404 on every one of its
    # routes, which looks exactly like a route nobody has written yet.
    #
    app.register_blueprint(creators_bp, url_prefix="/creators")  # videos too
    app.register_blueprint(products_bp, url_prefix="/products")
    app.register_blueprint(orders_bp, url_prefix="/orders")   # customers too
    app.register_blueprint(data_bp, url_prefix="/data")
    app.register_blueprint(auth_bp)

    return app


# Entry point of the application
if __name__ == "__main__":
    app = create_app()
    init_database()
    app.run(port=5000, debug=False)

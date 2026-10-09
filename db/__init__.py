import sqlite3
import csv
import utils
import string

def get_db_connection():
    # Loads the app config into the dictionary app_config.
    app_config = utils.load_config()

    if not app_config:
        print("Error: while loading the app configuration")
        return None

    if not "db" in app_config:
        print("Error: db file not specified in the configuration")
        return None

    # From the configuration, gets the path to the database file.
    db_file = app_config["db"]

    # Open a connection to the database.
    conn = sqlite3.connect(db_file)
    conn.row_factory = sqlite3.Row

    return conn

def close_db_connection(cursor, conn):
    """Close a database connection and the cursor.

    Parameters
    ----------
    cursor
        The object used to query the database.
    conn
        The object used to manage the database connection.
    """
    cursor.close()
    conn.close()


def create_database(cursor, conn):
    """Creates the TikTok Shop database

    Parameters
    ----------
    cursor
        The object used to query the database.
    conn
        The object used to manage the database connection.

    Returns
    -------
    bool
        True if the database could be created, False otherwise.
    """

    # We open a transaction.
    # A transaction is a sequence of read/write statements that
    # have a permanent result in the database only if they all succeed.
    #
    # More concretely, in this function we create many tables in the database.
    # The transaction is therefore a sequence of CREATE TABLE statements such as :
    #
    # BEGIN
    # CREATE TABLE XXX
    # CREATE TABLE YYY
    # CREATE TABLE ZZZ
    # ....
    #
    # If no error occurs, all the tables are permanently created in the database.
    # If an error occurs while creating a table (for instance YYY), no table will be created, even those for which
    # the statement CREATE TABLE has already been executed (in this example, XXX).
    #
    # When we start a transaction with the statement BEGIN, we must end it with either COMMIT
    # or ROLLBACK.
    #
    # * COMMIT is called when no error occurs. After calling COMMIT, the result of all the statements in
    # the transaction is permanently written to the database. In our example, COMMIT results in actually creating all the tables
    # (XXX, YYY, ZZZ, ....)
    #
    # * ROLLBACK is called when any error occurs in the transaction. Calling ROLLBACK means that
    # the database is not modified (in our example, no table is created).
    #
    # * When possible, use the same field names as in the provided ER
    # diagram for fields, and Entity names for tables. For foreign keys, use the field
    # name of the referenced table followed by "_id". For example, for the foreign key
    # to reference a creator in the videos table, use "creator_id".
    #
    cursor.execute("BEGIN")

    # Create the tables. Referenced tables are created before the tables
    # that reference them through a foreign key.
    tables = {
        "User": """
            CREATE TABLE IF NOT EXISTS User(
                username TEXT PRIMARY KEY,
                password BINARY(256)
            );
            """,

        "Order": """
            CREATE TABLE IF NOT EXISTS "Order"(
                order_id TEXT PRIMARY KEY,
                date TEXT,
                refunded INTEGER,
                username TEXT REFERENCES User(username),
                customer_id TEXT REFERENCES Customer(customer_id),
                video_id TEXT REFERENCES Video(video_id)
            );
            """,

        "Creator": """
            CREATE TABLE IF NOT EXISTS Creator(
                creator_id TEXT PRIMARY KEY,
                name TEXT,
                niche TEXT,
                followers INTEGER
            );
            """,

        "Video": """
            CREATE TABLE IF NOT EXISTS Video(
                video_id TEXT PRIMARY KEY,
                views INTEGER,
                likes INTEGER,
                creator_id TEXT REFERENCES Creator(creator_id)
            );
            """,

        "Spend": """
            CREATE TABLE IF NOT EXISTS Spend(
                campaign_id TEXT PRIMARY KEY,
                amount INTEGER,
                video_id TEXT REFERENCES Video(video_id)
            );
            """,

        "Product": """
            CREATE TABLE IF NOT EXISTS Product(
                product_id TEXT PRIMARY KEY,
                category TEXT,
                price FLOAT,
                cost FLOAT,
                stock INTEGER,
                CHECK (price >= cost),
                CHECK (stock >= 0)
            );
            """,

        "Customer": """
            CREATE TABLE IF NOT EXISTS Customer(
                customer_id TEXT PRIMARY KEY,
                country TEXT
            );
            """,

        "Contains": """
            CREATE TABLE IF NOT EXISTS Contains(
                quantity INTEGER,
                final_price FLOAT,
                order_id TEXT REFERENCES "Order"(order_id),
                product_id TEXT REFERENCES Product(product_id),

                PRIMARY KEY (order_id, product_id)
            );
            """,
    }
    try:
        # To create the tables, we call the function cursor.execute() and we pass it the
        # CREATE TABLE statement as a parameter.
        # The function cursor.execute() can raise an exception sqlite3.Error.
        # That's why we write the code for creating the tables in a try...except block.
        for tablename in tables:
            print(f"Creating table {tablename}...", end=" ")
            cursor.execute(tables[tablename])
            print("OK")

    ###################################################################

    # Exception raised when something goes wrong while creating the tables.
    except sqlite3.Error as error:
        print("An error occurred while creating the tables: {}".format(error))
        # IMPORTANT : we rollback the transaction! No table is created in the database.
        conn.rollback()
        # Return False to indicate that something went wrong.
        return False

    # If we arrive here, that means that no error occurred.
    # IMPORTANT : we must COMMIT the transaction, so that all tables are actually created in the database.
    conn.commit()
    print("Database created successfully")
    # Returns True to indicate that everything went well!
    return True

def populate_database(cursor, conn, csv_file_names):
    """Populate the database with the data of several CSV files.

    Parameters
    ----------
    cursor
        The object used to query the database.
    conn
        The object used to manage the database connection.
    csv_file_names
        A dictionary {table name: path to the CSV file with its data}.
        The tables must be listed so that referenced tables come first.

    Returns
    -------
    boom
        True if the database is correctly populated, False otherwise.
    """
    try:
        for table_name, file_path in csv_file_names.items():
            with open(file_path, "r", encoding="utf-8") as f:
                data = csv.DictReader(f)

                for row in data:
                    for key, value in row.items():
                        if value.isdigit() and key != "order_id":
                            row[key] = int(value)

                        if key == "date":
                            key = "ordered_at"

                    query = """
                        INSERT INTO '""" + table_name + """' (""" + ",".join(row.keys()) + """) VALUES(""" + ",".join(["?"] * len(row)) + """);
                    """
                    cursor.execute(query, tuple(row.values()))
    except (sqlite3.Error, OSError) as error:
        print(error)
        conn.rollback()
        return False

    conn.commit()
    return True

def init_database():
    """Initialise the database by creating the database
    and populating it.
    """
    conn = get_db_connection()
    
    # get_db_connection() already printed why it failed; going on would
    # only bury that message under an AttributeError on None.
    if conn is None:
        return

    # The cursor is used to execute queries to the database.
    cursor = conn.cursor()

    # Creates the database. THIS IS THE FUNCTION THAT YOU'LL NEED TO MODIFY
    create_database(cursor, conn)

    csv_file_names = {
        "User": "data/user.csv",
        "Creator": "data/creator.csv",
        "Product": "data/product.csv",
        "Customer": "data/customer.csv",

        "Video": "data/video.csv",

        "Order": "data/order.csv",
        "Spend": "data/spend.csv",

        "Contains": "data/contains.csv",
    }

    populate_database(cursor, conn, csv_file_names)

    # Closes the connection to the database
    close_db_connection(cursor, conn)

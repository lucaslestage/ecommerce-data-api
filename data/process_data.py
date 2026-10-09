"""
Process the data in `data/raw/` to generate a new csv file for each entity in
the ER diagram.

Each generated CSV matches the columns expected by the SQL tables.
"""

import csv
import os

RAW_CSV_FILE = "data/raw/tiktokshop.csv"


def write_csv(path, fieldnames, rows):
    """Write rows to a CSV file."""
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def process_creators(raw_csv_file):
    """Write data/creator.csv: one line per creator."""
    if os.path.exists("data/creator.csv"):
        return "Already exists"

    creators = {}
    with open(raw_csv_file, "r", encoding="utf-8") as f:
        for raw in csv.DictReader(f):
            creator_id = raw["creator_id"]
            if creator_id not in creators:
                creators[creator_id] = {
                    "creator_id": creator_id,
                    "name": raw["creator_name"],
                    "niche": raw["creator_niche"],
                    "followers": raw["creator_followers"],
                }

    write_csv(
        "data/creator.csv",
        ["creator_id", "name", "niche", "followers"],
        creators.values(),
    )
    return "Done"


def process_videos(raw_csv_file):
    """Write data/video.csv: one line per video."""
    if os.path.exists("data/video.csv"):
        return "Already exists"

    videos = {}
    with open(raw_csv_file, "r", encoding="utf-8") as f:
        for raw in csv.DictReader(f):
            video_id = raw["video_id"]
            if video_id not in videos:
                videos[video_id] = {
                    "video_id": video_id,
                    "creator_id": raw["creator_id"],
                    "views": raw["video_views"],
                    "likes": raw["likes"],
                }

    write_csv(
        "data/video.csv",
        ["video_id", "creator_id", "views", "likes"],
        videos.values(),
    )
    return "Done"


def process_spends(raw_csv_file):
    """Write data/spend.csv: one line per advertising campaign."""
    if os.path.exists("data/spend.csv"):
        return "Already exists"

    spends = {}
    with open(raw_csv_file, "r", encoding="utf-8") as f:
        for raw in csv.DictReader(f):
            campaign_id = raw["campaign_id"]
            if campaign_id not in spends:
                spends[campaign_id] = {
                    "campaign_id": campaign_id,
                    "video_id": raw["video_id"],
                    "amount": raw["campaign_spend"],
                }

    write_csv(
        "data/spend.csv",
        ["campaign_id", "video_id", "amount"],
        spends.values(),
    )
    return "Done"


def process_products(raw_csv_file):
    """Write data/product.csv: one line per product."""
    if os.path.exists("data/product.csv"):
        return "Already exists"

    products = {}
    with open(raw_csv_file, "r", encoding="utf-8") as f:
        for raw in csv.DictReader(f):
            product_id = raw["product_id"]
            if product_id not in products:
                stock = raw["inventory_remaining"]
                # The raw file may store an integer stock as "9137.0".
                if stock != "":
                    stock = str(int(float(stock)))

                products[product_id] = {
                    "product_id": product_id,
                    "category": raw["product_category"],
                    "price": raw["product_price"],
                    "cost": raw["product_cost"],
                    "stock": stock,
                }

    write_csv(
        "data/product.csv",
        ["product_id", "category", "price", "cost", "stock"],
        products.values(),
    )
    return "Done"


def process_customers(raw_csv_file):
    """Write data/customer.csv: one line per customer."""
    if os.path.exists("data/customer.csv"):
        return "Already exists"

    customers = {}
    with open(raw_csv_file, "r", encoding="utf-8") as f:
        for raw in csv.DictReader(f):
            customer_id = raw["customer_id"]
            if customer_id not in customers:
                customers[customer_id] = {
                    "customer_id": customer_id,
                    "country": raw["country"],
                }

    write_csv(
        "data/customer.csv",
        ["customer_id", "country"],
        customers.values(),
    )
    return "Done"


users_list = [
    {
        "username": "patrickpouyanne",
        "password": "jeanmichel",
    },
    {
        "username": "lucaslestage",
        "password": "cs29",
    },
    {
        "username": "aureliendagneaux",
        "password": "cs29",
    },
]


def process_users(raw_csv_file):
    """Write data/user.csv: the employees of the shop."""
    if os.path.exists("data/user.csv"):
        return "Already exists"

    write_csv(
        "data/user.csv",
        ["username", "password"],
        users_list,
    )
    return "Done"


def process_orders(raw_csv_file):
    """Write data/order.csv: one line per order.

    Each order keeps the customer and video foreign keys required by the
    SQL schema. An employee is assigned deterministically to each order.
    """
    if os.path.exists("data/order.csv"):
        return "Already exists"

    orders = {}
    with open(raw_csv_file, "r", encoding="utf-8") as f:
        for raw in csv.DictReader(f):
            order_id = raw["order_id"]

            if order_id in orders:
                continue

            refunded = 1 if float(raw["refund_amount"] or 0) > 0 else 0
            username = users_list[len(orders) % len(users_list)]["username"]

            orders[order_id] = {
                "order_id": order_id,
                "date": raw["date"],
                "refunded": refunded,
                "customer_id": raw["customer_id"],
                "video_id": raw["video_id"],
                "username": username,
            }

    write_csv(
        "data/order.csv",
        [
            "order_id",
            "date",
            "refunded",
            "customer_id",
            "video_id",
            "username",
        ],
        orders.values(),
    )
    return "Done"


def process_contains(raw_csv_file):
    """Write data/contains.csv: one line per product of an order."""
    if os.path.exists("data/contains.csv"):
        return "Already exists"

    contains = {}
    with open(raw_csv_file, "r", encoding="utf-8") as f:
        for raw in csv.DictReader(f):
            key = (raw["order_id"], raw["product_id"])

            if key in contains:
                continue

            # In this dataset quantity_per_order is zero-based, hence +1.
            quantity = int(float(raw["quantity_per_order"])) + 1

            contains[key] = {
                "order_id": raw["order_id"],
                "product_id": raw["product_id"],
                "quantity": quantity,
                "final_price": raw["final_price"],
            }

    write_csv(
        "data/contains.csv",
        ["order_id", "product_id", "quantity", "final_price"],
        contains.values(),
    )
    return "Done"


if __name__ == "__main__":
    print(process_users(RAW_CSV_FILE))
    print(process_creators(RAW_CSV_FILE))
    print(process_videos(RAW_CSV_FILE))
    print(process_spends(RAW_CSV_FILE))
    print(process_products(RAW_CSV_FILE))
    print(process_customers(RAW_CSV_FILE))
    print(process_orders(RAW_CSV_FILE))
    print(process_contains(RAW_CSV_FILE))

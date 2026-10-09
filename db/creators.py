import sqlite3

def insert_creator(creator: dict, cursor) -> bool:
    """Add a creator to the database.

    Parameters
    ----------
    creator: a dictionary
        The creator: creator["creator_id"], creator["name"],
        creator["followers"] and creator["niche"].
    cursor:
        The object used to query the database.

    Returns
    -------
    bool
        True if no error occurs, False otherwise.
    """
    try:
        query = """
            INSERT INTO "Creator" (creator_id, name, followers, niche) VALUES(?,?,?,?);
        """
        cursor.execute(query, tuple(creator.values()))
    except (sqlite3.Error, OSError) as error:
        print(error)
        return False

    return True


def get_creator(creator_id: str, cursor) -> dict | None:
    """Return the creator of specified id from the database.

    Returns
    -------
    dict
        the creator, as a dictionary, if one has this id
        an EMPTY dictionary if no creator has this id
        None if the query to the database failed

    The three cases are distinct on purpose: "no such creator" is a successful
    query returning nothing (the route answers 404), while a failed query is
    an error (the route answers 500). Returning None for both would make the
    500 impossible to reach. Every get_<entity>() of ./db follows this rule.
    """
    try:
        query = """
            SELECT * FROM "Creator" WHERE creator_id = ?;
        """
        cursor.execute(query, (creator_id,))

        creator_info = cursor.fetchone()

        if creator_info is None:
            return {}
        else:
            return dict(creator_info)
    except (sqlite3.Error, OSError) as error:
        print(error)
        return None


def get_creators(cursor) -> list[dict] | None:
    """Return all creators from the database.

    Returns the list of creators (each one a dictionary, possibly an empty
    list), or None if the query to the database failed.
    """
    try:
        query = """
            SELECT * FROM "Creator";
        """

        cursor.execute(query)

        return [dict(arg) for arg in cursor.fetchall()]
    except (sqlite3.Error, OSError) as error:
        print(error)
        return None

def update_creator_followers(creator_id: str, followers: int, cursor) -> bool:
    """Update the number of followers of a creator.

    Returns True if no error occurs, False otherwise.
    """
    try:
        query = """
            UPDATE "Creator" SET followers = ? WHERE creator_id = ?;
        """

        cursor.execute(query, (followers, creator_id,))

        return True
    except (sqlite3.Error, OSError) as error:
        print(error)
        return False


def get_creator_videos(creator_id: str, cursor) -> list[dict] | None:
    """Return the videos of a creator, the most viewed first.

    Returns the list of videos (possibly empty), or None if the query failed.
    """
    try:
        query = """
            SELECT * FROM "Video" WHERE creator_id = ? ORDER BY views DESC;
        """

        cursor.execute(query, (creator_id,))
        
        return [dict(arg) for arg in cursor.fetchall()]
    except (sqlite3.Error, OSError) as error:
        print(error)
        return None


def get_creators_without_sales(cursor) -> list[dict] | None:
    """Return the creators none of whose videos ever triggered an order.

    Returns the list of creators (possibly empty), or None if the query failed.
    """
    try:
        query = """
            SELECT * FROM "Creator";
        """

        cursor.execute(query)
        creators_list = cursor.fetchall()

        creator_with_no_order = []

        for creator_info in creators_list:
            query = """
                SELECT video_id FROM "Video" WHERE creator_id = ?;
            """

            cursor.execute(query, (creator_info["creator_id"],))
            video_list = cursor.fetchall()

            count_video_no_order = 0

            for video_info in video_list:
                query = """
                    SELECT * FROM "Order" WHERE video_id = ?;
                """

                cursor.execute(query, (video_info["video_id"],))
                has_video_order = cursor.fetchone() #fetchone is enough

                if has_video_order is None:
                    count_video_no_order += 1

            if count_video_no_order == len(video_list):
                creator_with_no_order.append(dict(creator_info))

        return creator_with_no_order
    except (sqlite3.Error, OSError) as error:
        print(error)
        return None

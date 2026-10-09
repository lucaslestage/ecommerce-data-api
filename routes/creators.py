from flask import Blueprint, request, jsonify

from db import get_db_connection, close_db_connection

import db.creators
import db.videos

creators_bp = Blueprint("creators", __name__)


@creators_bp.route("/<creator_id>")
def get_creator(creator_id):
    """Get a creator in the database.

    200 with the creator, 404 if no creator has this id, 500 on error.
    """
    conn = get_db_connection()

    if conn is None:
        return "Error", 500

    cursor = conn.cursor()

    creator_info = db.creators.get_creator(creator_id, cursor)
    
    close_db_connection(cursor, conn)

    if creator_info is None:
        return "Error", 500
    
    if creator_info == {}:
        return "Creator not found", 404

    return jsonify(creator_info), 200


@creators_bp.route("/<creator_id>", methods=["PATCH"])
def update_creator(creator_id):
    """Update a creator in the database based on its id.
    The new number of followers must be passed in the data of the PATCH
    request.

    200 if the creator is updated, 400 if no followers are given in the
    request, 404 if no creator has this id, 500 on error.
    """
    conn = get_db_connection()

    if conn is None:
        return "Error", 500

    cursor = conn.cursor()

    creator_info = db.creators.get_creator(creator_id, cursor)

    if creator_info is None:
        close_db_connection(cursor, conn)
        return "Error", 500

    if creator_info == {}:
        close_db_connection(cursor, conn)
        return "Creator not found", 404

    data = request.get_json()

    if data is None or "followers" not in data:
        close_db_connection(cursor, conn)
        return "lack of information", 400

    success = db.creators.update_creator_followers(
        creator_id,
        data["followers"],
        cursor
    )

    if not success:
        close_db_connection(cursor, conn)
        return "The update cannot be done", 500

    cursor.connection.commit()

    close_db_connection(cursor, conn)

    return jsonify({"message": "Followers updated"}), 200


@creators_bp.route("/<creator_id>/videos")
def get_creator_videos(creator_id):
    """Get the videos of a creator, the most viewed first.

    200 with {"videos": [...]}, 404 if no creator has this id, 500 on error.
    """
    conn = get_db_connection()

    if conn is None:
        return "Error", 500

    cursor = conn.cursor()

    creator = db.creators.get_creator(creator_id, cursor)

    if creator is None:
        close_db_connection(cursor, conn)
        return "Error", 500

    if creator == {}:
        close_db_connection(cursor, conn)
        return "Creator not found", 404

    videos = db.creators.get_creator_videos(creator_id, cursor)

    close_db_connection(cursor, conn)

    if videos is None:
        return "Error", 500

    return jsonify({"videos": videos}), 200


@creators_bp.route("/videos/<video_id>")
def get_video(video_id):
    """Get a video in the database.

    200 with the video, 404 if no video has this id, 500 on error.
    """
    conn = get_db_connection()

    if conn is None:
        return "Error", 500

    cursor = conn.cursor()

    video = db.videos.get_video(video_id, cursor)

    close_db_connection(cursor, conn)

    if video is None:
        return "Error", 500

    if video == {}:
        return "Video not found", 404

    return jsonify(video), 200


@creators_bp.route("/videos/count/<video_id>")
def get_video_orders_count(video_id):
    """Get the number of orders one video triggered.

    200 with {"count": n}, 404 if no video has this id, 500 on error.
    """
    conn = get_db_connection()

    if conn is None:
        return "Error", 500

    cursor = conn.cursor()

    video = db.videos.get_video(video_id, cursor)

    if video is None:
        close_db_connection(cursor, conn)
        return "Error", 500

    if video == {}:
        close_db_connection(cursor, conn)
        return "Video not found", 404

    count = db.videos.get_video_orders_count(video_id, cursor)

    close_db_connection(cursor, conn)

    if count is None:
        return "Error", 500

    return jsonify({"count": count}), 200


@creators_bp.route("/videos/best/<int:n>")
def get_best_videos(n):
    """Get the n videos with the highest net revenue.

    200 with {"videos": [...]}, 500 on error.
    """
    conn = get_db_connection()

    if conn is None:
        return "Error", 500

    cursor = conn.cursor()

    videos = db.videos.get_best_videos(n, cursor)

    close_db_connection(cursor, conn)

    if videos is None:
        return "Error", 500

    return jsonify({"videos": videos}), 200
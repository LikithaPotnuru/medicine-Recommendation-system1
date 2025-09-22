from flask import Flask, request, jsonify
from flask_cors import CORS
import mysql.connector
from mysql.connector import Error
from datetime import datetime

app = Flask(__name__)
CORS(app)

def get_db_connection():
    try:
        return mysql.connector.connect(
            host="localhost",
            user="root",
            password="bvganapathi3600@gmail.com",  # replace with your password
            database="medicine_db"
        )
    except Error as e:
        raise e

@app.route("/")
def home():
    return jsonify({"message": "✅ Medicine Recommendation API is running!"})

# -------------------- Recommend --------------------
@app.route("/recommend/<username>", methods=["GET"])
def recommend(username):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # ensure user
    cursor.execute("SELECT user_id FROM users WHERE username = %s", (username,))
    user = cursor.fetchone()
    new_user = False
    if not user:
        cursor.execute("INSERT INTO users (username) VALUES (%s)", (username,))
        conn.commit()
        user_id = cursor.lastrowid
        new_user = True
    else:
        user_id = user['user_id']

    # history
    cursor.execute("""
        SELECT m.id, m.name, m.uses, m.stock, m.price
        FROM purchase_history ph
        JOIN medicines m ON ph.medicine_id = m.id
        WHERE ph.user_id = %s AND ph.action='purchase'
        ORDER BY ph.timestamp DESC
    """, (user_id,))
    history = cursor.fetchall() or []

    # collaborative
    collaborative = []
    if history:
        cursor.execute("""
            SELECT DISTINCT m.id, m.name, m.uses, m.stock, m.price, COUNT(*) as freq
            FROM purchase_history ph1
            JOIN purchase_history ph2 ON ph1.medicine_id = ph2.medicine_id
            JOIN medicines m ON m.id = ph2.medicine_id
            WHERE ph1.user_id = %s AND ph2.user_id != %s
              AND ph2.medicine_id NOT IN (
                  SELECT medicine_id FROM purchase_history WHERE user_id = %s
              )
            GROUP BY m.id
            ORDER BY freq DESC
            LIMIT 5
        """, (user_id, user_id, user_id))
        collaborative = cursor.fetchall() or []

    # top_meds
    top_meds = []
    if new_user or not history:
        cursor.execute("""
            SELECT m.id, m.name, m.uses, m.stock, m.price, COUNT(ph.id) as freq
            FROM medicines m
            LEFT JOIN purchase_history ph ON m.id = ph.medicine_id AND ph.action='purchase'
            GROUP BY m.id
            ORDER BY freq DESC
            LIMIT 5
        """)
        top_meds = cursor.fetchall() or []

    cursor.close()
    conn.close()

    return jsonify({
        "message": "✅ Recommendations fetched successfully!",
        "user_id": user_id,
        "new_user": new_user,
        "history": history,
        "collaborative": collaborative,
        "top_meds": top_meds
    })

# -------------------- Search --------------------
@app.route("/search", methods=["GET"])
def search_medicines():
    query = request.args.get("query", "").strip().lower()
    if not query:
        return jsonify({"message": "Empty query", "results": []})

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    like_query = f"%{query}%"
    cursor.execute("""
        SELECT id, name, uses, stock, price
        FROM medicines
        WHERE LOWER(name) LIKE %s OR LOWER(uses) LIKE %s
        LIMIT 20
    """, (like_query, like_query))
    results = cursor.fetchall() or []
    cursor.close()
    conn.close()

    return jsonify({"message": f"Found {len(results)} medicine(s).", "results": results})

# -------------------- Purchase --------------------
@app.route("/purchase", methods=["POST"])
def purchase_medicine():
    data = request.json or {}
    username = data.get("username")
    medicine_id = data.get("medicine_id")
    quantity = int(data.get("quantity", 1))

    if not username or medicine_id is None:
        return jsonify({"error": "Username and medicine_id required"}), 400

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # ensure user
    cursor.execute("SELECT user_id FROM users WHERE username = %s", (username,))
    user = cursor.fetchone()
    if not user:
        cursor.execute("INSERT INTO users (username) VALUES (%s)", (username,))
        conn.commit()
        user_id = cursor.lastrowid
    else:
        user_id = user['user_id']

    # check medicine exists
    cursor.execute("SELECT id, name, stock, price FROM medicines WHERE id = %s", (medicine_id,))
    med = cursor.fetchone()
    if not med:
        cursor.close()
        conn.close()
        return jsonify({"error": "Medicine not found"}), 404

    # check stock
    if med['stock'] < quantity:
        cursor.close()
        conn.close()
        return jsonify({"error": f"Only {med['stock']} units of '{med['name']}' are available!"}), 400

    # insert purchase with price
    now = datetime.now()
    total_price = med['price'] * quantity  # total for this purchase
    cursor.execute("""
        INSERT INTO purchase_history 
        (user_id, medicine_id, action, username, medicine_name, timestamp, quantity, price)
        VALUES (%s, %s, 'purchase', %s, %s, %s, %s, %s)
    """, (user_id, medicine_id, username, med['name'], now, quantity, total_price))

    # update stock
    cursor.execute("UPDATE medicines SET stock = stock - %s WHERE id = %s", (quantity, medicine_id))
    conn.commit()

    # fetch new stock
    cursor.execute("SELECT stock FROM medicines WHERE id = %s", (medicine_id,))
    new_stock = cursor.fetchone()['stock']

    cursor.close()
    conn.close()

    return jsonify({
        "message": f"Medicine '{med['name']}' purchased successfully by {username} (Quantity: {quantity})!",
        "stock": new_stock
    })

# -------------------- History --------------------
@app.route("/history/<username>", methods=["GET"])
def history(username):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT user_id FROM users WHERE username = %s", (username,))
    user = cursor.fetchone()
    if not user:
        cursor.close()
        conn.close()
        return jsonify({"error": "User not found"}), 404

    user_id = user["user_id"]
    cursor.execute("""
        SELECT m.id, m.name, m.uses, m.stock, m.price, ph.timestamp, ph.quantity
        FROM purchase_history ph
        JOIN medicines m ON ph.medicine_id = m.id
        WHERE ph.user_id = %s AND ph.action='purchase'
        ORDER BY ph.timestamp DESC
    """, (user_id,))
    purchases = cursor.fetchall() or []

    cursor.close()
    conn.close()
    return jsonify({"message": "✅ Purchase history fetched.", "history": purchases})

# -------------------- Substitutes --------------------
@app.route("/substitutes/<int:medicine_id>", methods=["GET"])
def get_substitutes(medicine_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    # Substitute logic: same uses
    cursor.execute("""
        SELECT id, name, uses, stock, price
        FROM medicines
        WHERE id != %s AND uses IN (
            SELECT uses FROM medicines WHERE id = %s
        )
        LIMIT 5
    """, (medicine_id, medicine_id))
    subs = cursor.fetchall() or []
    
    cursor.close()
    conn.close()
    return jsonify({"substitutes": subs})

if __name__ == "__main__":
    app.run(debug=True)

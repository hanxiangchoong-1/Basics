from flask import Blueprint, jsonify, request
from argon2.exceptions import VerifyMismatchError
from db_utils import get_db_connection
from auth_utils import hash_password, verify_password

admin_bp = Blueprint('admin', __name__)

@admin_bp.route('/view_tables', methods=['GET'])
def view_tables():
    conn = get_db_connection()
    cur = conn.cursor()

    # Get list of tables
    cur.execute("""
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public'
    """)
    tables = cur.fetchall()
    
    result = []
    for table in tables:
        table_info = {"name": table[0], "columns": []}
        
        # Get column information for each table
        cur.execute(f"""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = '{table[0]}'
        """)
        columns = cur.fetchall()
        for column in columns:
            table_info["columns"].append({
                "name": column[0],
                "type": column[1]
            })
        
        # If it's the users table, show the number of users
        if table[0] == 'users':
            cur.execute("SELECT COUNT(*) FROM users")
            user_count = cur.fetchone()[0]
            table_info["total_users"] = user_count
        
        result.append(table_info)
    
    cur.close()
    conn.close()

    return jsonify(result)

@admin_bp.route('/delete_users_table', methods=['POST'])
def delete_users_table():
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("DROP TABLE IF EXISTS users")
        conn.commit()
        return jsonify({'message': 'Users table deleted successfully'}), 200
    except Exception as e:
        conn.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        cur.close()
        conn.close()

@admin_bp.route('/update_password', methods=['PUT'])
def update_password():
    data = request.get_json()
    username = data.get('username')
    old_password = data.get('old_password')
    new_password = data.get('new_password')

    if not all([username, old_password, new_password]):
        return jsonify({'error': 'Username, old password, and new password are required'}), 400

    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)

    try:
        # First, verify the old password
        cur.execute("SELECT password FROM users WHERE username = %s", (username,))
        user = cur.fetchone()
        if not user or not verify_password(user['password'], old_password):
            return jsonify({'error': 'Invalid credentials'}), 401

        # If old password is correct, update to new password
        hashed_new_password = hash_password(new_password)
        cur.execute("UPDATE users SET password = %s WHERE username = %s", (hashed_new_password, username))
        conn.commit()
        return jsonify({'message': 'Password updated successfully'}), 200
    except Exception as e:
        conn.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        cur.close()
        conn.close()

@admin_bp.route('/delete_user/<username>', methods=['DELETE'])
def delete_user(username):
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("DELETE FROM users WHERE username = %s", (username,))
        if cur.rowcount == 0:
            return jsonify({'error': 'User not found'}), 404
        conn.commit()
        return jsonify({'message': f'User {username} deleted successfully'}), 200
    except Exception as e:
        conn.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        cur.close()
        conn.close()
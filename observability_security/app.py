from flask import Flask, request, jsonify
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from admin_routes import admin_bp
from db_utils import get_db_connection
from auth_utils import hash_password, verify_password
import psycopg2
from psycopg2.extras import RealDictCursor
import os
from dotenv import load_dotenv


# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)
app.register_blueprint(admin_bp, url_prefix='/admin')
app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY')
jwt = JWTManager(app)

# Initialize the database
def init_db():
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        # Check if the users table already exists
        cur.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'public' AND table_name = 'users'
            );
        """)
        table_exists = cur.fetchone()[0]

        if not table_exists:
            cur.execute('''
                CREATE TABLE users (
                    id SERIAL PRIMARY KEY,
                    username VARCHAR(50) UNIQUE NOT NULL,
                    password VARCHAR(255) NOT NULL
                )
            ''')
            print("Users table created successfully.")
        else:
            print("Users table already exists. Skipping creation.")

        conn.commit()
    except Exception as e:
        conn.rollback()
        print(f"An error occurred: {e}")
    finally:
        cur.close()
        conn.close()

# Registration API
@app.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({'error': 'Username and password are required'}), 400

    hashed_password = hash_password(password)

    conn = get_db_connection()
    cur = conn.cursor()

    try:
        cur.execute("INSERT INTO users (username, password) VALUES (%s, %s)",
                    (username, hashed_password))
        conn.commit()
    except psycopg2.IntegrityError:
        conn.rollback()
        return jsonify({'error': 'Username already exists'}), 409
    finally:
        cur.close()
        conn.close()

    return jsonify({'message': 'User registered successfully'}), 201

# Login API
@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({'error': 'Username and password are required'}), 400

    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)

    cur.execute("SELECT * FROM users WHERE username = %s", (username,))
    user = cur.fetchone()

    cur.close()
    conn.close()

    if not user or not verify_password(user['password'], password):
        return jsonify({'error': 'Invalid credentials'}), 401

    # Create the JWT token
    access_token = create_access_token(identity=username)
    return jsonify(access_token=access_token), 200

if __name__ == '__main__':
    init_db()
    app.run(debug=True, port=5000)
I have a demo flask app that I'm intending to use to test elastic security and observability applications:

```python
app.py 
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
```

It imports these other utilities: 

```python
admin_routes.py 

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
```

and utils:

```python

auth_utils.py 

from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError

ph = PasswordHasher()

def hash_password(password):
    return ph.hash(password)

def verify_password(stored_hash, provided_password):
    try:
        ph.verify(stored_hash, provided_password)
        return True
    except VerifyMismatchError:
        return False

db_utils.py 

import psycopg2
import os

from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

DB_PARAMS = {
    'dbname': os.getenv('DB_NAME'),
    'user': os.getenv('DB_USER'),
    'password': os.getenv('DB_PASSWORD'),
    'host': os.getenv('DB_HOST'),
    'port': os.getenv('DB_PORT')
}

def get_db_connection():
    return psycopg2.connect(**DB_PARAMS)
```

It will be relying on this postgresql database to serve as a file system and to get user credentials.

```bash
docker-compose.yml
services:
  db:
    image: postgres:13
    container_name: demo-postgres
    environment:
      POSTGRES_DB: demoapp
      POSTGRES_USER: demouser
      POSTGRES_PASSWORD: demopass
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data

volumes:
  postgres_data:
  ```

I have this env file which should contain configuration variables

```bash
DB_NAME=demoapp
DB_USER=demouser
DB_PASSWORD=demopass
DB_HOST=localhost
DB_PORT=5432
```

I have this set of test api calls to assess app's health:

```python
import requests
import json

BASE_URL = "http://localhost:5000"

def test_register(username, password):
    url = f"{BASE_URL}/register"
    data = {"username": username, "password": password}
    response = requests.post(url, json=data)
    print(f"Register Response (Status Code: {response.status_code}):")
    print(json.dumps(response.json(), indent=2))
    print()

def test_login(username, password):
    url = f"{BASE_URL}/login"
    data = {"username": username, "password": password}
    response = requests.post(url, json=data)
    print(f"Login Response (Status Code: {response.status_code}):")
    print(json.dumps(response.json(), indent=2))
    print()

def test_view_tables():
    url = f"{BASE_URL}/admin/view_tables"
    response = requests.get(url)
    print(f"View Tables Response (Status Code: {response.status_code}):")
    print(json.dumps(response.json(), indent=2))
    print()

def delete_users_table():
    url = f"{BASE_URL}/admin/delete_users_table"
    response = requests.post(url)
    print(f"Delete Users Table Response (Status Code: {response.status_code}):")
    print(json.dumps(response.json(), indent=2))
    print()

def main():
    # First, delete the users table to start fresh
    # print("Deleting users table:")
    # delete_users_table()

    print("Print DB tables:")
    test_view_tables()

    # Test registration with a new user
    print("Testing registration with a new user:")
    test_register("newuser", "password123")

    # Test login with the new user
    print("Testing login with the new user:")
    test_login("newuser", "password123")

    # Test registration with an existing user (should fail)
    print("Testing registration with an existing user:")
    test_register("newuser", "password123")

    # Test login with incorrect password
    print("Testing login with incorrect password:")
    test_login("newuser", "wrongpassword")

    # Print DB tables again to see the changes
    print("Print DB tables after operations:")
    test_view_tables()

if __name__ == "__main__":
    main()
```

My objective is to simulate a user authentication and login service, and I want it to be as true to life to a production microservice as possible. What is missing?

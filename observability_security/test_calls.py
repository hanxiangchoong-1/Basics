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
    # JWT Token
    token = test_login("newuser", "password123")
    
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
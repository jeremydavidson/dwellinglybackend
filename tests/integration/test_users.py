from models.user import UserModel
from conftest import is_valid, log
from freezegun import freeze_time

def test_user_auth(client, test_database, admin_user):
    login_response = client.post("/api/login", json={
        "email": admin_user.email,
        "password": admin_user.password
    })
    """When an admin user logs in, the request should succeed."""
    assert is_valid(login_response, 200) # OK
    assert "access_token" in login_response.json.keys()

    """The server responds with an error when a user attempts to login with an incorrect password."""
    responseBadPassword = client.post("/api/login", json={"email": admin_user.email, "password": "incorrect"})
    assert responseBadPassword.status_code == 401

    """The server responds with an error when a request is made (to a protected route) without the admin token provided."""
    responseMissingToken = client.get(f"/api/user/1", headers={})
    assert responseMissingToken.status_code == 401

def test_last_active(client, test_database, admin_user):
    user = UserModel.find_by_email(admin_user.email)
    assert user.lastActive.strftime('%Y-%m-%d %H:%M:%S') != '2020-01-01 00:00:00'

    with freeze_time('2020-01-01'):
        login_response = client.post("/api/login", json={
            "email": admin_user.email,
            "password": admin_user.password
        })
        user = UserModel.find_by_email(admin_user.email)
        assert user.lastActive.strftime('%Y-%m-%d %H:%M:%S') == '2020-01-01 00:00:00'

def test_register_duplicate_user(client, test_database):
    """When a user first registers, the server responds successfully."""
    genericUser = {
        "firstName": "first",
        "lastName": "last",
        "password": "1234",
        "email": "email@mail.com",
        "phone": "123 123 5555"
    }
    login_response = client.post("/api/register", json=genericUser)
    assert login_response.status_code == 201

    """The server responds with an error if duplicate user details are used for registration."""
    duplicateUser = genericUser
    responseDuplicate = client.post("/api/register", json=duplicateUser)
    assert responseDuplicate.status_code == 400

def test_refresh_user(client, test_database, admin_user):
    login_response = client.post("/api/login", json={
        "email": admin_user.email,
        "password": admin_user.password
    })
    """The refresh route returns a successful response code."""
    refreshHeader = {"Authorization": f"Bearer {login_response.json['refresh_token']}"}
    responseRefreshToken = client.post("api/refresh", json={}, headers=refreshHeader)
    assert responseRefreshToken.status_code == 200

def test_get_user_by_id(client, auth_headers, admin_user):
    """The get user by id route returns a successful response code."""
    user = UserModel.find_by_email(admin_user.email)
    response = client.get(f"/api/user/{user.id}", headers=auth_headers["admin"])
    assert response.status_code == 200

    """The server responds with an error if a non-existent user id is requested from the get user by id route."""
    responseBadUserId = client.get("/api/user/000000", headers=auth_headers["admin"])
    assert responseBadUserId.status_code == 404

def test_get_user_by_property_manager_id(client, auth_headers, new_property):
    """The get user by property manager id return properties and tenants list"""
    user = UserModel.find_by_id(new_property.propertyManager)
    response = client.get(f"/api/user/{user.id}", headers=auth_headers["admin"])
    user_info = response.get_json()
    assert 'properties' in user_info.keys()
    assert 'tenants' in user_info.keys()
    assert response.status_code == 200

def test_user_roles(client, auth_headers):
    """The get users by role route returns a successful response code."""
    response = client.post("/api/users/role", json={"userrole": "admin"}, headers=auth_headers["admin"])
    assert len(response.get_json()['users']) == 4
    assert response.status_code == 200

    """The get users by role route returns only property managers."""
    response = client.post("/api/users/role", json={"userrole": "property-manager"}, headers=auth_headers["admin"])
    managers = response.get_json()['users']
    assert len(managers) == 2
    assert all(["property-manager" == pm['role'] for pm in managers])
    assert response.status_code == 200

def test_archive_user(client, auth_headers, new_user):
    """The archive user by id route returns a successful response code and changes the user's status."""
    userToArchive = UserModel.find_by_email(new_user.email)
    response = client.post(f"/api/user/archive/{userToArchive.id}", json={}, headers=auth_headers["admin"])
    assert response.status_code == 201
    assert response.json["archived"] == True

    """An archived user is prevented from logging in."""
    data = {
        "email": new_user.email,
        "password": new_user.password
    }
    responseLoginArchivedUser = client.post("/api/login", json=data)
    assert responseLoginArchivedUser.status_code == 403

def test_archive_user_failure(client, auth_headers):
    """The server responds with an error if a non-existent user id is used for the archive user by id route."""
    responseInvalidId = client.post("/api/user/archive/999999", json={}, headers=auth_headers["admin"])
    assert responseInvalidId.status_code == 400

def test_patch_user(client, auth_headers, new_user):
    """The route to patch a user by id returns a successful response code and the expected data is patched."""
    expected = "property_manager"
    userToPatch = UserModel.find_by_email(new_user.email)
    response = client.patch(f"/api/user/{userToPatch.id}", json={"role": expected}, headers=auth_headers["admin"])
    actual = response.json["role"]
    assert response.status_code == 201
    assert expected == actual

    """The server responds with an error if a non-existent user id is used for the patch user by id route."""
    responseInvalidId = client.patch("/api/user/999999", json={"role": "new_role"}, headers=auth_headers["admin"])
    assert responseInvalidId.status_code == 400

def test_delete_user(client, auth_headers, new_user):
    userToDelete = UserModel.find_by_email(new_user.email)

    response = client.delete(f"/api/user/{userToDelete.id}", headers=auth_headers["pm"])
    assert is_valid(response, 401) # UNAUTHORIZED - Admin Access Required
    
    response = client.delete(f"/api/user/{userToDelete.id}", headers=auth_headers["pending"])
    assert is_valid(response, 401) # UNAUTHORIZED - Admin Access Required

    response = client.delete(f"/api/user/{userToDelete.id}", headers=auth_headers["admin"])
    assert is_valid(response, 200) # OK

    response = client.delete("/api/user/999999", headers=auth_headers["admin"])
    assert is_valid(response, 400) # BAD REQUEST

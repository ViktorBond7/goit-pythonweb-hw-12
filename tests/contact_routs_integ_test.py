def test_create_contact(client, get_token):
    response = client.post(
        "/contacts/",
        json={
            "first_name": "John",
            "last_name": "Doe",
            "email": "john.doe@example.com",
            "phone_number": "+1234567890",
            "birthday": "1990-01-01",
            "additional_data": "test contact",
        },
        headers={"Authorization": f"Bearer {get_token}"},
    )
    assert response.status_code == 201, response.text
    data = response.json()
    assert data["first_name"] == "John"
    assert data["last_name"] == "Doe"
    assert data["email"] == "john.doe@example.com"
    assert "id" in data


def test_get_contact(client, get_token):
    # First create a contact
    create_resp = client.post(
        "/contacts/",
        json={
            "first_name": "Get",
            "last_name": "Contact",
            "email": "get.contact@example.com",
            "phone_number": "+1111111111",
            "birthday": "1991-01-01",
        },
        headers={"Authorization": f"Bearer {get_token}"},
    )
    contact_id = create_resp.json()["id"]

    response = client.get(
        f"/contacts/{contact_id}", headers={"Authorization": f"Bearer {get_token}"}
    )
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["first_name"] == "Get"
    assert data["last_name"] == "Contact"
    assert data["email"] == "get.contact@example.com"
    assert "id" in data


def test_get_contact_not_found(client, get_token):
    response = client.get(
        "/contacts/99999", headers={"Authorization": f"Bearer {get_token}"}
    )
    assert response.status_code == 404, response.text
    data = response.json()
    assert data["detail"] == "Contact not found"


def test_get_contacts(client, get_token):
    # Create at least one contact
    client.post(
        "/contacts/",
        json={
            "first_name": "List",
            "last_name": "Contact",
            "email": "list.contact@example.com",
            "phone_number": "+2222222222",
            "birthday": "1992-01-01",
        },
        headers={"Authorization": f"Bearer {get_token}"},
    )

    response = client.get("/contacts", headers={"Authorization": f"Bearer {get_token}"})
    assert response.status_code == 200, response.text
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0
    assert "first_name" in data[0]


def test_update_contact(client, get_token):
    # Create a contact for update testing
    create_resp = client.post(
        "/contacts/",
        json={
            "first_name": "Update",
            "last_name": "Test",
            "email": "update.test@example.com",
            "phone_number": "+0987654321",
            "birthday": "1995-05-05",
            "additional_data": "for update",
        },
        headers={"Authorization": f"Bearer {get_token}"},
    )
    contact_id = create_resp.json()["id"]

    response = client.patch(
        f"/contacts/{contact_id}",
        json={
            "first_name": "Jane",
            "last_name": "Doe",
            "email": "jane.doe@example.com",
            "phone_number": "+1234567890",
            "birthday": "1990-01-01",
        },
        headers={"Authorization": f"Bearer {get_token}"},
    )
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["first_name"] == "Jane"
    assert data["last_name"] == "Doe"
    assert data["email"] == "jane.doe@example.com"
    assert "id" in data


def test_update_contact_not_found(client, get_token):
    response = client.patch(
        "/contacts/99999",
        json={
            "first_name": "New",
            "last_name": "Contact",
            "email": "new.contact@example.com",
            "phone_number": "+1234567890",
            "birthday": "1990-01-01",
        },
        headers={"Authorization": f"Bearer {get_token}"},
    )
    assert response.status_code == 404, response.text
    data = response.json()
    assert data["detail"] == "Contact not found"


def test_delete_contact(client, get_token):
    # Create a contact for delete testing
    create_resp = client.post(
        "/contacts/",
        json={
            "first_name": "Delete",
            "last_name": "Test",
            "email": "delete.test@example.com",
            "phone_number": "+5555555555",
            "birthday": "2000-12-12",
        },
        headers={"Authorization": f"Bearer {get_token}"},
    )
    contact_id = create_resp.json()["id"]

    response = client.delete(
        f"/contacts/{contact_id}", headers={"Authorization": f"Bearer {get_token}"}
    )
    assert response.status_code == 200, response.text
    data = response.json()
    # assert "deleted successfully" in data.get("message", "")
    assert data["message"] == f'Contact with id "{contact_id}" deleted successfully'


def test_repeat_delete_contact(client, get_token):
    response = client.delete(
        "/contacts/99999", headers={"Authorization": f"Bearer {get_token}"}
    )
    assert response.status_code == 404, response.text
    data = response.json()
    assert data["detail"] == "Contact not found"

import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

import app as flask_app


def test_routes_and_cart_flow():
    flask_app.app.testing = True
    client = flask_app.app.test_client()

    response = client.get('/?lang=ru')
    assert response.status_code == 200
    assert 'Garmin Fenix 7' in response.get_data(as_text=True)

    response = client.post('/register', data={'username': 'tester', 'password': 'secret123', 'email': 'tester@example.com'})
    assert response.status_code == 302

    response = client.post('/login', data={'username': 'tester', 'password': 'secret123'})
    assert response.status_code == 302

    response = client.post('/add_to_cart', data={'lang': 'ru', 'product_id': '1'})
    assert response.status_code == 302

    with client.session_transaction() as session:
        assert session['cart']['1'] == 1

    response = client.post('/toggle_favorite', data={'product_id': '1'})
    assert response.status_code == 302

    response = client.post('/submit_order', data={'lang': 'ru', 'name': 'Anna', 'phone': '+374111111'})
    assert response.status_code == 302

    with client.session_transaction() as session:
        assert session['cart'] == {}

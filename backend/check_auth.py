from fastapi.testclient import TestClient

from main import app


def main():
    client = TestClient(app)
    email = 'auth-test@example.com'
    register = client.post('/auth/register', json={'name': 'Test User', 'email': email, 'password': 'StrongPass123!'})
    print('REGISTER', register.status_code, register.json())
    login = client.post('/auth/login', json={'email': email, 'password': 'StrongPass123!'})
    print('LOGIN', login.status_code, login.json())
    token = login.json().get('token')
    notes = client.get('/notes', headers={'Authorization': f'Bearer {token}'})
    print('NOTES', notes.status_code, notes.json())


if __name__ == '__main__':
    main()

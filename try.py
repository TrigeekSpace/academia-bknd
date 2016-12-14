from app import app, db
from app.models import User
from app.schemas import UserSchema

def login(username, password):
    client = app.test_client()
    return client.post('/users/login', data=json.dumps(dict(
        username=username,
        password=password
    )).encode(), content_type='application/json')

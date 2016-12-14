""" Test of user-related APIs. """
import os
from app import app, db
from app.config import AUTH_TOKEN_HEADER
from app.models import User
from app.schemas import UserSchema

from app.util.test import *
from unittest import TestCase


def add_user(info, commit = True):
    user = UserSchema().load(info)[0]
    print(user.password)
    db.session.add(user)
    if commit:
        db.session.commit()


class UserTestCase(TestCase):
    """ User-related API test class. """
    client = app.test_client()

    @classmethod
    def setUpClass(cls):
        super(UserTestCase, cls).setUpClass()
        print(User.query.all())

        add_user({
                'username': 'test_user',
                'password': 'test_pass',
                'email': 'test@test.com'
            }, False)
        print(User.query.all())

    @classmethod
    def tearDownClass(cls):
        super(UserTestCase, cls).tearDownClass()

    def setUp(self):
        """ Set up test case. """
        pass
    def tearDown(self):
        """ Tear down test case. """
        pass

    def login(self, username, password):
        return self.client.post('/users/login', data=json.dumps(dict(
            username=username,
            password=password
        )).encode(), content_type='application/json')

    def logout(self, token):
        return self.client.post('/users/logout', headers={AUTH_TOKEN_HEADER: token})

    def test_login_logout(self):
        # normal login
        login_rv = self.login('test_user', 'test_pass')
        print(login_rv.status)
        assert '200' in login_rv.status
        token = login_rv.token
        # normal logout
        logout_rv = self.logout(token)
        assert '200' in logout_rv.status

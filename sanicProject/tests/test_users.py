from contextvars import ContextVar
from http.client import OK, NO_CONTENT, BAD_REQUEST, FORBIDDEN, UNAUTHORIZED, NOT_FOUND, CREATED
from tkinter import ACTIVE
import pytest
from sanic import Sanic, Blueprint, response, json
from sanic_testing import TestManager
from sanic_testing.reusable import ReusableClient
from sanic_jwt import inject_user, Initialize
import jwt

from collections import deque

#from sanicProject.main

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select
from sqlalchemy.engine import create_engine

from ..auth import authenticate, retrieve_user
from ..views import get_user_accounts
from ..settings import DB_URL, SECRET, PYTEST_DB
from ..models import BaseModel, User, UserStatus
from .conf import create_users, admin_user, active_user, inactive_user, generate_auth_headers, admin_auth_header, active_user_auth_header, valid_user, delete_obj
from ..blueprints.users import users
#from sanicProject.models import BaseModel, User


async def prepare_db():
    engine = create_async_engine(
        PYTEST_DB,
        pool_pre_ping=True,
        echo=True
    )
    async with engine.begin() as conn:
        await conn.run_sync(BaseModel.metadata.drop_all)
        await conn.run_sync(BaseModel.metadata.create_all)

    session = sessionmaker(engine, AsyncSession, expire_on_commit=False)()
    async with session.begin():
        users = create_users()
        for user in users:
            user.set_password()
        session.add_all(users)
        await session.commit()

    await engine.dispose()

@pytest.fixture
async def get_engine():
    engine = True


@pytest.fixture(scope='function')
def app():
    sanic_app = Sanic('testApp')
    #TestManager(sanic_app)

    Initialize(
    sanic_app,
    authenticate=authenticate,
    user_id='id',
    retrieve_user=retrieve_user,
    url_prefix='/user',
    path_to_authenticate='/login',
    path_to_retrieve_user='/profile',
    secret=SECRET,
    )

    @sanic_app.before_server_start
    async def create_db_engine(sanic_app: Sanic, loop):
        sanic_app.ctx.bind = create_async_engine(
            PYTEST_DB,
            pool_pre_ping=True,
            echo=True
        )
        #async with sanic_app.ctx.bind.begin() as conn:
        #    await conn.run_sync(BaseModel.metadata.drop_all)
        #    await conn.run_sync(BaseModel.metadata.create_all)

        #yield sanic_app.ctx.bind

    #@sanic_app.before_server_start
    #async def add_users_to_db(sanic_app: Sanic, loop):
    #    session = sessionmaker(sanic_app.ctx.bind, AsyncSession, expire_on_commit=False)()
    #    sanic_app.ctx.session = session
    #    async with session.begin():
    #        users = create_users()
    #        for user in users:
    #            user.set_password()
    #        session.add_all(users)
    #        auth_headers = await generate_auth_headers(session, sanic_app.ctx.auth, admin_user)
    #        sanic_app.ctx.admin_headers = auth_headers
    #        sanic_app.ctx.fuckoff = True
    #        await session.commit()

    _base_model_session_ctx = ContextVar("session")

    @sanic_app.on_request
    async def inject_session(request):
        request.ctx.session = sessionmaker(sanic_app.ctx.bind, AsyncSession, expire_on_commit=False)()
        request.ctx.session_ctx_token = _base_model_session_ctx.set(request.ctx.session)

    @sanic_app.on_response
    async def close_session(request, response):
        if hasattr(request.ctx, 'session_ctx_token'):
            _base_model_session_ctx.reset(request.ctx.session_ctx_token)
            await request.ctx.session.close()


    sanic_app.blueprint(users)


    #sanic_app = Sanic.get_app()
    #sanic_app.ctx.PROD_MODE = False
    #sanic_app.ctx.TEST_MODE = True
    #myapp.listeners = {}
    #print(myapp.ctx)
    #myapp.ctx.bind = create_async_engine(
    #        PYTEST_DB,
    #        pool_pre_ping=True,
    #        echo=True
    #    )
    #async with myapp.ctx.bind.begin() as conn:
    #    await conn.run_sync(BaseModel.metadata.drop_all)
    #    await conn.run_sync(BaseModel.metadata.create_all)
    #
    #session = sessionmaker(myapp.ctx.bind, AsyncSession, expire_on_commit=False)()
    #myapp.ctx.session = session
    #async with session.begin():
    #    users = create_users()
    #    for user in users:
    #        user.set_password()
    #    #user = User(username='test_user', email='test@hello.py', password='hello', _is_admin=True)
    #    #user.set_password()
    #    #user.activate()
    #    #session.add(user)
    #    session.add_all(users)
    #    await session.commit()
    #    await session.close()
#
    #async with myapp.ctx.bind.begin() as conn:
    #    await conn.run_sync(BaseModel.metadata.drop_all)
    #    await conn.run_sync(BaseModel.metadata.create_all)
    #@myapp.before_server_start
    #async def create_db_engine(app: Sanic, loop):
    #    app.ctx.bind = create_async_engine(
    #        PYTEST_DB,
    #        pool_pre_ping=True,
    #        echo=True
    #    )
    #    #print(dir(sanic_app.ctx))
    #    async with app.ctx.bind.begin() as conn:
    #        await conn.run_sync(BaseModel.metadata.drop_all)
    #        await conn.run_sync(BaseModel.metadata.create_all)
    #    
    #    session = sessionmaker(app.ctx.bind, AsyncSession, expire_on_commit=False)()
    #    app.ctx.session = session
    #print(sanic_app.response_middleware)
    #sanic_app.request_middleware = deque()
    #sanic_app.response_middleware = deque()
    
    #@sanic_app.after_server_start
    #async def create_session(app, loop):
    #    print('hello im here')
    #    session = sessionmaker(app.ctx.bind, AsyncSession, expire_on_commit=False)()
    #    app.ctx.session = session
    #
    #print(dir(sanic_app))
    #print(dir(sanic_app.ctx))
    #print(type(sanic_app.ctx.bind))

    #print(sanic_app.ext)
    #Initialize(
    #sanic_app,
    #authenticate=authenticate,
    #user_id='id',
    #retrieve_user=retrieve_user,
    #url_prefix='/profile',
    #path_to_authenticate='/login',
    #path_to_retrieve_user='/me',
    #secret=SECRET,
    #)
    #TestManager(myapp)
    #return myapp
    #return sanic_app
    yield sanic_app

#@pytest.fixture(scope='session', autouse=True)
#def setup_db():
#    sync_engine = create_engine(PYTEST_DB, echo=True)
#    BaseModel.metadata.drop_all(sync_engine)
#    BaseModel.metadata.create_all(sync_engine)
#    
#    yield sync_engine
#
#    BaseModel.metadata.drop_all(sync_engine)

#@pytest.fixture(scope='session')
#async def async_engine():
#    engine = create_async_engine(PYTEST_DB, echo=True)
#    return engine
#
#@pytest.fixture(scope='session')
#async def session():
#    bind = create_async_engine(
#            PYTEST_DB,
#            pool_pre_ping=True,
#            echo=True
#    )
#    #async_engine = await async_engine
#    #trans = await conn.begin()
#    session = sessionmaker(bind, AsyncSession, expire_on_commit=False)()
#    return session
#
#    session.close()
#    #trans.rollback()
#

@pytest.mark.asyncio
async def test_smth():
    await prepare_db()


@pytest.mark.asyncio
class TestGroupUsers:
    #async def setup(self):
    #    await prepare_db()

    async def test_users_list_success_for_admin(self, app):
        _, response = await app.asgi_client.get('/users', headers=admin_auth_header)
        assert response.status == OK
        assert len(response.json.get('users')) == len((admin_user, active_user, inactive_user))

    #async def test_users_list_fails_for_non_admin(self, app):
    #    _, response = await app.asgi_client.get('/users', headers=active_user_auth_header)
    #    assert response.status == FORBIDDEN

    #async def test_user_detail_success_for_admin(self, app):
    #    _, response = await app.asgi_client.get(f'/users/{active_user.id}', headers=admin_auth_header)
    #    assert response.status == OK
    #    data = response.json
    #    assert data.get('id') == active_user.id
    #    assert data.get('name') == active_user.username
    #    assert data.get('email') == active_user.email
    #    assert data.get('status') == active_user.status
    #    assert data.get('admin') == active_user._is_admin
#
    #async def test_user_detail_fails_for_non_admin(self, app):
    #    _, response = await app.asgi_client.get(f'/users/{active_user.id}', headers=active_user_auth_header)
    #    assert response.status == FORBIDDEN

    #async def test_create_inactive_user_success_for_admin(self, app):
    #    req, response = await app.asgi_client.post('/users', headers=admin_auth_header, json=valid_user.to_dict())
    #    assert response.status == CREATED
    #    data = response.json
    #    assert data.get('name') == valid_user.username
    #    assert data.get('email') == valid_user.email
    #    assert data.get('status') == valid_user.status
    #    assert data.get('admin') == valid_user._is_admin

    #    # teardown
    #    await delete_obj(req.ctx.session, User, data.get('id'))

    #async def test_create_active_user_success_for_admin(self, app):
    #    ACTIVE_STATUS = 'active'
    #    payload = valid_user.to_dict()
    #    payload['status'] = ACTIVE_STATUS
    #    req, response = await app.asgi_client.post('/users', headers=admin_auth_header, json=payload)
    #    assert response.status == CREATED
    #    assert response.json.get('status') == ACTIVE_STATUS
    #    await delete_obj(req.ctx.session, User, response.json.get('id'))

    #async def test_create_user_with_invalid_status_fails(self, app):
    #    INVALID_STATUS = 'invalid_status'
    #    payload = valid_user.to_dict()
    #    payload['status'] = INVALID_STATUS
    #    _, response = await app.asgi_client.post('/users', headers=admin_auth_header, json=payload)
    #    assert response.status == BAD_REQUEST

    #async def test_create_user_fails_for_non_admin(self, app):
    #    _, response = await app.asgi_client.post('/users', headers=active_user_auth_header, json=valid_user.to_dict())
    #    assert response.status == FORBIDDEN

    #async def test_update_user_success_for_admin(self, app):
    #    payload = {
    #        'email': 'new_email@hello.py',
    #        'status': UserStatus.ACTIVE,
    #    }
    #    #payload = {}
    #    _, response = await app.asgi_client.patch(f'/users/{inactive_user.id}', headers=admin_auth_header, json=payload)
    #    print(response.json)


    #async def test_delete_user_success_for_admin(self, app):
    #    _, response = await app.asgi_client.delete(f'/users/{inactive_user.id}', headers=admin_auth_header)
    #    assert response.status == NO_CONTENT
    #    _, response = await app.asgi_client.get(f'/users/{inactive_user.id}', headers=admin_auth_header)
    #    assert response.status == NOT_FOUND

    #async def test_delete_user_returns_404_when_no_such_user(self, app):
    #    INVALID_ID = 123123123
    #    _, response = await app.asgi_client.get(f'/users/{INVALID_ID}', headers=admin_auth_header)
    #    assert response.status == NOT_FOUND

    #async def test_delete_user_fails_for_non_admin(self, app):
    #    _, response = await app.asgi_client.delete(f'/users/{inactive_user.id}', headers=active_user_auth_header)
    #    assert response.status == FORBIDDEN


    #async def test_some_user(self, app):
    #    _, response = await app.asgi_client.get(f'/users/{active_user.id}', headers=admin_auth_header)
    #    print(response.json)
    #async def test_create_invalid_user_fails_for_admin(self, app):
    #    payload = valid_user.to_dict()
    #    payload['email'] = 'invalid_email'
    #    _, response = await app.asgi_client.post('/users', headers=admin_auth_header, json=payload)
    #    assert response.status == BAD_REQUEST


'''
@pytest.mark.asyncio
async def test_smth(app):
    req, res = await app.asgi_client.get('/')
    #print(req.app.ctx)
    #assert res.status != OK

@pytest.mark.asyncio
async def test_foo(app):
    req, res = await app.asgi_client.get('/foo')
    #print(req.app.ctx)
    #print(dir(req.app.ctx.loop))
    #assert res.status != OK
'''
'''
@pytest.mark.asyncio
async def test_group(app):
    client = app.asgi_client

    @pytest.mark.asyncio
    async def test_smth():
        req, res = await client.get('/')
        print(req.app.ctx)
        #assert res.status != OK

    @pytest.mark.asyncio
    async def test_foo():
        req, res = await client.get('/foo')
        print(req.app.ctx)
        #assert res.status != OK

    await test_smth()
    await test_foo()
'''


#print(app)
#@pytest.fixture
#async def get_session(app):
#    session = sessionmaker(app.ctx.bind, AsyncSession, expire_on_commit=False)()
#    return session


#async def get_obj_by_id(session: AsyncSession, model: BaseModel, id: int) -> BaseModel:
#    async with session.begin():
#        #user = select(model).where(model.id==id)
#        return await session.get(model, id)
#        #user = await session.get(model, id)
#        #return user

#@pytest.fixture
#async def authorized_user(get_session):
#    session = await get_session
#    async with session.begin():
#        user = User(username='test_user', email='test@hello.py', password='hello')
#        user.set_password()
#        user.activate()
#        session.add(user)
#        await session.commit()
#    return user


#@pytest.fixture
#async def get_auth_token(app):
#    app = await app
#    user = await get_obj_by_id(app.ctx.session, User, 1)
#    authmodel = app.ctx.auth
#    token = await authmodel.generate_access_token(user)
#    return token


"""
@pytest.fixture
async def setUp(app):
    app = await app
    #print(app)
    user = await get_obj_by_id(app.ctx.session, User, 1)
    token = await gtoken(app.ctx.auth, user)
    headers = {"Authorization": f"Bearer {token}"}
    return app
    #return (app, headers)
"""

"""
@pytest.fixture
async def active_user_setup(app):
    app = await app
    #print(app)
    #async with
    user = await get_obj_by_id(app.ctx.session, User, active_user.get('id'))
    token = await gtoken(app.ctx.auth, user)
    headers = {"Authorization": f"Bearer {token}"}
    return app.asgi_client, headers
    #return (app, headers)


@pytest.mark.asyncio
class TestProfileGroup:

    async def test_me_authorized(self, active_user_setup):
        client, headers = await active_user_setup
        _, response = await client.get("/profile/me", headers=headers)
        assert response.status == 200
        data = response.json.get('me')
        assert data.get('id') == active_user.get('id')
        assert data.get('name') == active_user.get('username')
        assert data.get('email') == active_user.get('email')
        assert data.get('active') == active_user.get('_is_active')
        assert data.get('admin') == active_user.get('_is_admin')

    async def test_me_unauthorized(self, active_user_setup):
        client, _ = await active_user_setup
        _, response = await client.get("/profile/me")
        assert response.status == 401

    async def test_login_valid_data(self, active_user_setup):
        client, headers = await active_user_setup
        valid_data = {
            'username': active_user.get('username'),
            'password': active_user.get('password'),
        }
        _, response = await client.post('profile/loginf')
        assert response.status == 404
        #assert response.status == 200


    async def test_login_invalid_data(self, active_user_setup):
        client, headers = await active_user_setup
        valid_data = {
            'username': active_user.get('username'),
            'password': active_user.get('password'),
        }
        _, response = await client.post('profile/loginf')
        assert response.status != 404

"""
from sanic_testing.testing import SanicASGITestClient
from ..utils import get_obj_by_id

'''
@pytest.mark.asyncio
async def tests_signup_activation(app):
    """Test group for signup and authentication parts"""
    app = await app
    client: SanicASGITestClient = app.asgi_client

    @pytest.mark.asyncio
    async def test_signup_valid_data():
        valid_data = {
            'username': 'new_user',
            'email': 'new_user@hello.py',
            'password': 'new_&=USER'
        }
        _, response = await client.post('/signup', json=valid_data)
    
        assert response.status == CREATED
        assert response.json.get('name') == valid_data.get('username')
        assert response.json.get('email') == valid_data.get('email')
        assert response.json.get('active') == False
        assert response.json.get('admin') == False
        assert 'activation_link' in response.json

    @pytest.mark.asyncio
    async def test_signup_not_enough_data():
        invalid_data = {
            'username': 'another_user',
            'password': 'another_&&USer',
        }
        _, response = await client.post('/signup', json=invalid_data)

        assert response.status == BAD_REQUEST
        assert 'status' in response.json
        assert 'description' in response.json

    @pytest.mark.asyncio
    async def test_signup_too_much_data():
        """Only `username`, `email` and `password` counts.
        The rest is ignored.
        """
        verbose_data = {
            'id': 23,
            'username': 'another_user',
            'email': 'another_user@hello.py',
            'password': 'another_&&USer',
            '_is_admin': True,
            '_is_active': True,
        }
        _, response = await client.post('/signup', json=verbose_data)

        assert response.status == CREATED
        assert response.json.get('id') != verbose_data.get('id')
        assert response.json.get('name') == verbose_data.get('username')
        assert response.json.get('email') == verbose_data.get('email')
        assert response.json.get('active') == False
        assert response.json.get('admin') == False
        assert 'activation_link' in response.json

    @pytest.mark.asyncio
    async def test_signup_invalid_name():
        invalid_data = {
            'username': 'sh',
            'email': 'some_new_user@hello.py',
            'password': 'another_&&USer',
        }
        _, response = await client.post('/signup', json=invalid_data)

        assert response.status == BAD_REQUEST
        assert 'status' in response.json
        assert 'description' in response.json

    @pytest.mark.asyncio
    async def test_signup_invalid_email():
        invalid_data = {
            'username': 'some_new_user',
            'email': 'another_userhello.py',
            'password': 'another_&&USer',
        }
        _, response = await client.post('/signup', json=invalid_data)

        assert response.status == BAD_REQUEST
        assert 'status' in response.json
        assert 'description' in response.json

    @pytest.mark.asyncio
    async def test_signup_invalid_password():
        invalid_data = {
            'username': 'some_new_user',
            'email': 'some_new_user@hello.py',
            'password': 'short',
        }
        _, response = await client.post('/signup', json=invalid_data)

        assert response.status == BAD_REQUEST
        assert 'status' in response.json
        assert 'description' in response.json

    @pytest.mark.asyncio
    async def test_signup_existing_user_fails():
        _, response = await client.post('/signup', json=active_user)

        assert response.status == BAD_REQUEST
        assert 'invalid data!' in response.json

    @pytest.mark.asyncio
    async def test_activation_link_valid_user():
        """Valid user recieves token link."""
        _, response = await client.post(f"/users/{inactive_user.get('id')}/activate")

        assert response.status == OK
        assert inactive_user.get('username') in response.json

        response_data = response.json.get(f"{inactive_user.get('username')}")
        assert response_data.get('activated') == True
        assert 'login_link' in response_data

    @pytest.mark.asyncio
    async def test_activation_link_invalid_user():
        """Valid user recieves token link."""
        invalid_user_id = 23
        _, response = await client.post(f"/users/{invalid_user_id}/activate")
    
        assert response.status == NOT_FOUND

    await test_signup_existing_user_fails()
    await test_signup_valid_data()
    await test_signup_too_much_data()
    await test_signup_not_enough_data()
    await test_signup_invalid_name()
    await test_signup_invalid_email()
    await test_signup_invalid_password()
    await test_activation_link_valid_user()
    await test_activation_link_invalid_user()
'''
'''
@pytest.mark.asyncio
async def test_login_group(app):
    app = await app
    client: SanicASGITestClient = app.asgi_client

    @pytest.mark.asyncio
    async def test_login_active_user():
        """Active user recieves access token."""
        valid_data = {
            'username': active_user.get('username'),
            'password': active_user.get('password'),
        }
        _, response = await client.post("/user/login", json=valid_data)
    
        assert response.status == OK
        assert 'access_token' in response.json

    @pytest.mark.asyncio
    async def test_login_inactive_user():
        """Inactive user recieves 401 response
        and notification to activate account before
        being logged in."""
        valid_data = {
            'username': inactive_user.get('username'),
            'password': inactive_user.get('password'),
        }
        notification = 'You should activate your account first!'
        _, response = await client.post("/user/login", json=valid_data)
    
        assert response.status == UNAUTHORIZED
        assert notification in response.json.get('reasons')

    @pytest.mark.asyncio
    async def test_login_invalid_data():
        """User with invalid data recieves 401 response."""
        invalid_data = {
            'username': 'username',
            'password': 'password',
        }
        _, response = await client.post("/user/login", json=invalid_data)

        assert response.status == UNAUTHORIZED
        assert 'access_token' not in response.json

    await test_login_active_user()
    await test_login_inactive_user()
    await test_login_invalid_data()
''' 

'''
@pytest.mark.asyncio
async def tests_profile_endpoints_for_active_user(app):
    """A group of tests"""
    app = await app
    client: SanicASGITestClient = app.asgi_client
    user = await get_obj_by_id(
        app.ctx.session, User, active_user.get('id')
    )
    token = await gtoken(app.ctx.auth, user)
    auth_headers = {"Authorization": f"Bearer {token}"}

    @pytest.mark.asyncio
    async def test_me_authorized():
        _, response = await client.get("/profile/me", headers=auth_headers)
        assert response.status == OK
        data = response.json.get('me')
        assert data.get('id') == active_user.get('id')
        assert data.get('name') == active_user.get('username')
        assert data.get('email') == active_user.get('email')
        assert data.get('active') == active_user.get('_is_active')
        assert data.get('admin') == active_user.get('_is_admin')

    @pytest.mark.asyncio
    async def test_me_unauthorized():
        """Unauthorized user recieves 401 response."""
        _, response = await client.get("/profile/me", headers={})
        assert response.status == UNAUTHORIZED

    #@pytest.mark.asyncio
    #async def test_another_end():
    #    print('second test')
    #    request, response = await app.asgi_client.get("/users", headers=headers)
    #    print('second request')
    #    assert response.status_code == 200
    await test_me_authorized()
    await test_me_unauthorized()
    
    #print(s)
    #print(app.ctx)
    #print(app.listeners)
    #print(app.request_middleware)
    #user = await authorized_user
    #print(user)
    #request, response = await app.asgi_client.get("/users", headers={"Authorization": "Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJpZCI6NSwiZXhwIjoxNjYyNTA3NTM4fQ.d1ecsqKOK_c5o9o_txsIk3VwvZZGt5EQH_xBb1qKt1M"})
    #print(dir(app.ctx.bind))

    
    #token = await get_auth_token
    #print(token)
    #print(dir(app.ctx.auth))
    #assert request.method.lower() == 'get'
    #print(response.json)

    #assert response.status == 200

'''
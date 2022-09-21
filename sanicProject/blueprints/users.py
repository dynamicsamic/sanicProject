import asyncio
from http.client import BAD_REQUEST, CREATED, NOT_FOUND, NO_CONTENT
from sanic import Blueprint, Request, json
from sanic.response import HTTPResponse
from sanic.exceptions import NotFound, BadRequest
from sanic.log import logger
from sanic_jwt import protected, inject_user
from sanic_ext import validate
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import update

from ..models import Account, User, UserStatus
from ..auth import authorized
from ..schemas import UserAdminCreateSchema, UserAdminUpdateSchema
from sanicProject.crud import UserCRUDManager

users = Blueprint('users_for_admin', url_prefix='users')

@users.on_request
async def inject_user_manager(request: Request) -> None:
    """Add CRUD manager to request."""
    request.ctx.crud = UserCRUDManager(request.ctx.session)

@users.signal('app.user.deleted')
async def sig_delete_user(sleep_for: int = 10, **context):
    #logger.info('Start_waiting')
    #await asyncio.sleep(sleep_for)
    
    req = context.get('request')
    print(req)
    user_id = context.get('id')
    print(user_id)
    app = req.app
    print(req.app.ctx.bind)
    #logger.info(f'{app.bind}')
    session = sessionmaker(app.ctx.bind, AsyncSession, expire_on_commit=False)()
    #print(session)
    #session = req.ctx.session 
    logger.info('session created')
    async with session.begin():
        logger.warning('session started')
        user = await session.get(User, user_id)
        print(user)
    #    print(user)
    logger.warning(f'{user.to_dict()}')
    logger.info('ended waiting')
    #await req.ctx.crud.delete_user(user_id)


@users.get('/')
@protected()
@inject_user()
@authorized()
async def get_users(request: Request, *args, **kwargs) -> HTTPResponse:
    """Get all users."""
    users = await request.ctx.crud.get_users()
    return json(
        {'users': [user.to_dict() for user in users]}
    )


@users.get('/<id:int>')
@protected()
@inject_user()
@authorized()
async def get_user(request: Request, id: int, *args, **kwargs) -> HTTPResponse:
    """Admin only"""
    if user := await request.ctx.crud.get_user(id):
        return json(user.to_dict())

    return json(
        {'error': f'user with id `{id}` not found'},
        status=NOT_FOUND
    )


@users.post('/')
@inject_user()
@protected()
@authorized()
@validate(json=UserAdminCreateSchema)
async def add_user(request: Request, body: UserAdminCreateSchema, *args, **kwargs) -> HTTPResponse:
    if valid_data := body.dict():
        new_user = await request.ctx.crud.create_user(valid_data)

    result = new_user.to_dict()
    #activation_link = {'activation_link': f'http://127.0.0.1:8000/users/{new_user.id}/activate'}
    #sresult.update(activation_link)
    return json(result, status=CREATED)


@users.patch('/<id:int>')
@protected()
@inject_user()
@authorized()
@validate(UserAdminUpdateSchema)
async def update_user(request: Request, id: int, body: UserAdminUpdateSchema, *args, **kwargs) -> HTTPResponse:
    if valid_data := body.dict(exclude_unset=True):
        await request.ctx.crud.update_user(id, valid_data)
    user = await request.ctx.crud.get_user(id)
    return json(user.to_dict())


@users.delete('/<id:int>')
@protected()
@inject_user()
@authorized()
async def delete_user(request: Request, id: int, *args, **kwargs) -> HTTPResponse:
    """Admin only"""
    res = await request.app.dispatch('app.user.deleted', context={'request': request, 'id': id})
    logger.warning('dispatched')
    return json({})
    return json({'res': res})
    #session: AsyncSession = request.ctx.session
    ##user = await get_model_instance(session, User, get_query_params(request.uri_template), val=username)
    #async with session.begin():
#   #     if accounts := select(Account).where(Account.user_id == id)
    #    if accounts := await Account.get_many(session, ['user_id', id]):
    #        for account in accounts:
    #            account.user_status = UserStatus.DELETED
    #    await User.delete_object(session, id)
    #    #if user := await User.get(session, id, related='accounts'):
    #    #    
    #    #    # Change this to select(Account).where(Account.user_id == id)
    #    #    for account in user.accounts:
    #    #        account.user_status = UserStatus.DELETED
    #    #if user := await get_obj_by_id(session, User, id):
    #        #if accounts := await user.get_accounts(session):
    #        #    for account in accounts:
    #        #        account.user_status = UserStatus.DELETED
    #        #try:
    #        #    await session.delete(user)
    #        #    await session.commit()
    #        #except Exception as e:
    #        #    await session.rollback()
    #        #    raise DBError(context={f'{e.__class__.__name__}': f'{e.args}'})
    #        #finally:
    #        #    await session.close()
#
#
    #    return json({'user with id `{id}`': 'deleted'}, status=204)
#
    #raise NotFound
    #return json(
    #    {'error': f'user with id `{id}` not found'},
    #    status=NOT_FOUND
    #)
#    return json(user.to_dict())
    #return json({'name': user.username, 'email': user.email, 'acounts': user.accounts})


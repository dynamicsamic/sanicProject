import time
from typing import Dict, Optional
from dataclasses import dataclass
import jwt
from sqlalchemy.ext.asyncio import AsyncSession
from sanic_jwt.authentication import Authentication

from ..models import User, UserStatus, BaseModel
from ..utils import get_obj_by_id
from ..settings import SECRET


@dataclass(frozen=True)
class UserType:
    username: str
    email: str
    password: str
    status: str
    _is_admin: bool
    id: Optional[int] = None

    def to_dict(self):
        print(self.__dict__)
        return self.__dict__


admin_user = UserType(
    'admin',
    'admin@hello.py',
    'admin&=AB',
    UserStatus.ACTIVE,
    True,
    99,
)

active_user = UserType(
    'bob78',
    'bob@hello.py',
    'bob=-_AW',
    UserStatus.ACTIVE,
    False,
    101,
)

inactive_user = UserType(
    'carlo',
    'carl@hello.py',
    'carl-=A9',
    UserStatus.INACTIVE,
    False,
    114,
)

valid_user = UserType(
    'valid_user',
    'valid@hello.py',
    'valid-=VALID',
    UserStatus.INACTIVE,
    False,
)


def create_users():
    return [User(**user.to_dict()) for user in (admin_user, active_user, inactive_user)]


async def gtoken(authmodel, user):
    token = await authmodel.generate_access_token(user)
    return token

async def generate_auth_headers(session: AsyncSession, authmodel: Authentication, user_type: UserType) -> Dict[str, str]:
    user = await get_obj_by_id(
        session, User, getattr(user_type, 'id')
    )
    token = await gtoken(authmodel, user)
    return {"Authorization": f"Bearer {token}"}


admin_auth_payload = {'id': admin_user.id, 'exp': time.time() + 1_000_000}
active_user_auth_payload = {'id': active_user.id, 'exp': time.time() + 1_000_000}
#encoded = jwt.encode(payload, SECRET, algorithm="HS256")

def generate_auth_header(payload):
    encoded = jwt.encode(payload, SECRET, algorithm="HS256")
    return {"Authorization": f"Bearer {encoded}"}

admin_auth_header = generate_auth_header(admin_auth_payload)
active_user_auth_header = generate_auth_header(active_user_auth_payload)

from datetime import date, datetime

async def delete_obj(session: AsyncSession, model: BaseModel, id: int) -> None:
    """Delete an object with certain id"""
    async with session.begin():
        user = await session.get(model, id)
        await session.delete(user)
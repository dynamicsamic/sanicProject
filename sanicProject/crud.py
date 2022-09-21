from dataclasses import dataclass
from typing import Type

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.engine.result import ScalarResult
from sqlalchemy.orm import selectinload
from sanic.exceptions import BadRequest
from werkzeug.security import generate_password_hash

from sanicProject.models import BaseModel, User
from sanicProject.exceptions import DBError
from sanicProject.user_status import UserStatus


@dataclass
class BaseCRUDManager:
    session: AsyncSession

    async def _get_object(self, model: Type[BaseModel], id: int) -> BaseModel:
        async with self.session.begin():
            return await self.session.get(model, id)

    async def _get_object_with_related(self, model: Type[BaseModel], id: int, field_name: str = '') -> BaseModel:
        if hasattr(model, field_name):
            rel_field = getattr(model, field_name)
            q = await self.session.execute(select(model).where(model.id == id).options(selectinload(rel_field)))
        else:
            q = await self.session.execute(select(model).where(model.id == id))
        return q.scalar()


    async def _get_all(self, model: Type[BaseModel]) -> ScalarResult:
        async with self.session.begin():
            qs = await self.session.execute(select(model).order_by(model.id))
            return qs.scalars().all()

    async def _create_object(self, model: Type[BaseModel], data: dict) -> BaseModel:
        async with self.session.begin():
            try:
                object = model(**data)
                self.session.add(object)
                await self.session.commit()
            except Exception as e:
                await self.session.rollback()
                raise BadRequest(context={f'{e.__class__.__name__}': f'{e.args}'})

            return object

    async def _update_object(self, model: Type[BaseModel], id: int, data: dict) -> None:
        async with self.session.begin():
            q = update(model).where(model.id == id).values(**data)
            try:
                await self.session.execute(q)
                await self.session.commit()
            except Exception as e:
                await self.session.rollback()
                raise BadRequest(context={f'{e.__class__.__name__}': f'{e.args}'})

    async def _delete_object(self, model: Type[BaseModel], id: int) -> None:
        async with self.session.begin():
            if object := await self.session.get(model, id):
                try:
                    await self.session.delete(object)
                    await self.session.commit()
                except Exception as e:
                    await self.session.rollback()
                    raise DBError(context={f'{e.__class__.__name__}': f'{e.args}'})
                finally:
                    await self.session.close()


class UserCRUDManager(BaseCRUDManager):
    async def get_user(self, id: int) -> BaseModel:
        return await self._get_object(User, id)

    async def get_users(self):
        return await self._get_all(User)

    async def create_user(self, data: dict) -> BaseModel:
        return await self._create_object(User, data)

    async def update_user(self, id: int, data: dict) -> None:
        if pswrd := data.get('password'):
            data['password'] = generate_password_hash(pswrd)
        return await self._update_object(User, id, data)

    async def delete_user(self, id: int) -> None:
        return await self._delete_object(User, id)

    async def mark_deleted(self, id: int) -> None:
        deleted = {'status': UserStatus.DELETED}
        return await self.update_user(id, deleted)

    async def mark_frozen(self, id: int) -> None:
        frozen = {'status': UserStatus.FROZEN}
        return await self.update_user(id, frozen)

    async def get_user_with_accounts(self, id: int) -> BaseModel:
        return await self._get_object_with_related(User, id, 'accounts')

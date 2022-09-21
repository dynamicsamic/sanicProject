from typing import Any
from sqlalchemy import Integer, Column, ForeignKey, String, Boolean, Numeric, select, func, Enum, update
from sqlalchemy.orm import declarative_base, relationship, selectinload
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy.engine.result import ScalarResult
from sqlalchemy.ext.asyncio import AsyncSession
from sanic.exceptions import NotFound, BadRequest

from .modelmanager import UserManager, BaseManager
from .user_status import UserStatus
#class UserStatus(PyEnum):
#    ACTIVE = 1
#    INACTIVE = 2
#    FROZEN = 3
#    DELETED = 4



Base = declarative_base()

class BaseModel(Base):
    __abstract__ = True

    id = Column(Integer, primary_key=True)


    def to_dict(self):
        return 'NOT_IMPLEMENTED'

    def __repr__(self):
        return 'NOT_IMPLEMENTED'

from functools import partial

class Product(BaseModel):
    __tablename__ = 'product'

    name = Column(String(length=50), nullable=False, unique=True)
    description = Column(String(250), nullable=True)
    price = Column(Numeric(10, 2), nullable=False)

    def to_dict(self):
        return {
            'id': self.id,
            'product': self.name,
            'price': self.price,
        }

    def __repr__(self):
        return 'Product: {self.name}, price: {self.price} $'

class User(BaseModel):
    __tablename__ = 'user'

    username = Column(String(length=20), nullable=False, unique=True)
    email = Column(String(length=50), nullable=False, unique=True)
    password = Column(String(length=150), nullable=False)
    status = Column(Enum(UserStatus), nullable=False, default=UserStatus.INACTIVE)
    _is_admin = Column(Boolean, nullable=False, default=False)

    # :?? confirmation_code ??


    #accounts = relationship('Account', back_populates='user', lazy='select')
    #accounts = relationship('Account', back_populates='user', lazy='joined')
    accounts = relationship('Account', back_populates='user')

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.password = generate_password_hash(self.password)
        

    @property
    def is_admin(self):
        return self._is_admin

    @property
    def is_active(self):
        return self.status == UserStatus.active

    def set_password(self):
        self.password = generate_password_hash(self.password)

    def check_password(self, recieved_password: str):
        return check_password_hash(self.password, recieved_password)

    def get_valid_account(self, to_spend):
        for account in self.accounts:
            if account.available_money >= to_spend:
                return account
        
        return False

    def add_session(self, session):
        self.session = session
        #res = select(Account).where(Account.user_id==self.id)
        #return res

    async def get_accounts(self, session: AsyncSession) -> ScalarResult:
        query = select(Account).where(Account.user_id==self.id)
        queryset = await session.execute(query)
        return queryset.scalars()

    async def get_transactions(self, session: AsyncSession) -> ScalarResult:
#        query = select(Transaction).where(Transaction.account.user_id == self.id)
        query = select(Transaction).join(Account, Account.id == Transaction.account_id).where(Account.user_id == self.id)
        queryset = await session.execute(query)
        return queryset.scalars()

    async def raise_permission(self):
        self._is_admin = True

    def activate(self):
        self.status = UserStatus.active

    def to_dict(self, accounts: ScalarResult = None):
        data = {
            'id': self.id,
            'name': self.username,
            'email': self.email,
            'status': self.status,
            'admin': self.is_admin,
        }
        if accounts:
            data['accounts'] = [account.to_dict() for account in accounts]
            #data['accounts'] = await self.foo()
            #data['accounts'] = [account.to_dict() for account in self.accounts]

        return data

    def __repr__(self):
        return f'User: {self.username}, status: {self.status}'


from sqlalchemy.sql.selectable import Select
class Account(BaseModel):
    __tablename__ = 'account'

    initial_amount = Column(Integer, default=0) # 0 is ok; check amount >= 0
    user_id = Column(Integer, ForeignKey('user.id'), nullable=False)
    user_status = Column(Enum(UserStatus), nullable=False, default=UserStatus.INACTIVE)

    user = relationship('User', back_populates='accounts')
    transactions = relationship('Transaction', back_populates='account')
    #transactions = relationship('Transaction', back_populates='account', lazy='selectin')
    #transactions = relationship('Transaction', back_populates='account', lazy='joined')

    @property
    def available_money(self):
        return self.initial_amount + sum(trans.amount for trans in self.transactions)
        #return (
        #    select(func.sum(Transaction.amount)).
        #    where(Transaction.account_id == self.id).
        #    and_(Transaction._is_valid)
        #)

    #def get_session(self, session):
    #    self.session = session

    async def get_current_sum(self, session: AsyncSession):
        transquery = select(func.sum(Transaction.amount)).where(Transaction.account_id==self.id)
        result = await session.execute(transquery)
        return result.scalar()



    def to_dict(self):
        return {
            'account_id': self.id,
            'user_id': self.user_id,
            #'username': self.user.username,
            'amount': self.initial_amount,
            #'transactions': [trans.to_dict() for trans in self.transactions],
            #'transactions': self.transactions
            #'account_user': self.user.username,
            #'available_sum': self.available_money,
        }

    def __repr__(self):
        #return f"{[i.to_dict() for i in self.transactions]}"
        return f'Account: id({self.id})'
        #return f'Account: id({self.id}), User({self.user}), Money({self.available_money} $)'


class Transaction(BaseModel):
    """Negative integers = spend operation,
    positive integers = add operation.
    """
    __tablename__ = 'transaction'

    amount = Column(Integer, nullable=False)
    account_id = Column(Integer, ForeignKey('account.id'), nullable=False)
    #user_id = Column(Integer, nullable=False)
    #timestamp = Column(Date)
    #
    _is_valid = Column(Boolean, nullable=False, default=False)

    account = relationship('Account', back_populates='transactions', )

    def check(self):
        self._is_valid = (
            self.amount > 0 or
            self.amount <= self.account.available_money
        )
        print('A valid transaction' if self._is_valid else 'Invalid transaction')

    def to_dict(self):
        return {
            'amount': self.amount,
            'account': self.account_id,
            'valid': self._is_valid,
        }

    def __repr__(self):
        return f'Transaction: Validity({self._is_valid}), Account({self.account_id}), Amount({self.amount} $)'

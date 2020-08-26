"""
Common models for authentication backend
"""
try:
    from sqlalchemy import (
        MetaData,
        Table,
        UniqueConstraint,
        CheckConstraint,
        Column,
        ForeignKey,
        Integer,
        String,
        Boolean,
        DateTime,
    )
    from crax.database.model import BaseTable
except ImportError:
    raise ModuleNotFoundError("SQLAlchemy should be installed to use Crax Auth Models")


class Group(BaseTable):
    table_name = "groups"

    name = Column(String(length=100), nullable=False)


class User(BaseTable):
    table_name = "users"

    def __init__(self):
        self._pk = 0
        self._full_name = ""
        self._session = None

    @property
    def is_authenticated(self) -> bool:
        return True

    @property
    def pk(self) -> int:
        return self._pk

    @pk.setter
    def pk(self, val) -> None:
        self._pk = val

    @property
    def session(self) -> str:
        return self._session

    @session.setter
    def session(self, val) -> None:
        self._session = val

    @property
    def full_name(self) -> str:
        return self._full_name

    @full_name.setter
    def full_name(self, val) -> None:
        self._full_name = val

    def __str__(self) -> str:
        return self.full_name

    username = Column(String(length=50), nullable=False)
    password = Column(String(length=250), nullable=False)
    first_name = Column(String(length=50),)
    middle_name = Column(String(length=50), nullable=True)
    last_name = Column(String(length=50), nullable=True)
    phone = Column(String(length=20), nullable=True)
    email = Column(String(length=150), nullable=True)
    is_active = Column(Boolean(), nullable=True, default=True)
    is_staff = Column(Boolean(), nullable=True, default=False)
    is_superuser = Column(Boolean(), nullable=True, default=False)
    date_joined = Column(DateTime(), nullable=True)
    last_login = Column(DateTime(), nullable=True)
    unique = UniqueConstraint("username", name="username")


class Permission(BaseTable):
    table_name = "permissions"

    name = Column(String(length=100), nullable=False)
    model = Column(String(length=50), nullable=False)
    can_read = Column(Boolean(), default=True)
    can_write = Column(Boolean(), default=False)
    can_create = Column(Boolean(), default=False)
    can_delete = Column(Boolean(), default=False)


class UserGroup(BaseTable):
    table_name = "user_groups"
    user_id = Column(Integer, ForeignKey(User.id))
    group_id = Column(Integer, ForeignKey(Group.id))


class UserPermission(BaseTable):
    table_name = "user_permissions"
    user_id = Column(Integer, ForeignKey(User.id))
    permission_id = Column(Integer, ForeignKey(Permission.id))


class GroupPermission(BaseTable):
    table_name = "group_permissions"
    group_id = Column(Integer, ForeignKey(Group.id))
    permission_id = Column(Integer, ForeignKey(Permission.id))


class AnonymousUser:
    @property
    def is_authenticated(self) -> bool:
        return False

    @property
    def pk(self) -> int:
        return 0

    @property
    def username(self) -> str:
        return ""

    @property
    def is_staff(self) -> bool:
        return False

    @property
    def is_superuser(self) -> bool:
        return False

    @property
    def is_active(self) -> bool:
        return False

    @property
    def session(self) -> None:
        return None

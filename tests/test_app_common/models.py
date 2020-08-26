import sqlalchemy as sa
from crax.auth.models import User

from crax.database.model import BaseTable


class Notes(BaseTable):
    id = sa.Column(sa.Integer, primary_key=True)
    user_id = sa.Column(sa.Integer, sa.ForeignKey(User.id))
    text = sa.Column(sa.String(length=100))
    completed = sa.Column(sa.Boolean)

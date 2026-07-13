"""
User (read-only model)
SPDX - License - Identifier: LGPL - 3.0 - or -later
Auteurs : Gabriel C. Ullmann, Fabio Petrillo, 2025
"""

from db import get_sqlalchemy_session
from orders.models.user import User
from orders.models.user_type import UserType


def get_user_by_id(user_id):
    """Get user by ID."""
    session = get_sqlalchemy_session()
    result = (
        session.query(User, UserType)
        .join(UserType, User.user_type_id == UserType.id)
        .filter(User.id == user_id)
        .first()
    )

    if result:
        user, user_type = result
        return {
            'id': user.id,
            'name': user.name,
            'email': user.email,
            'user_type_id': user.user_type_id,
            'user_type_name': user_type.name,
        }
    return {}

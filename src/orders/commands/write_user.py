"""
Users (write-only model)
SPDX - License - Identifier: LGPL - 3.0 - or -later
Auteurs : Gabriel C. Ullmann, Fabio Petrillo, 2025
"""

import datetime
from typing import Optional

from db import get_sqlalchemy_session
from logger import Logger
from orders.commands.user_event_producer import UserEventProducer
from orders.models.user import User
from orders.models.user_type import UserType

logger = Logger.get_instance("write_user")
USER_EVENTS_TOPIC = "user-events"


def _get_user_type_name(session, user_type_id: int) -> str:
    user_type = session.query(UserType).filter(UserType.id == user_type_id).first()
    if user_type is None:
        raise ValueError(f"Invalid user_type_id: {user_type_id}")
    return user_type.name


def _publish_user_event(event_payload: dict) -> None:
    """Send a user event to Kafka without breaking the DB transaction result if Kafka is down."""
    try:
        UserEventProducer().publish(USER_EVENTS_TOPIC, event_payload)
    except Exception as exc:
        logger.warning(f"Impossible de publier l'événement Kafka {event_payload.get('event')}: {exc}")


def add_user(name: str, email: str, user_type_id: Optional[int] = 1):
    """Insert user in MySQL and publish a UserCreated event."""
    if not name or not email:
        raise ValueError("Cannot create user. A user must have name and email.")

    user_type_id = int(user_type_id or 1)
    session = get_sqlalchemy_session()

    try:
        user_type_name = _get_user_type_name(session, user_type_id)
        new_user = User(name=name, email=email, user_type_id=user_type_id)
        session.add(new_user)
        session.flush()
        session.commit()

        _publish_user_event({
            "event": "UserCreated",
            "id": new_user.id,
            "name": new_user.name,
            "email": new_user.email,
            "user_type_id": new_user.user_type_id,
            "user_type_name": user_type_name,
            "datetime": str(datetime.datetime.now()),
        })
        return new_user.id
    except Exception as e:
        session.rollback()
        raise e
    finally:
        session.close()


def delete_user(user_id: int):
    """Delete user in MySQL and publish a UserDeleted event."""
    session = get_sqlalchemy_session()
    try:
        user = session.query(User).filter(User.id == user_id).first()
        if user:
            user_snapshot = {
                "event": "UserDeleted",
                "id": user.id,
                "name": user.name,
                "email": user.email,
                "user_type_id": user.user_type_id,
                "user_type_name": _get_user_type_name(session, user.user_type_id),
                "datetime": str(datetime.datetime.now()),
            }
            session.delete(user)
            session.commit()
            _publish_user_event(user_snapshot)
            return 1
        return 0
    except Exception as e:
        session.rollback()
        raise e
    finally:
        session.close()

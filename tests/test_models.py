import uuid

import pytest
from sqlalchemy import inspect, select
from sqlalchemy.exc import IntegrityError

from app.backend.models import Attribute, Group, GroupMembership, User, UserAttribute


def _create_user(username: str, email: str) -> User:
    return User(username=username, email=email)


def test_tables_exist(test_engine):
    inspector = inspect(test_engine)
    table_names = set(inspector.get_table_names())
    assert {"users", "attributes", "user_attributes", "groups", "group_memberships"}.issubset(table_names)


def test_users_have_unique_username_and_email(db):
    db.add(_create_user("alice", "alice@example.com"))
    db.commit()

    db.add(_create_user("alice", "alice2@example.com"))
    with pytest.raises(IntegrityError):
        db.commit()
    db.rollback()

    db.add(_create_user("alice2", "alice@example.com"))
    with pytest.raises(IntegrityError):
        db.commit()


def test_attributes_have_unique_value(db):
    db.add(Attribute(value="software"))
    db.commit()

    db.add(Attribute(value="software"))
    with pytest.raises(IntegrityError):
        db.commit()


def test_user_attribute_unique_pair_constraint(db):
    user = _create_user("bob", "bob@example.com")
    attribute = Attribute(value="engineer")
    db.add_all([user, attribute])
    db.commit()

    db.add(UserAttribute(user_id=user.id, attribute_id=attribute.id))
    db.commit()

    db.add(UserAttribute(user_id=user.id, attribute_id=attribute.id))
    with pytest.raises(IntegrityError):
        db.commit()


def test_group_membership_unique_user_constraint(db):
    user = _create_user("carol", "carol@example.com")
    group1 = Group(name="group-1")
    group2 = Group(name="group-2")
    db.add_all([user, group1, group2])
    db.commit()

    db.add(GroupMembership(group_id=group1.id, user_id=user.id, reason="first"))
    db.commit()

    db.add(GroupMembership(group_id=group2.id, user_id=user.id, reason="second"))
    with pytest.raises(IntegrityError):
        db.commit()


def test_deleting_user_removes_related_links(db):
    user = _create_user("dave", "dave@example.com")
    attribute = Attribute(value="gamer")
    group = Group(name="group-x")
    db.add_all([user, attribute, group])
    db.commit()

    db.add(UserAttribute(user_id=user.id, attribute_id=attribute.id))
    db.add(GroupMembership(group_id=group.id, user_id=user.id, reason="assigned"))
    db.commit()

    db.delete(user)
    db.commit()

    assert db.scalars(select(UserAttribute).where(UserAttribute.user_id == user.id)).all() == []
    assert db.scalars(select(GroupMembership).where(GroupMembership.user_id == user.id)).all() == []
    assert db.get(Group, group.id) is not None


def test_uuid_ids_are_generated(db):
    user = _create_user("erin", "erin@example.com")
    attribute = Attribute(value="researcher")
    group = Group(name="group-y")
    db.add_all([user, attribute, group])
    db.commit()

    assert isinstance(user.id, uuid.UUID)
    assert isinstance(attribute.id, uuid.UUID)
    assert isinstance(group.id, uuid.UUID)

from datetime import datetime, timedelta, timezone

from sqlalchemy import func, select

from app.backend.models import Attribute, Group, GroupMembership, User, UserAttribute
from app.backend.services.grouping import (
    get_group_members,
    get_user_attributes,
    get_user_group,
    normalize_attributes,
    remove_user_membership,
    run_grouping_cycle,
    set_user_attributes,
)


def _create_user(db, username: str, email: str, created_at: datetime) -> User:
    user = User(username=username, email=email, created_at=created_at)
    db.add(user)
    db.flush()
    return user


def test_normalize_attributes_dedupes_and_cleans_values():
    raw = [" Software ", "ENGINEER", "", "engineer", "  ", "Brussels"]
    assert normalize_attributes(raw) == ["software", "engineer", "brussels"]


def test_set_user_attributes_replaces_existing_links(db):
    user = User(username="alice", email="alice@example.com")
    db.add(user)
    db.commit()

    first = set_user_attributes(db, user, ["Software", "Engineer", "Engineer"])
    db.commit()
    assert first == ["software", "engineer"]

    second = set_user_attributes(db, user, ["Researcher"])
    db.commit()
    assert second == ["researcher"]

    attr_values = set(get_user_attributes(db, user.id))
    assert attr_values == {"researcher"}
    assert db.scalar(select(func.count(Attribute.id))) == 3
    assert db.scalar(select(func.count(UserAttribute.user_id)).where(UserAttribute.user_id == user.id)) == 1


def test_remove_user_membership_deletes_empty_group(db):
    user = User(username="bob", email="bob@example.com")
    group = Group(name="group-1")
    db.add_all([user, group])
    db.commit()

    db.add(GroupMembership(group_id=group.id, user_id=user.id, reason="assigned"))
    db.commit()

    remove_user_membership(db, user.id)
    db.commit()

    membership = db.scalars(select(GroupMembership).where(GroupMembership.user_id == user.id)).first()
    assert membership is None
    assert db.get(Group, group.id) is None


def test_remove_user_membership_keeps_group_with_other_members(db):
    group = Group(name="group-1")
    user_1 = User(username="cathy", email="cathy@example.com")
    user_2 = User(username="dan", email="dan@example.com")
    db.add_all([group, user_1, user_2])
    db.commit()

    db.add(GroupMembership(group_id=group.id, user_id=user_1.id, reason="assigned"))
    db.add(GroupMembership(group_id=group.id, user_id=user_2.id, reason="assigned"))
    db.commit()

    remove_user_membership(db, user_1.id)
    db.commit()

    assert db.get(Group, group.id) is not None
    remaining = db.scalars(select(GroupMembership).where(GroupMembership.group_id == group.id)).all()
    assert len(remaining) == 1
    assert remaining[0].user_id == user_2.id


def test_run_grouping_cycle_assigns_users_to_expected_groups(db):
    base = datetime(2026, 1, 1, tzinfo=timezone.utc)
    u1 = _create_user(db, "u1", "u1@example.com", base)
    u2 = _create_user(db, "u2", "u2@example.com", base + timedelta(seconds=1))
    u3 = _create_user(db, "u3", "u3@example.com", base + timedelta(seconds=2))
    db.commit()

    set_user_attributes(db, u1, ["software", "engineer", "senior"])
    set_user_attributes(db, u2, ["software", "engineer", "gamer"])
    set_user_attributes(db, u3, ["researcher", "counterstrike"])
    db.commit()

    assigned = run_grouping_cycle(db, min_match=2)
    assert assigned == 3

    g1 = get_user_group(db, u1.id)
    g2 = get_user_group(db, u2.id)
    g3 = get_user_group(db, u3.id)
    assert g1 is not None and g2 is not None and g3 is not None
    assert g1.id == g2.id
    assert g3.id != g1.id

    second_run = run_grouping_cycle(db, min_match=2)
    assert second_run == 0


def test_run_grouping_cycle_respects_min_match(db):
    base = datetime(2026, 1, 1, tzinfo=timezone.utc)
    u1 = _create_user(db, "u4", "u4@example.com", base)
    u2 = _create_user(db, "u5", "u5@example.com", base + timedelta(seconds=1))
    db.commit()

    set_user_attributes(db, u1, ["software", "engineer", "belgium"])
    set_user_attributes(db, u2, ["software", "engineer", "gamer"])
    db.commit()

    assigned = run_grouping_cycle(db, min_match=3)
    assert assigned == 2

    g1 = get_user_group(db, u1.id)
    g2 = get_user_group(db, u2.id)
    assert g1 is not None and g2 is not None
    assert g1.id != g2.id


def test_run_grouping_cycle_regroup_all_rebuilds_existing_groups(db):
    base = datetime(2026, 1, 1, tzinfo=timezone.utc)
    u1 = _create_user(db, "ra", "ra@example.com", base)
    u2 = _create_user(db, "rb", "rb@example.com", base + timedelta(seconds=1))
    db.commit()

    set_user_attributes(db, u1, ["software", "engineer", "senior"])
    set_user_attributes(db, u2, ["software", "engineer", "gamer"])
    db.commit()

    initial_assigned = run_grouping_cycle(db, min_match=2)
    assert initial_assigned == 2
    initial_g1 = get_user_group(db, u1.id)
    initial_g2 = get_user_group(db, u2.id)
    assert initial_g1 is not None and initial_g2 is not None
    assert initial_g1.id == initial_g2.id

    reassigned = run_grouping_cycle(db, min_match=4, regroup_all=True)
    assert reassigned == 2
    updated_g1 = get_user_group(db, u1.id)
    updated_g2 = get_user_group(db, u2.id)
    assert updated_g1 is not None and updated_g2 is not None
    assert updated_g1.id != updated_g2.id


def test_get_group_members_and_user_attributes(db):
    base = datetime(2026, 1, 1, tzinfo=timezone.utc)
    u1 = _create_user(db, "x1", "x1@example.com", base)
    u2 = _create_user(db, "x2", "x2@example.com", base + timedelta(seconds=1))
    db.commit()

    set_user_attributes(db, u1, ["a", "b", "c"])
    set_user_attributes(db, u2, ["a", "b", "d"])
    db.commit()
    run_grouping_cycle(db, min_match=2)

    group = get_user_group(db, u1.id)
    assert group is not None

    members = get_group_members(db, group.id)
    member_ids = {member.id for member in members}
    assert member_ids == {u1.id, u2.id}

    attrs = set(get_user_attributes(db, u2.id))
    assert attrs == {"a", "b", "d"}

from __future__ import annotations

import logging
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.core.config import settings
from app.models import Attribute, Group, GroupMembership, User, UserAttribute

logger = logging.getLogger(__name__)


def normalize_attributes(raw_values: list[str]) -> list[str]:
    cleaned: list[str] = []
    seen: set[str] = set()
    for value in raw_values:
        normalized = value.strip().lower()
        if not normalized:
            continue
        if normalized in seen:
            continue
        seen.add(normalized)
        cleaned.append(normalized)
    return cleaned


def set_user_attributes(db: Session, user: User, attribute_values: list[str]) -> list[str]:
    values = normalize_attributes(attribute_values)

    current_links = db.scalars(select(UserAttribute).where(UserAttribute.user_id == user.id)).all()
    for link in current_links:
        db.delete(link)
    db.flush()

    if not values:
        return []

    existing_attrs = db.scalars(select(Attribute).where(Attribute.value.in_(values))).all()
    existing_by_value = {attr.value: attr for attr in existing_attrs}

    for value in values:
        attribute = existing_by_value.get(value)
        if attribute is None:
            attribute = Attribute(value=value)
            db.add(attribute)
            db.flush()
            existing_by_value[value] = attribute
        db.add(UserAttribute(user_id=user.id, attribute_id=attribute.id))

    db.flush()
    return values


def remove_user_membership(db: Session, user_id: UUID) -> None:
    membership = db.scalars(
        select(GroupMembership).where(GroupMembership.user_id == user_id)
    ).first()
    if membership is not None:
        group_id = membership.group_id
        db.delete(membership)
        db.flush()

        has_members = db.scalars(
            select(GroupMembership).where(GroupMembership.group_id == group_id)
        ).first()
        if has_members is None:
            group = db.get(Group, group_id)
            if group is not None:
                db.delete(group)


def _get_user_attr_set(db: Session, user_id: UUID) -> set[str]:
    rows = db.execute(
        select(Attribute.value)
        .join(UserAttribute, UserAttribute.attribute_id == Attribute.id)
        .where(UserAttribute.user_id == user_id)
    ).all()
    return {row[0] for row in rows}


def _shared_count(left: set[str], right: set[str]) -> int:
    return len(left.intersection(right))


def run_grouping_cycle(db: Session, min_match: int | None = None) -> int:
    threshold = settings.min_match if min_match is None else max(min_match, 0)

    users = db.scalars(select(User).order_by(User.created_at.asc())).all()

    membership_rows = db.execute(
        select(GroupMembership.group_id, GroupMembership.user_id)
    ).all()
    grouped_user_ids = {row[1] for row in membership_rows}

    group_member_map: dict[UUID, list[UUID]] = {}
    for group_id, user_id in membership_rows:
        group_member_map.setdefault(group_id, []).append(user_id)

    attr_rows = db.execute(
        select(UserAttribute.user_id, Attribute.value)
        .join(Attribute, Attribute.id == UserAttribute.attribute_id)
    ).all()
    user_attr_map: dict[UUID, set[str]] = {}
    for user_id, value in attr_rows:
        user_attr_map.setdefault(user_id, set()).add(value)

    ungrouped_users = [u for u in users if u.id not in grouped_user_ids]

    assigned_count = 0

    for user in ungrouped_users:
        user_attrs = user_attr_map.get(user.id, set())

        best_group_id: UUID | None = None
        best_score = -1

        for group_id, member_ids in group_member_map.items():
            if not member_ids:
                continue

            # Grouping logic:
            # - Compare an ungrouped user against all members in each existing group.
            # - For each group we keep the best overlap score (max shared attributes with any member).
            # - If best score >= MIN_MATCH, assign user to that group.
            # - If no group reaches MIN_MATCH, create a new group for that user.
            #
            # This keeps the process non-real-time and batch-friendly, while enforcing the
            # configurable threshold for similarity.
            group_score = 0
            for member_id in member_ids:
                member_attrs = user_attr_map.get(member_id, set())
                score = _shared_count(user_attrs, member_attrs)
                if score > group_score:
                    group_score = score

            if group_score >= threshold and group_score > best_score:
                best_score = group_score
                best_group_id = group_id

        if best_group_id is None:
            group = Group(name=f"Group-{str(user.id)[:8]}")
            db.add(group)
            db.flush()
            best_group_id = group.id
            group_member_map[best_group_id] = []

        db.add(
            GroupMembership(
                group_id=best_group_id,
                user_id=user.id,
                reason=f"Assigned by batch grouping process (min_match={threshold})",
            )
        )
        db.flush()

        group_member_map.setdefault(best_group_id, []).append(user.id)
        grouped_user_ids.add(user.id)
        user_attr_map.setdefault(user.id, set())

        assigned_count += 1

    db.commit()
    logger.info("Grouping cycle finished. Assigned users: %s", assigned_count)
    return assigned_count


def get_user_attributes(db: Session, user_id: UUID) -> list[str]:
    return list(_get_user_attr_set(db, user_id))


def get_group_members(db: Session, group_id: UUID) -> list[User]:
    return db.scalars(
        select(User)
        .join(GroupMembership, GroupMembership.user_id == User.id)
        .where(GroupMembership.group_id == group_id)
        .order_by(User.created_at.asc())
    ).all()


def get_user_group(db: Session, user_id: UUID) -> Group | None:
    membership = db.scalars(
        select(GroupMembership)
        .where(GroupMembership.user_id == user_id)
        .options(joinedload(GroupMembership.group))
    ).first()
    if membership is None:
        return None
    return membership.group

CREATE TABLE users (
    id UUID PRIMARY KEY,
    username VARCHAR(100) NOT NULL UNIQUE,
    email VARCHAR(255) NOT NULL UNIQUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE attributes (
    id UUID PRIMARY KEY,
    value VARCHAR(100) NOT NULL UNIQUE
);

CREATE TABLE user_attributes (
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    attribute_id UUID NOT NULL REFERENCES attributes(id) ON DELETE CASCADE,
    PRIMARY KEY (user_id, attribute_id),
    CONSTRAINT uq_user_attribute UNIQUE (user_id, attribute_id)
);

CREATE TABLE groups (
    id UUID PRIMARY KEY,
    name VARCHAR(120) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE group_memberships (
    id UUID PRIMARY KEY,
    group_id UUID NOT NULL REFERENCES groups(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    joined_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    reason TEXT NOT NULL,
    CONSTRAINT uq_group_membership_user UNIQUE (user_id)
);

CREATE INDEX ix_users_username ON users (username);
CREATE INDEX ix_users_email ON users (email);
CREATE INDEX ix_attributes_value ON attributes (value);
CREATE INDEX ix_group_memberships_group_id ON group_memberships (group_id);
CREATE INDEX ix_group_memberships_user_id ON group_memberships (user_id);

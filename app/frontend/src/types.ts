export type User = {
  id: string;
  username: string;
  email: string;
  created_at: string;
};

export type UserAttributesResponse = {
  user_id: string;
  attributes: string[];
};

export type GroupMember = {
  id: string;
  username: string;
  email: string;
};

export type Group = {
  id: string;
  name: string;
  created_at: string;
  members: GroupMember[];
};

export type UserGroupResponse = {
  user_id: string;
  group: Group | null;
};

export type GroupingRunResponse = {
  assigned_users: number;
  min_match: number;
};

import type {
  GroupingRunResponse,
  User,
  UserAttributesResponse,
  UserGroupResponse,
} from "./types";

const API_BASE = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    headers: {
      "Content-Type": "application/json",
      ...(init?.headers ?? {}),
    },
    ...init,
  });

  if (!response.ok) {
    let detail = "Request failed";
    try {
      const payload = await response.json();
      if (typeof payload?.detail === "string") {
        detail = payload.detail;
      }
    } catch {
      detail = `HTTP ${response.status}`;
    }
    throw new Error(detail);
  }

  if (response.status === 204) {
    return undefined as T;
  }

  return (await response.json()) as T;
}

export async function createUser(payload: {
  username: string;
  email: string;
}): Promise<User> {
  return request<User>("/api/users", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function getUsers(): Promise<User[]> {
  return request<User[]>("/api/users");
}

export async function getUser(userId: string): Promise<User> {
  return request<User>(`/api/users/${userId}`);
}

export async function getUserAttributes(userId: string): Promise<UserAttributesResponse> {
  return request<UserAttributesResponse>(`/api/users/${userId}/attributes`);
}

export async function setUserAttributes(
  userId: string,
  attributes: string[],
): Promise<UserAttributesResponse> {
  return request<UserAttributesResponse>(`/api/users/${userId}/attributes`, {
    method: "PUT",
    body: JSON.stringify({ attributes }),
  });
}

export async function getUserGroup(userId: string): Promise<UserGroupResponse> {
  return request<UserGroupResponse>(`/api/users/${userId}/group`);
}

export async function runGrouping(minMatch?: number): Promise<GroupingRunResponse> {
  const suffix = minMatch === undefined ? "" : `?min_match=${encodeURIComponent(minMatch)}`;
  return request<GroupingRunResponse>(`/api/grouping/run${suffix}`, {
    method: "POST",
  });
}

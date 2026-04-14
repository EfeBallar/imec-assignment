import { useEffect, useState } from "react";

import { getUsers } from "../api";
import type { User } from "../types";

type UserSelectorProps = {
  selectedUserId: string;
  onChange: (userId: string) => void;
  label?: string;
};

export function UserSelector({ selectedUserId, onChange, label = "Select user" }: UserSelectorProps) {
  const [users, setUsers] = useState<User[]>([]);
  const [error, setError] = useState<string>("");
  const [loading, setLoading] = useState<boolean>(false);

  useEffect(() => {
    let mounted = true;
    setLoading(true);
    setError("");

    async function loadUsers() {
      try {
        const result = await getUsers();
        if (!mounted) {
          return;
        }
        setUsers(result);
      } catch (err) {
        if (!mounted) {
          return;
        }
        setError(err instanceof Error ? err.message : "Failed to load users");
      } finally {
        if (mounted) {
          setLoading(false);
        }
      }
    }

    void loadUsers();

    return () => {
      mounted = false;
    };
  }, []);

  return (
    <div className="field">
      <label htmlFor="user-selector">{label}</label>
      <select
        id="user-selector"
        value={selectedUserId}
        onChange={(event) => onChange(event.target.value)}
        disabled={loading}
      >
        <option value="">Choose a user</option>
        {users.map((user) => (
          <option key={user.id} value={user.id}>
            {user.username} ({user.email})
          </option>
        ))}
      </select>
      {loading && <small>Loading users...</small>}
      {!loading && users.length === 0 && <small>No users yet. Create one first.</small>}
      {error && <small className="error">{error}</small>}
    </div>
  );
}

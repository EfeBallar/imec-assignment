import { useMemo, useState } from "react";

import { getUserAttributes, getUserGroup, runGrouping } from "../api";
import { UserSelector } from "../components/UserSelector";
import type { Group, GroupingRunResponse } from "../types";

type MemberWithAttributes = {
  id: string;
  username: string;
  email: string;
  attributes: string[];
};

async function getGroupWithMemberAttributes(userId: string): Promise<{
  group: Group | null;
  members: MemberWithAttributes[];
}> {
  const groupResponse = await getUserGroup(userId);
  if (!groupResponse.group) {
    return { group: null, members: [] };
  }

  const memberAttributes = await Promise.all(
    groupResponse.group.members.map(async (member) => {
      const attrsResponse = await getUserAttributes(member.id);
      return {
        id: member.id,
        username: member.username,
        email: member.email,
        attributes: attrsResponse.attributes,
      };
    }),
  );

  return {
    group: groupResponse.group,
    members: memberAttributes,
  };
}

export function GroupViewPage() {
  const [selectedUserId, setSelectedUserId] = useState("");
  const [group, setGroup] = useState<Group | null>(null);
  const [members, setMembers] = useState<MemberWithAttributes[]>([]);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [minMatchInput, setMinMatchInput] = useState("");
  const [runningGrouping, setRunningGrouping] = useState(false);
  const [groupingResult, setGroupingResult] = useState<GroupingRunResponse | null>(null);

  const sortedMembers = useMemo(
    () => [...members].sort((left, right) => left.username.localeCompare(right.username)),
    [members],
  );

  async function loadUserGroup(userId: string) {
    if (!userId) {
      setGroup(null);
      setMembers([]);
      return;
    }

    setLoading(true);
    setError("");

    try {
      const response = await getGroupWithMemberAttributes(userId);
      setGroup(response.group);
      setMembers(response.members);
    } catch (err) {
      if (err instanceof Error) {
        setError(err.message);
      } else {
        setError("Failed to load group");
      }
    } finally {
      setLoading(false);
    }
  }

  function onUserChange(userId: string) {
    setSelectedUserId(userId);
    setGroupingResult(null);
    void loadUserGroup(userId);
  }

  async function onRunGrouping() {
    setRunningGrouping(true);
    setError("");
    setGroupingResult(null);

    let parsedMinMatch: number | undefined;
    if (minMatchInput.trim().length > 0) {
      const value = Number(minMatchInput);
      if (!Number.isInteger(value) || value < 0) {
        setRunningGrouping(false);
        setError("MIN_MATCH must be a non-negative integer");
        return;
      }
      parsedMinMatch = value;
    }

    try {
      const response = await runGrouping(parsedMinMatch);
      setGroupingResult(response);
      if (selectedUserId) {
        await loadUserGroup(selectedUserId);
      }
    } catch (err) {
      if (err instanceof Error) {
        setError(err.message);
      } else {
        setError("Failed to run grouping");
      }
    } finally {
      setRunningGrouping(false);
    }
  }

  return (
    <section className="panel panel-elevated page-enter">
      <div className="section-head">
        <h2>Group View</h2>
        <p className="muted">Inspect a user cluster and trigger a fresh grouping run when needed.</p>
      </div>

      <div className="stack group-controls">
        <UserSelector selectedUserId={selectedUserId} onChange={onUserChange} label="Select user to inspect group" />

        <div className="field-inline">
          <label htmlFor="min-match">MIN_MATCH override (optional)</label>
          <input
            id="min-match"
            type="number"
            min={0}
            step={1}
            value={minMatchInput}
            onChange={(event) => setMinMatchInput(event.target.value)}
            placeholder="Leave empty to use backend default"
          />
          <button className="btn btn-primary" type="button" onClick={onRunGrouping} disabled={runningGrouping}>
            {runningGrouping ? "Running..." : "Run Grouping"}
          </button>
        </div>

        {groupingResult && (
          <p className="feedback success">
            Grouping complete: assigned <strong>{groupingResult.assigned_users}</strong> users with min_match={" "}
            <strong>{groupingResult.min_match}</strong>
          </p>
        )}
      </div>

      {loading ? (
        <p className="muted">Loading group...</p>
      ) : !selectedUserId ? (
        <p className="muted">Select a user to see their group.</p>
      ) : !group ? (
        <p className="muted">This user is not assigned to a group yet.</p>
      ) : (
        <div className="stack">
          <div className="result">
            <p>
              <strong>Group name:</strong> {group.name}
            </p>
          </div>

          <h3>Members</h3>
          <ul className="list stacked">
            {sortedMembers.map((member) => (
              <li key={member.id} className="member-card">
                <p>
                  <strong>{member.username}</strong> ({member.email})
                </p>
                <p>
                  Attributes: {member.attributes.length ? member.attributes.join(", ") : "No attributes"}
                </p>
              </li>
            ))}
          </ul>
        </div>
      )}

      {error && <p className="feedback error">{error}</p>}
    </section>
  );
}

import { FormEvent, useMemo, useState } from "react";

import { getUserAttributes, setUserAttributes } from "../api";
import { UserSelector } from "../components/UserSelector";

function parseAttributeInput(input: string): string[] {
  return input
    .split(",")
    .map((part) => part.trim())
    .filter((part) => part.length > 0);
}

export function AttributeManagementPage() {
  const [selectedUserId, setSelectedUserId] = useState("");
  const [newAttribute, setNewAttribute] = useState("");
  const [attributes, setAttributes] = useState<string[]>([]);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);

  const sortedAttributes = useMemo(
    () => [...new Set(attributes.map((item) => item.trim()).filter((item) => item))].sort(),
    [attributes],
  );

  async function loadAttributes(userId: string) {
    if (!userId) {
      setAttributes([]);
      return;
    }
    setLoading(true);
    setError("");
    try {
      const response = await getUserAttributes(userId);
      setAttributes(response.attributes);
    } catch (err) {
      if (err instanceof Error) {
        setError(err.message);
      } else {
        setError("Failed to load attributes");
      }
    } finally {
      setLoading(false);
    }
  }

  function onUserChange(userId: string) {
    setSelectedUserId(userId);
    setError("");
    void loadAttributes(userId);
  }

  function addAttributes(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const parsed = parseAttributeInput(newAttribute);
    if (parsed.length === 0) {
      return;
    }
    setAttributes((current) => [...current, ...parsed]);
    setNewAttribute("");
  }

  function removeAttribute(value: string) {
    setAttributes((current) => current.filter((entry) => entry !== value));
  }

  async function saveAttributes() {
    if (!selectedUserId) {
      setError("Please select a user");
      return;
    }
    setSaving(true);
    setError("");
    try {
      const response = await setUserAttributes(selectedUserId, sortedAttributes);
      setAttributes(response.attributes);
    } catch (err) {
      if (err instanceof Error) {
        setError(err.message);
      } else {
        setError("Failed to save attributes");
      }
    } finally {
      setSaving(false);
    }
  }

  return (
    <section className="panel panel-elevated page-enter">
      <div className="section-head">
        <h2>Attribute Management</h2>
        <p className="muted">
          Define the tags that describe a user profile. These tags drive automatic similarity grouping.
        </p>
      </div>

      <div className="attribute-selector">
        <UserSelector selectedUserId={selectedUserId} onChange={onUserChange} />
      </div>

      <form className="stack attribute-form" onSubmit={addAttributes}>
        <div className="field">
          <label htmlFor="attribute-input">Attributes (comma-separated)</label>
          <input
            id="attribute-input"
            value={newAttribute}
            onChange={(event) => setNewAttribute(event.target.value)}
            placeholder="software, engineer, brussels"
            disabled={!selectedUserId}
          />
        </div>
        <button className="btn btn-primary" type="submit" disabled={!selectedUserId || loading}>
          Add
        </button>
      </form>

      <div className="stack attribute-current">
        <h3>Current Attributes</h3>
        {loading ? (
          <p className="muted">Loading...</p>
        ) : sortedAttributes.length === 0 ? (
          <p className="muted">No attributes yet.</p>
        ) : (
          <ul className="list">
            {sortedAttributes.map((attribute) => (
              <li key={attribute}>
                <span>{attribute}</span>
                <button className="btn" type="button" onClick={() => removeAttribute(attribute)}>
                  Remove
                </button>
              </li>
            ))}
          </ul>
        )}
      </div>

      <button
        className="btn btn-primary attribute-save"
        type="button"
        onClick={saveAttributes}
        disabled={!selectedUserId || saving}
      >
        {saving ? "Saving..." : "Save Attributes"}
      </button>

      {error && <p className="feedback error">{error}</p>}
    </section>
  );
}

import { FormEvent, useState } from "react";

import { createUser } from "../api";
import type { User } from "../types";

export function UserCreationPage() {
  const [username, setUsername] = useState("");
  const [email, setEmail] = useState("");
  const [createdUser, setCreatedUser] = useState<User | null>(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function onSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setLoading(true);
    setError("");
    setCreatedUser(null);

    try {
      const user = await createUser({
        username: username.trim(),
        email: email.trim(),
      });
      setCreatedUser(user);
      setUsername("");
      setEmail("");
    } catch (err) {
      if (err instanceof Error) {
        setError(err.message);
      } else {
        setError("Failed to create user");
      }
    } finally {
      setLoading(false);
    }
  }

  return (
    <section className="panel panel-elevated page-enter">
      <div className="section-head">
        <h2>Create User</h2>
        <p className="muted">Add a new account and generate a unique identity for grouping.</p>
      </div>

      <form className="stack" onSubmit={onSubmit}>
        <div className="field">
          <label htmlFor="username">Username</label>
          <input
            id="username"
            value={username}
            onChange={(event) => setUsername(event.target.value)}
            required
            minLength={3}
            maxLength={100}
            placeholder="alex.vermeer"
          />
        </div>

        <div className="field">
          <label htmlFor="email">Email</label>
          <input
            id="email"
            type="email"
            value={email}
            onChange={(event) => setEmail(event.target.value)}
            required
            placeholder="alex@example.com"
          />
        </div>

        <button className="btn btn-primary" type="submit" disabled={loading}>
          {loading ? "Creating..." : "Create"}
        </button>
      </form>

      {error && <p className="feedback error">{error}</p>}
      {createdUser && (
        <div className="result created-user-result" aria-live="polite">
          <strong>Account created</strong>
          <div className="meta-row">
            <span className="meta-label">Username</span>
            <span className="meta-value">{createdUser.username}</span>
          </div>
          <div className="meta-row">
            <span className="meta-label">Email</span>
            <span className="meta-value">{createdUser.email}</span>
          </div>
        </div>
      )}
    </section>
  );
}

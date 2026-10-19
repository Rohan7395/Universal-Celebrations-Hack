-- Care Team schema: the 12 tables from docs/BUILD-PLAN.md §4.
-- Timestamps are ISO 8601 text. JSON columns hold JSON text.

PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS tenants (
    id          TEXT PRIMARY KEY,
    name        TEXT NOT NULL,
    kind        TEXT NOT NULL,
    created_at  TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%S', 'now'))
);

-- A Client is the person being cared for; the family contact lives on the same row.
CREATE TABLE IF NOT EXISTS clients (
    id               TEXT PRIMARY KEY,
    tenant_id        TEXT NOT NULL REFERENCES tenants(id),
    name             TEXT NOT NULL,
    phone            TEXT,
    address          TEXT,
    notes            TEXT,
    family_name      TEXT,
    family_relation  TEXT,
    family_phone     TEXT,
    family_email     TEXT,
    created_at       TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%S', 'now'))
);

CREATE TABLE IF NOT EXISTS caregivers (
    id          TEXT PRIMARY KEY,
    tenant_id   TEXT NOT NULL REFERENCES tenants(id),
    name        TEXT NOT NULL,
    phone       TEXT,
    skills      TEXT NOT NULL DEFAULT '[]',
    active      INTEGER NOT NULL DEFAULT 1,
    created_at  TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%S', 'now'))
);

-- An open slot has client_id NULL and status 'open'; booking fills client_id.
CREATE TABLE IF NOT EXISTS visits (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    tenant_id     TEXT NOT NULL REFERENCES tenants(id),
    caregiver_id  TEXT NOT NULL REFERENCES caregivers(id),
    client_id     TEXT REFERENCES clients(id),
    case_id       INTEGER REFERENCES cases(id),
    starts_at     TEXT NOT NULL,
    ends_at       TEXT NOT NULL,
    status        TEXT NOT NULL DEFAULT 'open'
                  CHECK (status IN ('open', 'booked', 'done', 'cancelled')),
    reason        TEXT,
    created_at    TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%S', 'now'))
);

CREATE TABLE IF NOT EXISTS calls (
    id          TEXT PRIMARY KEY,
    tenant_id   TEXT NOT NULL REFERENCES tenants(id),
    client_id   TEXT REFERENCES clients(id),
    direction   TEXT NOT NULL CHECK (direction IN ('outbound', 'inbound')),
    channel     TEXT NOT NULL DEFAULT 'voice' CHECK (channel IN ('voice', 'chat')),
    agent       TEXT NOT NULL,
    status      TEXT NOT NULL DEFAULT 'active'
                CHECK (status IN ('active', 'ended', 'blocked', 'failed')),
    started_at  TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%S', 'now')),
    ended_at    TEXT
);

CREATE TABLE IF NOT EXISTS flags (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    tenant_id      TEXT NOT NULL REFERENCES tenants(id),
    client_id      TEXT NOT NULL REFERENCES clients(id),
    call_id        TEXT REFERENCES calls(id),
    what_was_said  TEXT NOT NULL,
    rule_severity  TEXT CHECK (rule_severity IN ('routine', 'watch', 'urgent', 'emergency')),
    llm_severity   TEXT CHECK (llm_severity IN ('routine', 'watch', 'urgent', 'emergency')),
    severity       TEXT NOT NULL CHECK (severity IN ('routine', 'watch', 'urgent', 'emergency')),
    actions        TEXT NOT NULL DEFAULT '[]',
    say            TEXT,
    created_at     TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%S', 'now'))
);

-- escalation: from a flag, goes to the human queue. uncovered: a question no policy answers.
CREATE TABLE IF NOT EXISTS cases (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    tenant_id    TEXT NOT NULL REFERENCES tenants(id),
    client_id    TEXT REFERENCES clients(id),
    kind         TEXT NOT NULL CHECK (kind IN ('escalation', 'uncovered')),
    severity     TEXT CHECK (severity IN ('routine', 'watch', 'urgent', 'emergency')),
    status       TEXT NOT NULL DEFAULT 'open'
                 CHECK (status IN ('open', 'accepted', 'resolved')),
    flag_id      INTEGER REFERENCES flags(id),
    summary      TEXT NOT NULL,
    assigned_to  TEXT,
    created_at   TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%S', 'now')),
    updated_at   TEXT
);

-- The agent room. Pushed to the dashboard over SSE.
CREATE TABLE IF NOT EXISTS messages (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    tenant_id   TEXT NOT NULL REFERENCES tenants(id),
    agent       TEXT NOT NULL,
    kind        TEXT NOT NULL CHECK (kind IN ('say', 'handoff', 'decision', 'system')),
    text        TEXT NOT NULL,
    payload     TEXT NOT NULL DEFAULT '{}',
    created_at  TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%S', 'now'))
);

-- Structured audit trail; never holds raw client text.
CREATE TABLE IF NOT EXISTS events (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    tenant_id   TEXT NOT NULL REFERENCES tenants(id),
    agent       TEXT NOT NULL,
    kind        TEXT NOT NULL,
    tool        TEXT,
    payload     TEXT NOT NULL DEFAULT '{}',
    created_at  TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%S', 'now'))
);

-- Kill switch. Agents may only tighten; loosening needs a human and a reason.
CREATE TABLE IF NOT EXISTS controls (
    key         TEXT PRIMARY KEY,
    value       TEXT NOT NULL,
    updated_by  TEXT NOT NULL,
    reason      TEXT,
    updated_at  TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%S', 'now'))
);

CREATE TABLE IF NOT EXISTS proposals (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    tenant_id     TEXT NOT NULL REFERENCES tenants(id),
    case_id       INTEGER REFERENCES cases(id),
    policy_name   TEXT NOT NULL,
    title         TEXT NOT NULL,
    body          TEXT NOT NULL,
    sources       TEXT NOT NULL DEFAULT '[]',
    status        TEXT NOT NULL DEFAULT 'pending'
                  CHECK (status IN ('pending', 'approved', 'rejected')),
    decided_by    TEXT,
    reason        TEXT,
    commit_sha    TEXT,
    check_result  TEXT,
    created_at    TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%S', 'now')),
    decided_at    TEXT
);

-- Which library skills the Architect picked (or skipped) for a tenant's Fleet.
CREATE TABLE IF NOT EXISTS fleet_skills (
    tenant_id    TEXT NOT NULL REFERENCES tenants(id),
    skill_name   TEXT NOT NULL,
    agent        TEXT,
    status       TEXT NOT NULL CHECK (status IN ('active', 'pending_approval', 'skipped')),
    risky        INTEGER NOT NULL DEFAULT 0,
    reason       TEXT,
    approved_by  TEXT,
    approved_at  TEXT,
    PRIMARY KEY (tenant_id, skill_name)
);

CREATE INDEX IF NOT EXISTS idx_messages_tenant ON messages(tenant_id, id);
CREATE INDEX IF NOT EXISTS idx_visits_open ON visits(tenant_id, status, starts_at);
CREATE INDEX IF NOT EXISTS idx_cases_queue ON cases(tenant_id, status);

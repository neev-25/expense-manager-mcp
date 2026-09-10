"""
models.py — SQL CREATE TABLE statements for every table.

Design notes:
  - SQLite is used for simplicity and portability.
  - Foreign keys are enabled via PRAGMA in db.py.
  - `is_deleted` on expenses enables soft-delete / restore.
  - `split_data` on event_expenses stores JSON (e.g. percentages / custom amounts).
  - `tags` on expenses stores comma-separated tag strings.
"""

# ── Expenses ──────────────────────────────────────────────────────────────────
EXPENSES = """
CREATE TABLE IF NOT EXISTS expenses (
    id              SERIAL PRIMARY KEY,
    title           TEXT    NOT NULL,
    amount          REAL    NOT NULL CHECK(amount > 0),
    description     TEXT    DEFAULT '',
    category_id     INTEGER REFERENCES categories(id) ON DELETE SET NULL,
    subcategory_id  INTEGER REFERENCES subcategories(id) ON DELETE SET NULL,
    merchant        TEXT    DEFAULT '',
    payment_method  TEXT    DEFAULT 'Cash',
    currency        TEXT    DEFAULT 'INR',
    location        TEXT    DEFAULT '',
    expense_date    TEXT    NOT NULL,          -- ISO 8601: YYYY-MM-DD
    receipt_url     TEXT    DEFAULT '',
    tags            TEXT    DEFAULT '',        -- comma-separated
    notes           TEXT    DEFAULT '',
    is_deleted      INTEGER DEFAULT 0,        -- 0 = active, 1 = soft-deleted
    created_at      TIMESTAMP DEFAULT NOW(),
    updated_at      TIMESTAMP DEFAULT NOW()
)
"""

# ── Categories & Subcategories ────────────────────────────────────────────────
CATEGORIES = """
CREATE TABLE IF NOT EXISTS categories (
    id      SERIAL PRIMARY KEY,
    name    TEXT    NOT NULL UNIQUE,
    icon    TEXT    DEFAULT '💰'
)
"""

SUBCATEGORIES = """
CREATE TABLE IF NOT EXISTS subcategories (
    id          SERIAL PRIMARY KEY,
    category_id INTEGER NOT NULL REFERENCES categories(id) ON DELETE CASCADE,
    name        TEXT    NOT NULL,
    UNIQUE(category_id, name)
)
"""

# ── Friends ───────────────────────────────────────────────────────────────────
FRIENDS = """
CREATE TABLE IF NOT EXISTS friends (
    id      SERIAL PRIMARY KEY,
    name    TEXT NOT NULL,
    email   TEXT DEFAULT '',
    phone   TEXT DEFAULT '',
    created_at TIMESTAMP DEFAULT NOW()
)
"""

# ── General Balances (Splitwise-lite, non-event) ──────────────────────────────
BALANCES = """
CREATE TABLE IF NOT EXISTS balances (
    id          SERIAL PRIMARY KEY,
    friend_id   INTEGER NOT NULL REFERENCES friends(id) ON DELETE CASCADE,
    amount      REAL    NOT NULL CHECK(amount > 0),
    direction   TEXT    NOT NULL CHECK(direction IN ('i_owe', 'they_owe')),
    reason      TEXT    DEFAULT '',
    expense_id  INTEGER REFERENCES expenses(id) ON DELETE SET NULL,
    status      TEXT    DEFAULT 'pending' CHECK(status IN ('pending', 'settled')),
    created_at  TIMESTAMP DEFAULT NOW()
)
"""

# ── Events ────────────────────────────────────────────────────────────────────
EVENTS = """
CREATE TABLE IF NOT EXISTS events (
    id          SERIAL PRIMARY KEY,
    title       TEXT NOT NULL,
    description TEXT DEFAULT '',
    start_date  TEXT DEFAULT '',
    end_date    TEXT DEFAULT '',
    status      TEXT DEFAULT 'active' CHECK(status IN ('active', 'closed')),
    created_at  TIMESTAMP DEFAULT NOW()
)
"""

EVENT_MEMBERS = """
CREATE TABLE IF NOT EXISTS event_members (
    event_id    INTEGER NOT NULL REFERENCES events(id) ON DELETE CASCADE,
    friend_id   INTEGER NOT NULL REFERENCES friends(id) ON DELETE CASCADE,
    PRIMARY KEY (event_id, friend_id)
)
"""

EVENT_EXPENSES = """
CREATE TABLE IF NOT EXISTS event_expenses (
    id                  SERIAL PRIMARY KEY,
    event_id            INTEGER NOT NULL REFERENCES events(id) ON DELETE CASCADE,
    expense_id          INTEGER REFERENCES expenses(id) ON DELETE SET NULL,
    title               TEXT NOT NULL,
    amount              REAL NOT NULL CHECK(amount > 0),
    paid_by_friend_id   INTEGER NOT NULL REFERENCES friends(id),
    split_type          TEXT NOT NULL CHECK(split_type IN ('equal','percentage','custom')),
    -- JSON string: {"friend_id": amount, ...}  for percentage/custom splits
    split_data          TEXT DEFAULT '{}',
    created_at          TIMESTAMP DEFAULT NOW()
)
"""

# ── Settlements ───────────────────────────────────────────────────────────────
SETTLEMENTS = """
CREATE TABLE IF NOT EXISTS settlements (
    id              SERIAL PRIMARY KEY,
    from_friend_id  INTEGER NOT NULL REFERENCES friends(id),
    to_friend_id    INTEGER NOT NULL REFERENCES friends(id),
    amount          REAL    NOT NULL CHECK(amount > 0),
    event_id        INTEGER REFERENCES events(id) ON DELETE SET NULL,
    status          TEXT    DEFAULT 'pending' CHECK(status IN ('pending', 'settled')),
    settled_at      TEXT    DEFAULT '',
    created_at      TIMESTAMP DEFAULT NOW()
)
"""

# ── Budgets ───────────────────────────────────────────────────────────────────
BUDGETS = """
CREATE TABLE IF NOT EXISTS budgets (
    id          SERIAL PRIMARY KEY,
    category_id INTEGER NOT NULL REFERENCES categories(id) ON DELETE CASCADE,
    month       INTEGER NOT NULL CHECK(month BETWEEN 1 AND 12),
    year        INTEGER NOT NULL,
    amount      REAL    NOT NULL CHECK(amount > 0),
    UNIQUE(category_id, month, year)
)
"""

# ── Recurring Expenses ────────────────────────────────────────────────────────
RECURRING = """
CREATE TABLE IF NOT EXISTS recurring_expenses (
    id              SERIAL PRIMARY KEY,
    title           TEXT    NOT NULL,
    amount          REAL    NOT NULL CHECK(amount > 0),
    category_id     INTEGER REFERENCES categories(id) ON DELETE SET NULL,
    payment_method  TEXT    DEFAULT 'Cash',
    frequency       TEXT    NOT NULL CHECK(frequency IN ('daily','weekly','monthly','yearly')),
    next_due_date   TEXT    NOT NULL,   -- ISO 8601: YYYY-MM-DD
    is_active       INTEGER DEFAULT 1,  -- 0 = paused
    created_at      TIMESTAMP DEFAULT NOW()
)
"""

# ── Ordered list used by db.py to initialise every table ─────────────────────
ALL_TABLES = [
    CATEGORIES,
    SUBCATEGORIES,
    FRIENDS,
    EXPENSES,
    BALANCES,
    EVENTS,
    EVENT_MEMBERS,
    EVENT_EXPENSES,
    SETTLEMENTS,
    BUDGETS,
    RECURRING,
]

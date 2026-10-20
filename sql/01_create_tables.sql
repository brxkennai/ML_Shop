-- Run once inside the database ml_shop (Query Tool in pgAdmin).
CREATE TABLE IF NOT EXISTS users (
    user_id BIGINT PRIMARY KEY,
    registered_at TIMESTAMP NOT NULL,
    country TEXT NOT NULL,
    acquisition_channel TEXT NOT NULL,
    age INTEGER
);

CREATE TABLE IF NOT EXISTS sessions (
    session_id BIGINT PRIMARY KEY,
    user_id BIGINT NOT NULL REFERENCES users(user_id),
    started_at TIMESTAMP NOT NULL,
    device TEXT NOT NULL,
    traffic_source TEXT NOT NULL,
    duration_seconds INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS events (
    event_id BIGINT PRIMARY KEY,
    session_id BIGINT NOT NULL REFERENCES sessions(session_id),
    user_id BIGINT NOT NULL REFERENCES users(user_id),
    event_at TIMESTAMP NOT NULL,
    event_type TEXT NOT NULL,
    category TEXT
);

CREATE TABLE IF NOT EXISTS orders (
    order_id BIGINT PRIMARY KEY,
    user_id BIGINT NOT NULL REFERENCES users(user_id),
    session_id BIGINT NOT NULL REFERENCES sessions(session_id),
    created_at TIMESTAMP NOT NULL,
    amount NUMERIC(14,2) NOT NULL,
    status TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS payments (
    payment_id BIGINT PRIMARY KEY,
    order_id BIGINT NOT NULL REFERENCES orders(order_id),
    paid_at TIMESTAMP NOT NULL,
    amount NUMERIC(14,2) NOT NULL,
    status TEXT NOT NULL,
    method TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS support_tickets (
    ticket_id BIGINT PRIMARY KEY,
    user_id BIGINT NOT NULL REFERENCES users(user_id),
    created_at TIMESTAMP NOT NULL,
    topic TEXT NOT NULL,
    status TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_sessions_user_time ON sessions(user_id, started_at);
CREATE INDEX IF NOT EXISTS idx_events_user_time ON events(user_id, event_at);
CREATE INDEX IF NOT EXISTS idx_orders_user_time ON orders(user_id, created_at);
CREATE INDEX IF NOT EXISTS idx_tickets_user_time ON support_tickets(user_id, created_at);

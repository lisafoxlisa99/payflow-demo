-- Payflow demo seed data. All values are synthetic; no real customer or
-- payment data is used anywhere in this demo.

CREATE TABLE customers (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    country TEXT NOT NULL
);

INSERT INTO customers (name, country) VALUES
    ('Northwind Traders', 'US'),
    ('Baymark Studio', 'US'),
    ('Kettlewell & Co', 'GB'),
    ('Umber Robotics', 'DE'),
    ('Cascade Analytics', 'US'),
    ('Bluebird Logistics', 'CA'),
    ('Vantage Point Media', 'US'),
    ('Solstice Robotics', 'FR'),
    ('Harborline Freight', 'US'),
    ('Fernwood Analytics', 'AU');

CREATE TABLE transactions (
    id TEXT PRIMARY KEY,
    customer_id INTEGER NOT NULL REFERENCES customers(id),
    amount NUMERIC NOT NULL,
    currency TEXT NOT NULL DEFAULT 'usd',
    status TEXT NOT NULL,
    created_at TIMESTAMP NOT NULL,
    settled_at TIMESTAMP  -- NULL only for the seeded demo-error row, see below
);

INSERT INTO transactions (id, customer_id, amount, status, created_at, settled_at) VALUES
    ('txn_00031', 1, 482.00, 'success', '2026-07-14 09:12:00', '2026-07-14 09:12:04'),
    ('txn_00030', 2, 129.50, 'success', '2026-07-14 08:47:00', '2026-07-14 08:47:03'),
    ('txn_00029', 3, 2140.00, 'success', '2026-07-13 22:10:00', '2026-07-13 22:10:05'),
    ('txn_00028', 4, 87.20, 'pending', '2026-07-13 19:03:00', NULL),
    ('txn_00027', 5, 615.00, 'success', '2026-07-13 15:44:00', '2026-07-13 15:44:02'),
    ('txn_00026', 6, 33.00, 'success', '2026-07-13 11:20:00', '2026-07-13 11:20:06'),
    ('txn_00025', 7, 998.75, 'disputed', '2026-07-12 20:31:00', '2026-07-12 20:31:09'),
    ('txn_00024', 8, 74.40, 'success', '2026-07-12 17:02:00', '2026-07-12 17:02:03'),
    ('txn_00023', 9, 1520.00, 'success', '2026-07-12 13:55:00', '2026-07-12 13:55:04'),
    ('txn_00022', 10, 210.00, 'success', '2026-07-12 09:18:00', '2026-07-12 09:18:02'),
    ('txn_00021', 1, 56.90, 'success', '2026-07-11 21:40:00', '2026-07-11 21:40:03'),
    ('txn_00020', 2, 340.00, 'pending', '2026-07-11 18:12:00', NULL),
    ('txn_00019', 3, 78.30, 'success', '2026-07-11 14:05:00', '2026-07-11 14:05:02'),
    ('txn_00018', 4, 2999.00, 'success', '2026-07-11 10:47:00', '2026-07-11 10:47:07'),
    ('txn_00017', 5, 45.00, 'success', '2026-07-10 23:59:00', '2026-07-10 23:59:03'),
    ('txn_00016', 6, 189.20, 'disputed', '2026-07-10 20:14:00', '2026-07-10 20:14:08'),
    ('txn_00015', 7, 62.10, 'success', '2026-07-10 16:33:00', '2026-07-10 16:33:02'),
    ('txn_00014', 8, 725.00, 'success', '2026-07-10 12:09:00', '2026-07-10 12:09:04'),
    ('txn_00013', 9, 310.50, 'success', '2026-07-09 22:21:00', '2026-07-09 22:21:03'),
    ('txn_00012', 10, 95.00, 'success', '2026-07-09 18:47:00', '2026-07-09 18:47:02'),
    -- Seeded DB-access error: this row has no settled_at, unlike every
    -- other row above. The detail lookup succeeds; the code that computes
    -- settlement duration right after does not (see main.py). Reached by
    -- clicking into this specific transaction from the dashboard table.
    ('txn_demo_investigate', 1, 4820.00, 'pending', '2026-07-09 15:00:00', NULL),
    ('txn_00010', 3, 41.00, 'success', '2026-07-09 11:30:00', '2026-07-09 11:30:02'),
    ('txn_00009', 4, 512.00, 'success', '2026-07-08 21:15:00', '2026-07-08 21:15:03'),
    ('txn_00008', 5, 68.75, 'success', '2026-07-08 17:52:00', '2026-07-08 17:52:02'),
    ('txn_00007', 6, 1230.00, 'success', '2026-07-08 13:40:00', '2026-07-08 13:40:05'),
    ('txn_00006', 7, 29.99, 'success', '2026-07-08 09:22:00', '2026-07-08 09:22:02'),
    ('txn_00005', 8, 815.00, 'pending', '2026-07-07 22:50:00', NULL),
    ('txn_00004', 9, 143.20, 'success', '2026-07-07 18:33:00', '2026-07-07 18:33:03'),
    ('txn_00003', 10, 276.00, 'success', '2026-07-07 14:11:00', '2026-07-07 14:11:02'),
    ('txn_00002', 1, 62.40, 'success', '2026-07-07 10:05:00', '2026-07-07 10:05:02'),
    ('txn_00001', 2, 799.00, 'success', '2026-07-06 21:47:00', '2026-07-06 21:47:04');

-- Dispute archive: backs the "review queue" search on the dashboard.
-- Seeded with 130 rows (well past the 100+ needed to make the N+1 lookup
-- in main.py visibly slow, not just "a bit slow") — see
-- references/observability_scenarios.md.
CREATE TABLE dispute_archive (
    id SERIAL PRIMARY KEY,
    customer_id INTEGER NOT NULL REFERENCES customers(id),
    amount NUMERIC NOT NULL,
    created_at TIMESTAMP NOT NULL
);

INSERT INTO dispute_archive (customer_id, amount, created_at)
SELECT
    ((i % 10) + 1),
    round((50 + (i * 7 % 950))::numeric, 2),
    TIMESTAMP '2026-05-01 00:00:00' + (i || ' hours')::interval
FROM generate_series(1, 130) AS i;

-- Lesson 1: run each query separately.
-- Show 5 customers.
SELECT * FROM users LIMIT 5;

-- How many customers total?
SELECT COUNT(*) AS user_count FROM users;

-- Count sessions for each user, biggest first.
SELECT user_id, COUNT(*) AS session_count
FROM sessions
GROUP BY user_id
ORDER BY session_count DESC
LIMIT 10;

-- How many orders have been successfully completed?
SELECT COUNT(*) AS completed_orders
FROM orders
WHERE status = 'completed';

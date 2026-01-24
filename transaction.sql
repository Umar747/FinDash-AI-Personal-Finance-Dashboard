CREATE TABLE users (
    id BIGSERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL
);

CREATE TABLE accounts (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    account_name VARCHAR(50) NOT NULL,
    UNIQUE(user_id, account_name)
);

CREATE TABLE transactions (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    account_id BIGINT NOT NULL REFERENCES accounts(id) ON DELETE CASCADE,
    transaction_name VARCHAR(100) NOT NULL,
    amount NUMERIC(12,2) NOT NULL,
    transaction_date DATE NOT NULL,
    category VARCHAR(50) NOT NULL
);

CREATE INDEX idx_transactions_user_id ON transactions(user_id);
CREATE INDEX idx_transactions_date ON transactions(transaction_date);
CREATE INDEX idx_transactions_account_id ON transactions(account_id);
CREATE INDEX idx_accounts_user_id ON accounts(user_id);

INSERT INTO users (username) VALUES ('umar'), ('test');
INSERT INTO accounts (user_id, account_name) VALUES (1, 'HSBC Current Account'), (1, 'TSB Credit Account'), (2, 'Nationwide Flex Account');
INSERT INTO transactions (user_id, account_id, transaction_name, amount, transaction_date, category) VALUES (1, 1, 'Transport for London', '-2.90', '2025-12-02', 'Travel'), (1, 1, 'Tesco', '-28.35', '2025-12-11', 'Groceries'), (1, 1, 'HMRC Salary Deposit', '3500', '2025-12-015', 'Income'), (1, 1, 'Express Local Supermarket', '-7.86', '2025-12-17', 'Groceries'), (1, 1, 'The Gym Group', '-28.50', '2025-12-24', 'Bills');
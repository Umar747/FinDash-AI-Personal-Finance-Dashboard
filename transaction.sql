CREATE TABLE users (
    id BIGSERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    password VARCHAR NOT NULL,
    stock text[] NOT NULL,
    balance money NOT NULL,
    days text[] NOT NULL
);

CREATE TABLE value (
    valueid BIGSERIAL PRIMARY KEY,
    value money[] NOT NULL,
    CONSTRAINT value_valueid_fkey FOREIGN KEY(valueid) REFERENCES users(id) ON DELETE CASCADE
);







CREATE TABLE users (
    id BIGSERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
);

CREATE TABLE transactions (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGSERIAL NOT NULL
    transaction_name VARCHAR(100) NOT NULL,
    amount money NOT NULL,
    credit boolean NOT NULL,
    transaction_date date NOT NULL,
    category VARCHAR(50) NOT NULL,
    confidence_score float NOT NULL
);







CREATE TABLE users (
    id BIGSERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create transactions table with proper foreign key
CREATE TABLE transactions (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    transaction_name VARCHAR(100) NOT NULL,
    amount NUMERIC(12,2) NOT NULL, -- Using numeric instead of money
    credit BOOLEAN NOT NULL,
    transaction_date DATE NOT NULL,
    category VARCHAR(50) NOT NULL,
    confidence_score FLOAT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create index for better performance
CREATE INDEX idx_transactions_user_id ON transactions(user_id);
CREATE INDEX idx_transactions_date ON transactions(transaction_date);
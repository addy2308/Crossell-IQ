CREATE TABLE IF NOT EXISTS agents (
    id SERIAL PRIMARY KEY,
    agent_id VARCHAR(100) UNIQUE NOT NULL,
    name VARCHAR(200) NOT NULL,
    email VARCHAR(200) UNIQUE NOT NULL,
    hashed_password VARCHAR(500) NOT NULL,
    region VARCHAR(100),
    role VARCHAR(50) DEFAULT 'agent',
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO agents (agent_id, name, email, hashed_password, role) 
VALUES ('AGT-ADMIN-001', 'Admin Kumar', 'admin@crosselliq.com', 
        '\\\', 'admin')
ON CONFLICT (agent_id) DO NOTHING;

CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(150) UNIQUE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);

INSERT INTO users (name, email) VALUES
    ('Alice Silva', 'alice@example.com'),
    ('Bob Santos', 'bob@example.com'),
    ('Carol Oliveira', 'carol@example.com'),
    ('David Costa', 'david@example.com'),
    ('Eva Souza', 'eva@example.com')
ON CONFLICT (email) DO NOTHING;


CREATE TABLE IF NOT EXISTS access_logs (
    id SERIAL PRIMARY KEY,
    endpoint VARCHAR(255),
    method VARCHAR(10),
    status_code INTEGER,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);


DO $$
DECLARE
    user_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO user_count FROM users;
    RAISE NOTICE '===========================================';
    RAISE NOTICE 'Banco de dados inicializado com sucesso!';
    RAISE NOTICE 'Total de usuários: %', user_count;
    RAISE NOTICE '===========================================';
END $$;


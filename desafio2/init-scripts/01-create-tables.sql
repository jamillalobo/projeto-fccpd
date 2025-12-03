
CREATE TABLE IF NOT EXISTS usuarios (
    id SERIAL PRIMARY KEY,
    nome VARCHAR(100) NOT NULL,
    email VARCHAR(150) UNIQUE NOT NULL,
    data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS produtos (
    id SERIAL PRIMARY KEY,
    nome VARCHAR(200) NOT NULL,
    descricao TEXT,
    preco DECIMAL(10, 2) NOT NULL,
    estoque INTEGER DEFAULT 0,
    data_cadastro TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO usuarios (nome, email) VALUES
    ('João Silva', 'joao@example.com'),
    ('Maria Santos', 'maria@example.com'),
    ('Pedro Oliveira', 'pedro@example.com');

INSERT INTO produtos (nome, descricao, preco, estoque) VALUES
    ('Notebook Dell', 'Notebook Dell Inspiron 15, 8GB RAM, 256GB SSD', 3499.90, 10),
    ('Mouse Logitech', 'Mouse sem fio Logitech MX Master 3', 449.90, 25),
    ('Teclado Mecânico', 'Teclado mecânico RGB, switches blue', 599.90, 15),

CREATE INDEX idx_usuarios_email ON usuarios(email);
CREATE INDEX idx_produtos_nome ON produtos(nome);

DO $$
BEGIN
    RAISE NOTICE 'Banco de dados inicializado com sucesso!';
END $$;


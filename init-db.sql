-- Banco de dados segregado para o serviço de vendas
-- Este banco armazena apenas dados relacionados a vendas e cache de veículos

-- Tabela de cache de veículos (sincronizada do serviço principal)
CREATE TABLE IF NOT EXISTS vehicles (
    id SERIAL PRIMARY KEY,
    external_id INTEGER UNIQUE NOT NULL,
    marca VARCHAR(100) NOT NULL,
    modelo VARCHAR(100) NOT NULL,
    ano INTEGER NOT NULL,
    cor VARCHAR(50) NOT NULL,
    preco DECIMAL(12, 2) NOT NULL,
    status VARCHAR(20) DEFAULT 'DISPONIVEL',
    data_cadastro TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tabela de vendas
CREATE TABLE IF NOT EXISTS sales (
    id SERIAL PRIMARY KEY,
    vehicle_id INTEGER NOT NULL REFERENCES vehicles(id),
    cpf_comprador VARCHAR(14) NOT NULL,
    codigo_pagamento UUID NOT NULL UNIQUE,
    status_pagamento VARCHAR(20) DEFAULT 'PENDENTE',
    data_venda TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    valor_venda DECIMAL(12, 2) NOT NULL
);

-- Índices para otimização
CREATE INDEX IF NOT EXISTS idx_vehicles_status ON vehicles(status);
CREATE INDEX IF NOT EXISTS idx_vehicles_preco ON vehicles(preco);
CREATE INDEX IF NOT EXISTS idx_sales_codigo_pagamento ON sales(codigo_pagamento);
CREATE INDEX IF NOT EXISTS idx_sales_status_pagamento ON sales(status_pagamento);

# Vehicle Sales API

Serviço de vendas de veículos - Tech Challenge Fase 4 (FIAP/SOAT)

## Descrição

Este é o **serviço de vendas**, responsável por:

- ✅ Listagem de veículos disponíveis (ordenados por preço, do mais barato para o mais caro)
- ✅ Listagem de veículos vendidos (ordenados por preço, do mais barato para o mais caro)
- ✅ Efetuar a venda de um veículo (com CPF do comprador e data da venda)
- ✅ Webhook para confirmação/cancelamento de pagamento

## Arquitetura

Este serviço opera de forma **isolada** com seu próprio banco de dados PostgreSQL (`vehicle_sales`), conforme requisito do Tech Challenge.

A comunicação com o **serviço principal de veículos** é feita via **requisições HTTP síncronas**.

```
┌─────────────────────┐         HTTP          ┌──────────────────────┐
│  Vehicle Sales API  │ ◄──────────────────►  │  Vehicle Management  │
│    (porta 8001)     │                       │    API (porta 8000)  │
└─────────┬───────────┘                       └──────────┬───────────┘
          │                                              │
          │                                              │
          ▼                                              ▼
┌─────────────────────┐                       ┌──────────────────────┐
│   PostgreSQL        │                       │   PostgreSQL         │
│   vehicle_sales     │                       │   tech_challenge     │
│   (porta 5433)      │                       │   (porta 5432)       │
└─────────────────────┘                       └──────────────────────┘
```

## Stack Tecnológica

- **Linguagem:** Python 3.12
- **Framework:** FastAPI
- **Banco de Dados:** PostgreSQL (isolado)
- **ORM:** SQLAlchemy (Async)
- **Comunicação:** HTTP via httpx
- **Gerenciamento de Dependências:** Poetry
- **Infraestrutura:** Docker & Docker Compose
- **CI/CD:** GitHub Actions

## Como Rodar Localmente

### Pré-requisitos

- Docker e Docker Compose instalados
- O serviço principal (`vehicle-management-api`) deve estar rodando na porta 8000

### Com Docker Compose

1. Crie a rede compartilhada (se ainda não existir):
   ```bash
   docker network create vehicle-network
   ```

2. Construa e inicie o serviço:
   ```bash
   docker-compose up --build
   ```

3. A API estará disponível em: `http://localhost:8001`
4. Documentação Swagger: `http://localhost:8001/docs`

### Desenvolvimento Local (sem Docker)

1. Instale o Poetry:
   ```bash
   pip install poetry
   ```

2. Instale as dependências:
   ```bash
   poetry install
   ```

3. Execute a aplicação:
   ```bash
   poetry run uvicorn app.main:app --reload --port 8001
   ```

## Endpoints

### Veículos

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| GET | `/api/v1/vehicles/available` | Lista veículos disponíveis (ordenados por preço) |
| GET | `/api/v1/vehicles/sold` | Lista veículos vendidos (ordenados por preço) |

### Vendas

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| POST | `/api/v1/sales/` | Efetua a venda de um veículo |
| GET | `/api/v1/sales/` | Lista todas as vendas |
| GET | `/api/v1/sales/{codigo_pagamento}` | Busca venda pelo código |

### Webhook

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| POST | `/webhook/pagamento` | Confirma ou cancela pagamento |

## Exemplos de Uso

### Efetuar Venda

```bash
curl -X POST http://localhost:8001/api/v1/sales/ \
  -H "Content-Type: application/json" \
  -d '{
    "vehicle_id": 1,
    "cpf_comprador": "52998224725"
  }'
```

**Resposta:**
```json
{
  "id": 1,
  "vehicle_id": 1,
  "cpf_comprador": "529.982.247-25",
  "codigo_pagamento": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "status_pagamento": "PENDENTE",
  "data_venda": "2024-01-15T10:30:00",
  "valor_venda": 95000.00
}
```

### Confirmar Pagamento (Webhook)

```bash
curl -X POST http://localhost:8001/webhook/pagamento \
  -H "Content-Type: application/json" \
  -d '{
    "codigo_pagamento": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
    "status": "CONFIRMADO"
  }'
```

### Cancelar Pagamento (Webhook)

```bash
curl -X POST http://localhost:8001/webhook/pagamento \
  -H "Content-Type: application/json" \
  -d '{
    "codigo_pagamento": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
    "status": "CANCELADO"
  }'
```

## Testes

### Executar Testes

```bash
poetry run pytest tests/ -v
```

### Executar Testes com Cobertura

```bash
poetry run pytest tests/ -v --cov=app --cov-report=html --cov-report=term
```

O relatório de cobertura HTML será gerado em `htmlcov/index.html`.

### Requisito de Cobertura

O CI/CD está configurado para **falhar se a cobertura for menor que 80%**.

## CI/CD

O pipeline de CI/CD (GitHub Actions) executa:

1. **Lint & Test**: Executa testes com validação de cobertura mínima de 80%
2. **Build Docker**: Constrói a imagem Docker
3. **Security Scan**: Analisa vulnerabilidades com Trivy
4. **Deploy**: Simula deploy na AWS (ECS) em merges para `main`

### Gatilho de Deploy

O deploy é executado automaticamente em **merges para a branch `main`** (via Pull Request).

## Variáveis de Ambiente

| Variável | Descrição | Padrão |
|----------|-----------|--------|
| `DATABASE_URL` | URL do banco PostgreSQL | `sqlite+aiosqlite:///./sales.db` |
| `VEHICLE_SERVICE_URL` | URL do serviço principal | `http://localhost:8000` |
| `SECRET_KEY` | Chave secreta da aplicação | `development-secret-key` |

## Estrutura do Projeto

```
vehicle-sales-api/
├── app/
│   ├── core/
│   │   └── config.py          # Configurações
│   ├── models/
│   │   └── models.py          # Vehicle, Sale, PaymentStatus
│   ├── routers/
│   │   ├── vehicles.py        # Listagens
│   │   ├── sales.py           # Vendas
│   │   └── webhook.py         # Webhook pagamento
│   ├── schemas/
│   │   └── schemas.py         # Validação CPF, DTOs
│   ├── services/
│   │   ├── sale_service.py    # Lógica de negócio
│   │   └── vehicle_client.py  # Cliente HTTP
│   ├── database.py
│   └── main.py
├── tests/
│   ├── conftest.py
│   ├── test_main.py
│   ├── test_sales.py
│   ├── test_webhook.py
│   ├── test_vehicles.py
│   └── test_schemas.py
├── .github/workflows/ci.yml
├── docker-compose.yml
├── Dockerfile
├── pyproject.toml
└── README.md
```

## Licença

MIT

# Desafio 4

## Descrição

Este desafio demonstra a arquitetura de microsserviços com comunicação direta via HTTP, sem uso de API Gateway:
- **Microsserviço A**: Fornece lista de usuários em formato JSON
- **Microsserviço B**: Consome dados do Microsserviço A e exibe informações combinadas e formatadas

Ambos os serviços possuem Dockerfiles independentes e se comunicam através da rede Docker interna.

##  Componentes

### Microsserviço A - Users API

**Responsabilidade**: Fornecedor de dados de usuários

**Tecnologia**: Flask (Python)

**Endpoints**:
- `GET /` - Informações do serviço
- `GET /health` - Health check
- `GET /users` - Lista todos os usuários
- `GET /users/<id>` - Obtém usuário específico
- `GET /users/status/<status>` - Filtra por status
- `GET /stats` - Estatísticas de usuários

**Dockerfile**: `service-a/Dockerfile`

### Microsserviço B - User Info Aggregator

**Responsabilidade**: Consumidor que agrega e formata dados

**Tecnologia**: Flask (Python) + Requests

**Endpoints**:
- `GET /` - Informações do serviço
- `GET /health` - Health check (inclui status do Service A)
- `GET /user-info` - Usuários com informações formatadas
- `GET /user-info/<id>` - Info formatada de usuário específico
- `GET /active-users` - Apenas usuários ativos
- `GET /summary` - Resumo executivo

**Dockerfile**: `service-b/Dockerfile`

**Formato das mensagens**:
```
"Usuário Alice Silva (👑 admin) está active desde 1 ano, 10 meses atrás"
"Usuário Daniel Costa (👤 user) está inactive desde 1 ano, 1 mês atrás"
```

## Como Executar

### 1. Construir e iniciar os microsserviços

```bash
cd desafio4
docker-compose up -d --build
```

### 2. Verificar que os containers estão rodando

```bash
docker-compose ps
```

Saída esperada:
```
NAME                  IMAGE              STATUS    PORTS
desafio4-service-a    desafio4-service-a Up        0.0.0.0:5001->5001/tcp
desafio4-service-b    desafio4-service-b Up        0.0.0.0:5002->5002/tcp
```

### 3. Ver logs dos serviços

```bash
# Logs de ambos os serviços
docker-compose logs -f

# Logs do Service A
docker-compose logs -f service-a

# Logs do Service B
docker-compose logs -f service-b
```

## Demonstração da Comunicação

### Método 1: Script Automatizado (Recomendado)

Execute o script de teste completo:

```bash
chmod +x test-microservices.sh
./test-microservices.sh
```


### Método 2: Testes Manuais

#### Teste 1: Buscar usuários do Service A

```bash
# Listar todos os usuários
curl http://localhost:5001/users | python3 -m json.tool

# Buscar usuário específico
curl http://localhost:5001/users/1 | python3 -m json.tool
```

Resposta do Service A (dados brutos):
```json
{
  "service": "Service-A (Users API)",
  "user": {
    "id": 1,
    "name": "Alice Silva",
    "email": "alice.silva@example.com",
    "status": "active",
    "role": "admin",
    "registration_date": "2023-01-15"
  }
}
```

#### Teste 2: Buscar informações formatadas do Service B

```bash
# Informações de todos os usuários formatadas
curl http://localhost:5002/user-info | python3 -m json.tool

# Informação de usuário específico formatada
curl http://localhost:5002/user-info/1 | python3 -m json.tool
```

Resposta do Service B (dados agregados e formatados):
```json
{
  "service": "Service-B (User Info Aggregator)",
  "source": "Service A",
  "user": {
    "id": 1,
    "name": "Alice Silva",
    "email": "alice.silva@example.com",
    "status": "active",
    "role": "admin",
    "registration_date": "2023-01-15",
    "time_since_registration": "1 ano, 10 meses",
    "formatted_message": "✅ Usuário Alice Silva (👑 admin) está active desde 1 ano, 10 meses atrás"
  }
}
```

#### Teste 3: Apenas usuários ativos

```bash
curl http://localhost:5002/active-users | python3 -m json.tool
```

#### Teste 4: Resumo executivo

```bash
curl http://localhost:5002/summary | python3 -m json.tool
```

#### Teste 5: Comunicação direta entre containers

```bash
# Do container Service B, fazer requisição ao Service A
docker exec desafio4-service-b curl -s http://service-a:5001/users | python3 -m json.tool
```

**Demonstração**: Service B consegue acessar Service A usando apenas o nome do serviço!

## Demonstração de Comunicação HTTP

### Fluxo de Requisição

```
Cliente
  │
  │ GET /user-info/1
  ▼
┌──────────────────┐
│   Service B      │ 1. Recebe requisição
│  (Porta 5002)    │ 2. Precisa de dados do usuário
└────────┬─────────┘
         │
         │ HTTP GET http://service-a:5001/users/1
         ▼
┌──────────────────┐
│   Service A      │ 3. Retorna dados do usuário (JSON)
│  (Porta 5001)    │
└────────┬─────────┘
         │
         │ Response: {"user": {...}}
         ▼
┌──────────────────┐
│   Service B      │ 4. Processa dados
│                  │ 5. Calcula tempo desde registro
└────────┬─────────┘ 6. Formata mensagem
         │
         │ Response: {"formatted_message": "..."}
         ▼
      Cliente
```

### Ver Logs de Comunicação

```bash
# Terminal 1: Monitorar Service A (recebe requisições)
docker logs -f desafio4-service-a

# Terminal 2: Monitorar Service B (faz requisições)
docker logs -f desafio4-service-b

# Terminal 3: Fazer requisições
curl http://localhost:5002/user-info/2
```

Você verá:
- **Service A logs**: `GET /users/2` (requisição recebida do Service B)
- **Service B logs**: Requisição para `http://service-a:5001/users/2`

## Estrutura do Projeto

```
desafio4/
├── docker-compose.yml           # Orquestração dos microsserviços
├── service-a/
│   ├── Dockerfile              # Build independente do Service A
│   ├── requirements.txt        # Dependências: Flask
│   └── app.py                  # API de usuários
├── service-b/
│   ├── Dockerfile              # Build independente do Service B
│   ├── requirements.txt        # Dependências: Flask + Requests
│   └── app.py                  # Agregador de informações
├── test-microservices.sh        # Script de teste automatizado
└── README.md                   # Esta documentação
```

## Configuração via Variáveis de Ambiente

### Service A

```yaml
environment:
  - SERVICE_NAME=Service-A (Users API)
  - SERVICE_PORT=5001
```

### Service B

```yaml
environment:
  - SERVICE_NAME=Service-B (User Info Aggregator)
  - SERVICE_PORT=5002
  - SERVICE_A_URL=http://service-a:5001  # ← Comunicação via DNS interno
```

**Importante**: `SERVICE_A_URL` usa o nome do serviço (`service-a`) definido no docker-compose, não um IP!


## Endpoints Disponíveis

### Service A (porta 5001)

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| GET | `/` | Informações do serviço |
| GET | `/health` | Health check |
| GET | `/users` | Lista todos os usuários |
| GET | `/users/<id>` | Obtém usuário específico |
| GET | `/users/status/<status>` | Filtra por status (active, inactive, suspended) |
| GET | `/stats` | Estatísticas de usuários |

### Service B (porta 5002)

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| GET | `/` | Informações do serviço |
| GET | `/health` | Health check (verifica Service A também) |
| GET | `/user-info` | Lista usuários com info formatada |
| GET | `/user-info/<id>` | Info formatada de usuário específico |
| GET | `/active-users` | Apenas usuários ativos |
| GET | `/summary` | Resumo executivo |

## Testes e Validações

### Teste 1: Health checks

```bash
# Service A
curl http://localhost:5001/health

# Service B (também verifica Service A)
curl http://localhost:5002/health
```

### Teste 2: Comparar dados

```bash
# Dados brutos do Service A
curl http://localhost:5001/users/3

# Dados processados do Service B
curl http://localhost:5002/user-info/3
```

### Teste 3: Resolução DNS

```bash
# Service B pode resolver 'service-a'
docker exec desafio4-service-b ping -c 2 service-a
```

### Teste 4: Comunicação HTTP funciona

```bash
# Fazer requisição do Service B para o Service A
docker exec desafio4-service-b curl http://service-a:5001/health
```

### Teste 5: Consistência de dados

```bash
# Contar usuários em ambos os serviços
USERS_A=$(curl -s http://localhost:5001/users | python3 -c "import sys,json; print(json.load(sys.stdin)['total_users'])")
USERS_B=$(curl -s http://localhost:5002/user-info | python3 -c "import sys,json; print(json.load(sys.stdin)['total_users'])")

echo "Service A: $USERS_A usuários"
echo "Service B: $USERS_B usuários"
```

## Conceitos Demonstrados

### 1. Microsserviços Independentes
- Cada serviço tem seu próprio Dockerfile
- Responsabilidades bem definidas
- Podem ser desenvolvidos e deployados independentemente

### 2. Service Discovery
- Resolução DNS via rede Docker
- Comunicação usando nomes de serviços
- Não precisa de IPs hardcoded

### 3. HTTP como Protocolo de Comunicação
- RESTful APIs
- JSON como formato de dados
- Stateless (sem estado compartilhado)

### 4. Separação de Responsabilidades
- **Service A**: Provider (fornecedor de dados)
- **Service B**: Consumer/Aggregator (consumidor/agregador)

### 5. Agregação de Dados
- Service B enriquece os dados do Service A
- Adiciona lógica de negócio (cálculo de tempo)
- Formata para apresentação

## Troubleshooting

### Problema: Service B não consegue conectar ao Service A

**Verificar**:
```bash
# 1. Verificar que Service A está rodando
docker ps | grep service-a

# 2. Verificar health do Service A
curl http://localhost:5001/health

# 3. Testar do container do Service B
docker exec desafio4-service-b curl http://service-a:5001/health
```

### Problema: "Connection refused"

**Causa**: Service A ainda está iniciando

**Solução**: Aguardar o health check passar:
```bash
docker-compose logs service-a | grep "Running on"
```

### Problema: Portas já em uso

**Solução**: Alterar portas no `docker-compose.yml`:
```yaml
ports:
  - "5003:5001"  # Service A na porta 5003 externamente
  - "5004:5002"  # Service B na porta 5004 externamente
```

### Problema: Dados inconsistentes

**Solução**: Rebuild dos containers:
```bash
docker-compose down
docker-compose up -d --build
```



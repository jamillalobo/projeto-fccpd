# Desafio 5

## Descrição

Este desafio demonstra o **padrão API Gateway** (Gateway Pattern), centralizando o acesso a múltiplos microsserviços:
- **Gateway**: Ponto único de entrada que roteia requisições
- **Users Service**: Microsserviço que fornece dados de usuários
- **Orders Service**: Microsserviço que fornece dados de pedidos

Todos os serviços rodam em containers Docker e se comunicam através de uma rede interna.

## Componentes

### 1. API Gateway (porta 8000)

**Responsabilidade**: Ponto único de entrada e roteamento

**Funcionalidades**:
- Roteia `/users/*` para Users Service
- Roteia `/orders/*` para Orders Service
- Health check agregado de todos os serviços
- Estatísticas de requisições
- Tratamento de erros centralizado

**Dockerfile**: `gateway/Dockerfile`

### 2. Users Service (porta 5001 - interna)

**Responsabilidade**: Gerenciamento de usuários

**Endpoints**:
- `GET /users` - Lista todos os usuários
- `POST /users` - Cria novo usuário
- `GET /users/<id>` - Obtém usuário específico
- `PUT /users/<id>` - Atualiza usuário
- `DELETE /users/<id>` - Remove usuário
- `GET /users/search/<query>` - Busca usuários

**Dockerfile**: `users-service/Dockerfile`

**Importante**: Não expõe porta externamente, apenas via Gateway!

### 3. Orders Service (porta 5002 - interna)

**Responsabilidade**: Gerenciamento de pedidos

**Endpoints**:
- `GET /orders` - Lista todos os pedidos
- `POST /orders` - Cria novo pedido
- `GET /orders/<id>` - Obtém pedido específico
- `PUT /orders/<id>` - Atualiza pedido
- `DELETE /orders/<id>` - Remove pedido
- `GET /orders/user/<user_id>` - Pedidos de um usuário
- `GET /orders/status/<status>` - Filtra por status

**Dockerfile**: `orders-service/Dockerfile`

**Dependência**: Consome Users Service para enriquecer dados dos pedidos

**Importante**: Não expõe porta externamente, apenas via Gateway!

## Como Executar

### 1. Construir e iniciar todos os serviços

```bash
cd desafio5
docker-compose up -d --build
```

### 2. Verificar que todos os containers estão rodando

```bash
docker-compose ps
```

Saída esperada:
```
NAME                       IMAGE                      STATUS    PORTS
desafio5-gateway           desafio5-gateway           Up        0.0.0.0:8000->8000/tcp
desafio5-users-service     desafio5-users-service     Up        
desafio5-orders-service    desafio5-orders-service    Up        
```

**Observar**: Apenas o Gateway expõe porta externamente!

### 3. Ver logs

```bash
# Todos os logs
docker-compose logs -f

# Logs específicos
docker-compose logs -f gateway
docker-compose logs -f users-service
docker-compose logs -f orders-service
```

## Usando a API

### Acesso via Gateway (porta 8000)

**IMPORTANTE**: Todas as requisições devem passar pelo Gateway!

#### Endpoint Raiz

```bash
curl http://localhost:8000/
```

#### Health Check Agregado

```bash
curl http://localhost:8000/health | python3 -m json.tool
```

Resposta:
```json
{
  "gateway": "healthy",
  "users_service": "healthy",
  "orders_service": "healthy",
  "overall": "healthy",
  "timestamp": "2025-12-03T10:00:00"
}
```

### Operações com Usuários (via Gateway)

#### Listar usuários

```bash
curl http://localhost:8000/users | python3 -m json.tool
```

#### Buscar usuário específico

```bash
curl http://localhost:8000/users/1 | python3 -m json.tool
```

#### Criar novo usuário

```bash
curl -X POST http://localhost:8000/users \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Novo Usuário",
    "email": "novo@example.com",
    "role": "customer"
  }' | python3 -m json.tool
```

#### Atualizar usuário

```bash
curl -X PUT http://localhost:8000/users/1 \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Nome Atualizado"
  }' | python3 -m json.tool
```

#### Buscar usuários

```bash
curl http://localhost:8000/users/search/ana | python3 -m json.tool
```

### Operações com Pedidos (via Gateway)

#### Listar pedidos

```bash
curl http://localhost:8000/orders | python3 -m json.tool
```

**Observação**: Os pedidos vêm enriquecidos com informações dos usuários!

#### Buscar pedido específico

```bash
curl http://localhost:8000/orders/1 | python3 -m json.tool
```

#### Criar novo pedido

```bash
curl -X POST http://localhost:8000/orders \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": 2,
    "items": ["Produto A", "Produto B"],
    "total": 299.90
  }' | python3 -m json.tool
```

#### Pedidos de um usuário específico

```bash
curl http://localhost:8000/orders/user/2 | python3 -m json.tool
```

Resposta (exemplo):
```json
{
  "service": "Orders Service",
  "user_id": 2,
  "user_name": "Bruno Costa",
  "total_orders": 2,
  "total_value": 4249.70,
  "orders": [...]
}
```

#### Filtrar pedidos por status

```bash
curl http://localhost:8000/orders/status/delivered | python3 -m json.tool
```

### Estatísticas do Gateway

```bash
curl http://localhost:8000/stats | python3 -m json.tool
```

Resposta:
```json
{
  "gateway": "API Gateway",
  "request_statistics": {
    "total": 45,
    "users": 20,
    "orders": 23,
    "errors": 2
  },
  "timestamp": "2025-12-03T10:30:00"
}
```

## Demonstração Completa

### Método 1: Script Automatizado (Recomendado)

Execute o script de teste completo:

```bash
chmod +x test-gateway.sh
./test-gateway.sh
```

### Método 2: Teste Manual do Fluxo Completo

#### Cenário: Buscar pedidos de um usuário

```
Cliente
  │
  │ GET /orders/user/2
  ▼
┌──────────────┐
│   Gateway    │ 1. Recebe requisição
│              │ 2. Roteia para Orders Service
└──────┬───────┘
       │
       │ GET http://orders-service:5002/orders/user/2
       ▼
┌──────────────────┐
│ Orders Service   │ 3. Busca pedidos do user_id 2
│                  │ 4. Precisa info do usuário
└──────┬───────────┘
       │
       │ GET http://users-service:5001/users/2
       ▼
┌──────────────────┐
│ Users Service    │ 5. Retorna dados do usuário
└──────┬───────────┘
       │
       │ Response: {"name": "Bruno Costa", ...}
       ▼
┌──────────────────┐
│ Orders Service   │ 6. Enriquece pedidos com dados do usuário
└──────┬───────────┘ 7. Retorna para Gateway
       │
       │ Response: {"orders": [...], "user_name": "Bruno Costa"}
       ▼
┌──────────────┐
│   Gateway    │ 8. Retorna ao Cliente
└──────┬───────┘
       │
       ▼
    Cliente
```

**Executar**:

```bash
curl http://localhost:8000/orders/user/2 | python3 -m json.tool
```

**Observar**: O resultado inclui `user_name` e `user_email`, demonstrando que o Orders Service consultou o Users Service!

## 🔍 Verificações Importantes

### 1. Microsserviços não são acessíveis externamente

```bash
# Tentar acessar Users Service diretamente (deve falhar)
curl http://localhost:5001/users

# Tentar acessar Orders Service diretamente (deve falhar)
curl http://localhost:5002/orders
```

**Esperado**: Connection refused (serviços não expõem portas externamente)

### 2. Comunicação interna funciona

```bash
# Do container Orders, acessar Users
docker exec desafio5-orders-service curl http://users-service:5001/health
```

**Esperado**: Resposta de sucesso

### 3. Gateway está roteando corretamente

```bash
# Ver logs do Gateway
docker logs desafio5-gateway | grep -E "users|orders"
```

Você verá entradas como:
- `GET /users` → roteado para `http://users-service:5001/users`
- `GET /orders` → roteado para `http://orders-service:5002/orders`

### 4. Rede Docker

```bash
docker network inspect desafio5-network
```

Todos os 3 serviços devem estar na mesma rede.

## Estrutura do Projeto

```
desafio5/
├── docker-compose.yml           # Orquestração de 3 serviços
├── gateway/
│   ├── Dockerfile              # Build do Gateway
│   ├── requirements.txt        # Flask + Requests
│   └── app.py                  # Lógica de roteamento
├── users-service/
│   ├── Dockerfile              # Build do Users Service
│   ├── requirements.txt        # Flask
│   └── app.py                  # API de usuários
├── orders-service/
│   ├── Dockerfile              # Build do Orders Service
│   ├── requirements.txt        # Flask + Requests
│   └── app.py                  # API de pedidos
├── test-gateway.sh              # Script de teste automatizado
└── README.md                   # Esta documentação
```

## Benefícios do API Gateway

### 1. Ponto Único de Entrada (Single Entry Point)
- Cliente precisa conhecer apenas o endereço do Gateway
- Simplifica configuração de clientes
- Facilita mudanças de infraestrutura

### 2. Roteamento Centralizado
- Lógica de roteamento em um único lugar
- Fácil adicionar/remover/modificar rotas
- Versionamento de API simplificado

### 3. Isolamento de Microsserviços
- Serviços backend não ficam expostos
- Maior segurança
- Controle de acesso centralizado

### 4. Orquestração de Chamadas
- Gateway pode agregar múltiplos serviços
- Pode fazer transformações de dados
- Pode implementar caching

### 5. Cross-Cutting Concerns
- Autenticação/Autorização centralizada
- Rate limiting
- Logging e monitoramento
- CORS handling
- Retry e circuit breaker

### 6. Flexibilidade
- Serviços podem ser atualizados independentemente
- Gateway pode fazer A/B testing
- Facilita migração gradual de serviços

## Testes e Validações

### Teste 1: Gateway está roteando

```bash
# Fazer requisição via Gateway
curl http://localhost:8000/users

# Ver logs para confirmar roteamento
docker logs desafio5-gateway --tail 5
```

### Teste 2: Enriquecimento de dados

```bash
# Orders Service enriquece pedidos com dados de usuários
curl http://localhost:8000/orders | python3 -c "
import sys, json
data = json.load(sys.stdin)
for order in data['orders']:
    if 'user_name' in order:
        print(f\"✓ Order {order['id']} enriquecido com user: {order['user_name']}\")
"
```

### Teste 3: Health check agregado

```bash
curl http://localhost:8000/health
```

Deve retornar status de todos os serviços.

### Teste 4: Estatísticas

```bash
# Fazer várias requisições
for i in {1..10}; do
  curl -s http://localhost:8000/users > /dev/null
  curl -s http://localhost:8000/orders > /dev/null
done

# Ver estatísticas
curl http://localhost:8000/stats | python3 -m json.tool
```

### Teste 5: CRUD completo via Gateway

```bash
# Criar
USER_ID=$(curl -s -X POST http://localhost:8000/users \
  -H "Content-Type: application/json" \
  -d '{"name":"Test","email":"test@x.com"}' | \
  python3 -c "import sys,json; print(json.load(sys.stdin)['user']['id'])")

# Ler
curl http://localhost:8000/users/$USER_ID

# Atualizar
curl -X PUT http://localhost:8000/users/$USER_ID \
  -H "Content-Type: application/json" \
  -d '{"name":"Test Updated"}'

# Deletar
curl -X DELETE http://localhost:8000/users/$USER_ID
```

## Troubleshooting

### Problema: Gateway não consegue conectar aos serviços

**Verificar**:
```bash
# 1. Serviços estão rodando?
docker-compose ps

# 2. Health checks estão passando?
docker exec desafio5-users-service curl http://localhost:5001/health
docker exec desafio5-orders-service curl http://localhost:5002/health

# 3. Rede está OK?
docker network inspect desafio5-network
```

### Problema: "Service Unavailable" no Gateway

**Causa**: Microsserviço não está respondendo

**Solução**:
```bash
# Ver logs do serviço com problema
docker-compose logs users-service
docker-compose logs orders-service

# Reiniciar serviço específico
docker-compose restart users-service
```

### Problema: Dados não são enriquecidos

**Causa**: Orders Service não consegue acessar Users Service

**Solução**:
```bash
# Testar comunicação
docker exec desafio5-orders-service curl http://users-service:5001/health

# Ver logs
docker-compose logs orders-service | grep users-service
```

### Problema: Porta 8000 já em uso

**Solução**: Alterar porta do Gateway no `docker-compose.yml`:
```yaml
gateway:
  ports:
    - "8001:8000"  # Usar porta 8001 externamente
```
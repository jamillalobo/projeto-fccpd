# Desafio 3

## Descrição

Este desafio demonstra uma aplicação completa com 3 serviços integrados:
- **Web**: API Flask com endpoints REST
- **Database (db)**: PostgreSQL para armazenamento persistente
- **Cache**: Redis para cache de dados e estatísticas

A aplicação demonstra comunicação entre serviços, uso de variáveis de ambiente, dependências (`depends_on`), health checks e rede interna.

## Como Executar

### 1. Iniciar todos os serviços

```bash
cd desafio3
docker-compose up -d --build
```

Isso irá:
- ✅ Construir a imagem do serviço web
- ✅ Baixar imagens do PostgreSQL e Redis
- ✅ Criar a rede `desafio3-network`
- ✅ Criar volumes para persistência
- ✅ Iniciar os serviços respeitando as dependências

### 2. Verificar que todos os containers estão rodando

```bash
docker-compose ps
```

Saída esperada:
```
NAME                IMAGE                 STATUS    PORTS
desafio3-cache      redis:7-alpine        Up        0.0.0.0:6379->6379/tcp
desafio3-db         postgres:15-alpine    Up        0.0.0.0:5433->5432/tcp
desafio3-web        desafio3-web          Up        0.0.0.0:5000->5000/tcp
```

### 3. Ver logs dos serviços

```bash
# Todos os logs
docker-compose logs

# Logs de um serviço específico
docker-compose logs web
docker-compose logs db
docker-compose logs cache

# Follow mode (tempo real)
docker-compose logs -f web
```

## Demonstração da Comunicação

### Método 1: Script Automatizado (Recomendado)

Execute o script de teste que demonstra toda a comunicação:

```bash
chmod +x test-communication.sh
./test-communication.sh
```

### Método 2: Testes Manuais via API

#### Teste 1: Verificar que a API está rodando

```bash
curl http://localhost:5000/
```

#### Teste 2: Health Check (verifica comunicação com DB e Cache)

```bash
curl http://localhost:5000/health | python3 -m json.tool
```

Resposta esperada:
```json
{
  "web": "healthy",
  "database": "healthy",
  "cache": "healthy",
  "timestamp": "2025-12-02T10:30:00",
  "total_health_checks": "1"
}
```

#### Teste 3: Listar usuários (primeira vez busca do DB)

```bash
curl http://localhost:5000/users | python3 -m json.tool
```

Resposta:
```json
{
  "source": "database",
  "users": [
    {
      "id": 1,
      "name": "Alice Silva",
      "email": "alice@example.com",
      "created_at": "2025-12-02T10:00:00"
    },
    ...
  ]
}
```

#### Teste 4: Listar usuários novamente (vem do Cache)

```bash
curl http://localhost:5000/users | python3 -m json.tool
```

Resposta:
```json
{
  "source": "cache",
  "users": [...],
  "cached_at": "2025-12-02T10:30:00"
}
```

**Demonstração de Cache**: A segunda requisição é mais rápida pois vem do Redis!

#### Teste 5: Criar novo usuário

```bash
curl -X POST http://localhost:5000/users \
  -H "Content-Type: application/json" \
  -d '{"name": "João Teste", "email": "joao@test.com"}' | python3 -m json.tool
```

#### Teste 6: Buscar usuário específico

```bash
curl http://localhost:5000/users/1 | python3 -m json.tool
```

#### Teste 7: Ver estatísticas

```bash
curl http://localhost:5000/stats | python3 -m json.tool
```

Resposta:
```json
{
  "health_checks": "5",
  "cache_hits": "10",
  "cache_misses": "3",
  "users_created": "2",
  "cache_hit_rate": "76.92%",
  "timestamp": "2025-12-02T10:35:00"
}
```

#### Teste 8: Testar cache diretamente

```bash
curl http://localhost:5000/cache/test | python3 -m json.tool
```

### Método 3: Comunicação Direta Entre Containers

#### Teste Web → Database

```bash
# Executar query SQL do container web
docker exec desafio3-web psql $DATABASE_URL -c "SELECT COUNT(*) FROM users;"
```

#### Teste Web → Cache

```bash
# Executar comando Redis do container web
docker exec desafio3-web redis-cli -h cache PING
```

Resposta esperada: `PONG`

#### Teste de resolução DNS

```bash
# Do container web, resolver o nome 'db'
docker exec desafio3-web ping -c 2 db

# Do container web, resolver o nome 'cache'
docker exec desafio3-web ping -c 2 cache
```

## Configurações e Variáveis de Ambiente

### Serviço Web (Flask)

```yaml
environment:
  - FLASK_ENV=development
  - FLASK_APP=app.py
  - DATABASE_URL=postgresql://postgres:postgres123@db:5432/app_db
  - REDIS_HOST=cache
  - REDIS_PORT=6379
  - API_SECRET_KEY=chave_secreta_super_segura_123
```

**Observações**:
- `DATABASE_URL`: Usa o nome do serviço `db` para resolução DNS
- `REDIS_HOST`: Usa o nome do serviço `cache` para resolução DNS
- Todas as configs são injetadas via variáveis de ambiente

### Serviço Database (PostgreSQL)

```yaml
environment:
  - POSTGRES_USER=postgres
  - POSTGRES_PASSWORD=postgres123
  - POSTGRES_DB=app_db
```

### Serviço Cache (Redis)

```yaml
command: redis-server --appendonly yes --appendfsync everysec
```

**Persistência habilitada**: AOF (Append Only File) com sync a cada segundo

## Dependências (depends_on)

```yaml
web:
  depends_on:
    db:
      condition: service_healthy
    cache:
      condition: service_healthy
```

**Como funciona**:
1. Docker Compose inicia `db` e `cache` primeiro
2. Aguarda até que os health checks retornem sucesso
3. Só então inicia o serviço `web`
4. Garante que a aplicação não tente conectar a serviços indisponíveis

### Health Checks

#### Database (PostgreSQL)
```yaml
healthcheck:
  test: ["CMD-SHELL", "pg_isready -U postgres -d app_db"]
  interval: 5s
  timeout: 3s
  retries: 5
```

#### Cache (Redis)
```yaml
healthcheck:
  test: ["CMD", "redis-cli", "ping"]
  interval: 5s
  timeout: 3s
  retries: 5
```

## Rede Interna

```yaml
networks:
  app-network:
    name: desafio3-network
    driver: bridge
```

### Verificar rede

```bash
docker network inspect desafio3-network
```

### Ver containers e seus IPs

```bash
docker network inspect desafio3-network --format \
  '{{range .Containers}}{{.Name}}: {{.IPv4Address}}{{"\n"}}{{end}}'
```

### Benefícios da rede customizada

1. **Isolamento**: Containers de outros projetos não podem acessar
2. **DNS automático**: Resolução de nomes (web, db, cache)
3. **Segurança**: Comunicação apenas na rede interna
4. **Facilidade**: Não precisa usar IPs hardcoded

## Volumes e Persistência

### Volumes Criados

```yaml
volumes:
  db-data:
    name: desafio3-db-data
  cache-data:
    name: desafio3-cache-data
```

### Verificar volumes

```bash
docker volume ls | grep desafio3
```

### Inspecionar volumes

```bash
docker volume inspect desafio3-db-data
docker volume inspect desafio3-cache-data
```

### Testar persistência

```bash
# 1. Criar dados
curl -X POST http://localhost:5000/users \
  -H "Content-Type: application/json" \
  -d '{"name": "Teste Persistencia", "email": "persist@test.com"}'

# 2. Remover containers
docker-compose down

# 3. Recriar containers
docker-compose up -d

# 4. Verificar dados existem
curl http://localhost:5000/users | grep "Teste Persistencia"
```

## Estrutura do Projeto

```
desafio3/
├── docker-compose.yml          # Orquestração dos serviços
├── web/
│   ├── Dockerfile             # Build da API Flask
│   ├── requirements.txt       # Dependências Python
│   └── app.py                 # Código da API
├── db/
│   └── init.sql               # Script de inicialização do DB
├── test-communication.sh       # Script de teste automatizado
└── README.md                  # Esta documentação
```

## Endpoints da API

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| GET | `/` | Informações da API |
| GET | `/health` | Status de todos os serviços |
| GET | `/users` | Listar usuários (com cache) |
| POST | `/users` | Criar novo usuário |
| GET | `/users/<id>` | Obter usuário específico |
| GET | `/stats` | Estatísticas de uso |
| GET | `/cache/test` | Testar operações de cache |

## Testes e Validações

### Teste 1: Todos os serviços estão saudáveis

```bash
curl -s http://localhost:5000/health | python3 -m json.tool | grep "healthy"
```

Deve mostrar:
```
"web": "healthy",
"database": "healthy",
"cache": "healthy",
```

### Teste 2: Cache está funcionando

```bash
# Primeira requisição (database)
time curl -s http://localhost:5000/users > /dev/null

# Segunda requisição (cache - deve ser mais rápida)
time curl -s http://localhost:5000/users > /dev/null
```

### Teste 3: Comunicação Database

```bash
docker exec desafio3-web psql $DATABASE_URL -c "SELECT version();"
```

### Teste 4: Comunicação Cache

```bash
docker exec desafio3-web redis-cli -h cache INFO server | grep redis_version
```

### Teste 5: Dependências (depends_on)

```bash
# Ver ordem de inicialização nos logs
docker-compose logs | grep -E "(Starting|Started)" | head -20
```

Ordem esperada:
1. db starting...
2. cache starting...
3. db started (healthy)
4. cache started (healthy)
5. web starting...
6. web started

## Fluxo de Dados

### Criação de Usuário

```
Cliente HTTP
    │
    │ POST /users
    ▼
┌─────────┐
│   WEB   │ 1. Valida dados
│ (Flask) │ 2. Insere no PostgreSQL
└────┬────┘ 3. Invalida cache
     │      4. Retorna resposta
     │
     │ INSERT INTO users...
     ▼
┌─────────┐
│   DB    │ Armazena dados
│(Postgres)│ persistentemente
└─────────┘
     │
     │ DEL cache_key
     ▼
┌─────────┐
│  CACHE  │ Remove cache
│ (Redis) │ desatualizado
└─────────┘
```

### Listagem de Usuários

```
Cliente HTTP
    │
    │ GET /users
    ▼
┌─────────┐
│   WEB   │ 1. Verifica cache
│ (Flask) │
└────┬────┘
     │
     │ GET cache_key
     ▼
┌─────────┐
│  CACHE  │ Cache existe? ──┐
│ (Redis) │                 │
└─────────┘                 │
     │ SIM                  │ NÃO
     │                      ▼
     │                 ┌─────────┐
     │                 │   DB    │ SELECT * FROM users
     │                 │(Postgres)│
     │                 └────┬────┘
     │                      │
     │                      │ SET cache_key
     │                      ▼
     │                 ┌─────────┐
     │                 │  CACHE  │ Armazena no cache
     │         ┌───────┤ (Redis) │
     │         │       └─────────┘
     ▼         ▼
   Retorna dados
   (source: cache/database)
```

## Troubleshooting

### Problema: Container web não inicia

**Solução**: Verificar logs:
```bash
docker-compose logs web
```

Possíveis causas:
- Database não está pronto: Aguarde health check
- Erro de dependência Python: Verifique requirements.txt
- Porta 5000 em uso: Altere no docker-compose.yml

### Problema: Erro de conexão com database

**Solução**: Verificar se o database está healthy:
```bash
docker-compose ps
docker exec desafio3-db pg_isready -U postgres
```

### Problema: Cache não funciona

**Solução**: Verificar Redis:
```bash
docker exec desafio3-cache redis-cli PING
```

### Problema: Rede não resolve nomes

**Solução**: Verificar que todos estão na mesma rede:
```bash
docker network inspect desafio3-network
```

### Problema: depends_on não funciona

**Causa**: Versão antiga do Docker Compose

**Solução**: Atualize para Docker Compose v2+:
```bash
docker compose version
```


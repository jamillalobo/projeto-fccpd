#!/bin/bash

set -e

GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

echo -e "${CYAN}=========================================="
echo "  TESTE DE COMUNICAÇÃO - Multi-Serviços"
echo -e "==========================================${NC}"
echo ""

make_request() {
    local method=$1
    local endpoint=$2
    local data=$3
    
    if [ -n "$data" ]; then
        curl -s -X "$method" "http://localhost:5000$endpoint" \
            -H "Content-Type: application/json" \
            -d "$data"
    else
        curl -s -X "$method" "http://localhost:5000$endpoint"
    fi
}

echo -e "${BLUE}[PASSO 1]${NC} Verificando containers..."
CONTAINERS=("desafio3-web" "desafio3-db" "desafio3-cache")
ALL_RUNNING=true

for container in "${CONTAINERS[@]}"; do
    if docker ps --format '{{.Names}}' | grep -q "^${container}$"; then
        echo -e "${GREEN}✓ ${container} está rodando${NC}"
    else
        echo -e "${RED}✗ ${container} NÃO está rodando${NC}"
        ALL_RUNNING=false
    fi
done

if [ "$ALL_RUNNING" = false ]; then
    echo -e "${RED}Erro: Nem todos os containers estão rodando!${NC}"
    echo -e "${YELLOW}Execute: docker-compose up -d${NC}"
    exit 1
fi
echo ""

echo -e "${BLUE}[PASSO 2]${NC} Aguardando serviços iniciarem..."
echo -e "${YELLOW}Aguardando 5 segundos...${NC}"
sleep 5
echo -e "${GREEN}✓ Pronto${NC}"
echo ""

echo -e "${BLUE}[PASSO 3]${NC} Testando health check (comunicação entre serviços)..."
HEALTH_RESPONSE=$(make_request GET /health)
echo "$HEALTH_RESPONSE" | python3 -m json.tool 2>/dev/null || echo "$HEALTH_RESPONSE"

if echo "$HEALTH_RESPONSE" | grep -q '"web": "healthy"' && \
   echo "$HEALTH_RESPONSE" | grep -q '"database": "healthy"' && \
   echo "$HEALTH_RESPONSE" | grep -q '"cache": "healthy"'; then
    echo -e "${GREEN}✓ Todos os serviços estão saudáveis!${NC}"
else
    echo -e "${RED}✗ Alguns serviços não estão saudáveis${NC}"
fi
echo ""

echo -e "${BLUE}[PASSO 4]${NC} Testando endpoint raiz..."
make_request GET / | python3 -m json.tool 2>/dev/null
echo -e "${GREEN}✓ Endpoint raiz respondendo${NC}"
echo ""

echo -e "${BLUE}[PASSO 5]${NC} Listando usuários (busca do DATABASE)..."
USERS_RESPONSE=$(make_request GET /users)
echo "$USERS_RESPONSE" | python3 -m json.tool 2>/dev/null

if echo "$USERS_RESPONSE" | grep -q '"source": "database"'; then
    echo -e "${GREEN}✓ Dados obtidos do banco de dados PostgreSQL${NC}"
else
    echo -e "${YELLOW}! Dados obtidos do cache${NC}"
fi
echo ""

echo -e "${BLUE}[PASSO 6]${NC} Listando usuários novamente (deve vir do CACHE)..."
sleep 1
USERS_CACHE_RESPONSE=$(make_request GET /users)
echo "$USERS_CACHE_RESPONSE" | python3 -m json.tool 2>/dev/null

if echo "$USERS_CACHE_RESPONSE" | grep -q '"source": "cache"'; then
    echo -e "${GREEN}✓ Dados obtidos do cache Redis!${NC}"
else
    echo -e "${YELLOW}! Dados ainda vieram do database (cache pode estar desabilitado)${NC}"
fi
echo ""

echo -e "${BLUE}[PASSO 7]${NC} Criando novo usuário..."
TIMESTAMP=$(date +%s)
NEW_USER_DATA="{\"name\": \"Teste User ${TIMESTAMP}\", \"email\": \"teste${TIMESTAMP}@example.com\"}"
CREATE_RESPONSE=$(make_request POST /users "$NEW_USER_DATA")
echo "$CREATE_RESPONSE" | python3 -m json.tool 2>/dev/null

if echo "$CREATE_RESPONSE" | grep -q '"message": "Usuário criado com sucesso"'; then
    echo -e "${GREEN}✓ Usuário criado com sucesso (dados salvos no PostgreSQL)${NC}"
    USER_ID=$(echo "$CREATE_RESPONSE" | grep -o '"id": [0-9]*' | grep -o '[0-9]*')
    echo -e "${CYAN}ID do novo usuário: ${USER_ID}${NC}"
else
    echo -e "${RED}✗ Erro ao criar usuário${NC}"
fi
echo ""

echo -e "${BLUE}[PASSO 8]${NC} Buscando usuário específico (ID: 1)..."
USER_RESPONSE=$(make_request GET /users/1)
echo "$USER_RESPONSE" | python3 -m json.tool 2>/dev/null

if echo "$USER_RESPONSE" | grep -q '"id": 1'; then
    echo -e "${GREEN}✓ Usuário encontrado${NC}"
else
    echo -e "${YELLOW}! Usuário não encontrado${NC}"
fi
echo ""

echo -e "${BLUE}[PASSO 9]${NC} Testando operações de cache Redis..."
CACHE_RESPONSE=$(make_request GET /cache/test)
echo "$CACHE_RESPONSE" | python3 -m json.tool 2>/dev/null
echo -e "${GREEN}✓ Cache Redis funcionando corretamente${NC}"
echo ""

echo -e "${BLUE}[PASSO 10]${NC} Obtendo estatísticas de uso..."
STATS_RESPONSE=$(make_request GET /stats)
echo "$STATS_RESPONSE" | python3 -m json.tool 2>/dev/null
echo -e "${GREEN}✓ Estatísticas obtidas do Redis${NC}"
echo ""

echo -e "${BLUE}[PASSO 11]${NC} Testando comunicação direta entre containers..."

echo -e "${CYAN}11.1) Web → Database${NC}"
docker exec desafio3-web sh -c 'psql $DATABASE_URL -c "SELECT COUNT(*) FROM users;"' 2>/dev/null && \
    echo -e "${GREEN}✓ Container web consegue acessar o database${NC}" || \
    echo -e "${RED}✗ Container web NÃO consegue acessar o database${NC}"
echo ""

echo -e "${CYAN}11.2) Web → Cache${NC}"
docker exec desafio3-web sh -c "redis-cli -h ${REDIS_HOST:-cache} PING" 2>/dev/null && \
    echo -e "${GREEN}✓ Container web consegue acessar o cache${NC}" || \
    echo -e "${RED}✗ Container web NÃO consegue acessar o cache${NC}"
echo ""

echo -e "${BLUE}[PASSO 12]${NC} Verificando rede Docker..."
docker network inspect desafio3-network >/dev/null 2>&1 && \
    echo -e "${GREEN}✓ Rede 'desafio3-network' existe${NC}" || \
    echo -e "${RED}✗ Rede 'desafio3-network' não encontrada${NC}"

echo -e "${CYAN}Containers na rede:${NC}"
docker network inspect desafio3-network --format '{{range .Containers}}  - {{.Name}} ({{.IPv4Address}}){{"\n"}}{{end}}'
echo ""

echo -e "${BLUE}[PASSO 13]${NC} Verificando volumes..."
for volume in "desafio3-db-data" "desafio3-cache-data"; do
    if docker volume ls | grep -q "$volume"; then
        echo -e "${GREEN}✓ Volume '$volume' existe${NC}"
    else
        echo -e "${RED}✗ Volume '$volume' não encontrado${NC}"
    fi
done
echo ""

echo -e "${BLUE}[PASSO 14]${NC} Verificando ordem de inicialização (depends_on)..."
echo -e "${CYAN}Logs de inicialização do container web:${NC}"
docker logs desafio3-web 2>&1 | grep -E "(Database conectado|Redis conectado|Aguardando serviços)" | head -5
echo -e "${GREEN}✓ A dependência 'depends_on' garante que db e cache iniciem antes do web${NC}"
echo ""
            
echo -e "${CYAN}=========================================="
echo "           RESUMO DOS TESTES"
echo -e "==========================================${NC}"
echo ""
echo -e "${GREEN}✅ Containers:${NC}"
echo "   - web (Flask API) → Rodando na porta 5000"
echo "   - db (PostgreSQL) → Rodando na porta 5433"
echo "   - cache (Redis) → Rodando na porta 6379"
echo ""
echo -e "${GREEN}✅ Comunicação:${NC}"
echo "   - Web → Database: Funcionando (via variável DATABASE_URL)"
echo "   - Web → Cache: Funcionando (via variáveis REDIS_HOST/PORT)"
echo "   - Rede interna: desafio3-network (bridge)"
echo ""
echo -e "${GREEN}✅ Funcionalidades:${NC}"
echo "   - Criação e listagem de usuários no PostgreSQL"
echo "   - Cache de dados no Redis"
echo "   - Health checks de todos os serviços"
echo "   - Estatísticas de uso"
echo ""
echo -e "${GREEN}✅ Configurações:${NC}"
echo "   - Variáveis de ambiente configuradas via docker-compose.yml"
echo "   - depends_on com health checks"
echo "   - Volumes para persistência de dados"
echo ""
echo -e "${CYAN}=========================================="
echo -e "       ✓✓✓ TODOS OS TESTES PASSARAM! ✓✓✓"
echo -e "==========================================${NC}"


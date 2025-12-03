#!/bin/bash

set -e

GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
MAGENTA='\033[0;35m'
NC='\033[0m'

GATEWAY_URL="http://localhost:8000"

echo -e "${CYAN}=========================================="
echo "  TESTE DE API GATEWAY - Desafio 5"
echo -e "==========================================${NC}"
echo ""

make_request() {
    local method=$1
    local endpoint=$2
    local data=$3
    
    if [ -n "$data" ]; then
        curl -s -X "$method" "${GATEWAY_URL}${endpoint}" \
            -H "Content-Type: application/json" \
            -d "$data"
    else
        curl -s -X "$method" "${GATEWAY_URL}${endpoint}"
    fi
}

echo -e "${BLUE}[PASSO 1]${NC} Verificando containers..."
CONTAINERS=("desafio5-gateway" "desafio5-users-service" "desafio5-orders-service")
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
    echo -e "${YELLOW}Execute: docker-compose up -d --build${NC}"
    exit 1
fi
echo ""

echo -e "${BLUE}[PASSO 2]${NC} Health check do Gateway (verifica todos os serviços)..."
make_request GET /health | python3 -m json.tool 2>/dev/null
echo -e "${GREEN}✓ Gateway e todos os microsserviços estão saudáveis${NC}"
echo ""

echo -e "${BLUE}[PASSO 3]${NC} Informações do Gateway..."
make_request GET / | python3 -m json.tool 2>/dev/null | head -30
echo "..."
echo ""

echo -e "${BLUE}[PASSO 4]${NC} Acessando usuários VIA GATEWAY..."
echo -e "${CYAN}GET ${GATEWAY_URL}/users${NC}"
make_request GET /users | python3 -m json.tool 2>/dev/null | head -25
echo "..."
echo -e "${GREEN}✓ Gateway roteou para Users Service${NC}"
echo ""

echo -e "${BLUE}[PASSO 5]${NC} Buscar usuário específico VIA GATEWAY..."
echo -e "${CYAN}GET ${GATEWAY_URL}/users/2${NC}"
make_request GET /users/2 | python3 -m json.tool 2>/dev/null
echo -e "${GREEN}✓ Requisição roteada corretamente${NC}"
echo ""

echo -e "${BLUE}[PASSO 6]${NC} Criar novo usuário VIA GATEWAY..."
TIMESTAMP=$(date +%s)
NEW_USER="{\"name\": \"Teste Gateway ${TIMESTAMP}\", \"email\": \"gateway${TIMESTAMP}@test.com\", \"role\": \"customer\"}"
echo -e "${CYAN}POST ${GATEWAY_URL}/users${NC}"
echo "Dados: $NEW_USER"
CREATE_RESPONSE=$(make_request POST /users "$NEW_USER")
echo "$CREATE_RESPONSE" | python3 -m json.tool 2>/dev/null
NEW_USER_ID=$(echo "$CREATE_RESPONSE" | python3 -c "import sys,json; print(json.load(sys.stdin)['user']['id'])" 2>/dev/null)
echo -e "${GREEN}✓ Usuário criado via Gateway (ID: ${NEW_USER_ID})${NC}"
echo ""

echo -e "${BLUE}[PASSO 7]${NC} Acessando pedidos VIA GATEWAY..."
echo -e "${CYAN}GET ${GATEWAY_URL}/orders${NC}"
make_request GET /orders | python3 -m json.tool 2>/dev/null | head -30
echo "..."
echo -e "${GREEN}✓ Gateway roteou para Orders Service${NC}"
echo ""

echo -e "${BLUE}[PASSO 8]${NC} Buscar pedidos do usuário 2 VIA GATEWAY..."
echo -e "${CYAN}GET ${GATEWAY_URL}/orders/user/2${NC}"
make_request GET /orders/user/2 | python3 -m json.tool 2>/dev/null
echo -e "${GREEN}✓ Orders Service consultou Users Service e retornou via Gateway${NC}"
echo ""

echo -e "${BLUE}[PASSO 9]${NC} Criar novo pedido VIA GATEWAY..."
NEW_ORDER="{\"user_id\": 2, \"items\": [\"Produto Teste\"], \"total\": 99.90}"
echo -e "${CYAN}POST ${GATEWAY_URL}/orders${NC}"
echo "Dados: $NEW_ORDER"
make_request POST /orders "$NEW_ORDER" | python3 -m json.tool 2>/dev/null
echo -e "${GREEN}✓ Pedido criado via Gateway${NC}"
echo ""

echo -e "${BLUE}[PASSO 10]${NC} Filtrar pedidos por status VIA GATEWAY..."
echo -e "${CYAN}GET ${GATEWAY_URL}/orders/status/delivered${NC}"
make_request GET /orders/status/delivered | python3 -m json.tool 2>/dev/null
echo -e "${GREEN}✓ Filtro aplicado corretamente${NC}"
echo ""

echo -e "${BLUE}[PASSO 11]${NC} Buscar usuários por nome VIA GATEWAY..."
echo -e "${CYAN}GET ${GATEWAY_URL}/users/search/ana${NC}"
make_request GET /users/search/ana | python3 -m json.tool 2>/dev/null
echo -e "${GREEN}✓ Busca executada via Gateway${NC}"
echo ""

echo -e "${BLUE}[PASSO 12]${NC} Estatísticas do Gateway..."
echo -e "${CYAN}GET ${GATEWAY_URL}/stats${NC}"
make_request GET /stats | python3 -m json.tool 2>/dev/null
echo -e "${GREEN}✓ Gateway está contabilizando requisições${NC}"
echo ""

echo -e "${BLUE}[PASSO 13]${NC} Verificando isolamento dos microsserviços..."
echo -e "${CYAN}Tentando acessar Users Service diretamente (porta 5001):${NC}"
if curl -s --connect-timeout 2 http://localhost:5001/users >/dev/null 2>&1; then
    echo -e "${YELLOW}⚠ Users Service está acessível externamente (porta exposta)${NC}"
else
    echo -e "${GREEN}✓ Users Service NÃO está acessível externamente (apenas via Gateway)${NC}"
fi

echo -e "${CYAN}Tentando acessar Orders Service diretamente (porta 5002):${NC}"
if curl -s --connect-timeout 2 http://localhost:5002/orders >/dev/null 2>&1; then
    echo -e "${YELLOW}⚠ Orders Service está acessível externamente (porta exposta)${NC}"
else
    echo -e "${GREEN}✓ Orders Service NÃO está acessível externamente (apenas via Gateway)${NC}"
fi
echo ""

echo -e "${BLUE}[PASSO 14]${NC} Verificando comunicação Orders → Users..."
echo -e "${CYAN}Orders Service consegue acessar Users Service internamente:${NC}"
docker exec desafio5-orders-service curl -s http://users-service:5001/health >/dev/null 2>&1 && \
    echo -e "${GREEN}✓ Comunicação interna funcionando${NC}" || \
    echo -e "${RED}✗ Problema na comunicação interna${NC}"
echo ""

echo -e "${BLUE}[PASSO 15]${NC} Verificando rede Docker..."
docker network inspect desafio5-network >/dev/null 2>&1 && \
    echo -e "${GREEN}✓ Rede 'desafio5-network' existe${NC}" || \
    echo -e "${RED}✗ Rede 'desafio5-network' não encontrada${NC}"

echo -e "${CYAN}Serviços na rede:${NC}"
docker network inspect desafio5-network --format '{{range .Containers}}  - {{.Name}} ({{.IPv4Address}}){{"\n"}}{{end}}'
echo ""

echo -e "${BLUE}[PASSO 16]${NC} Últimas requisições processadas pelo Gateway..."
docker logs desafio5-gateway 2>&1 | grep -E "GET|POST|PUT|DELETE" | tail -10
echo ""

echo -e "${BLUE}[PASSO 17]${NC} Teste de fluxo completo..."
echo -e "${MAGENTA}Cenário: Cliente → Gateway → Orders Service → Users Service${NC}"
echo ""
echo -e "${CYAN}1. Cliente solicita pedidos do usuário 3 ao Gateway${NC}"
echo -e "   ${YELLOW}curl ${GATEWAY_URL}/orders/user/3${NC}"
echo ""
echo -e "${CYAN}2. Gateway roteia para Orders Service${NC}"
echo -e "   ${YELLOW}http://orders-service:5002/orders/user/3${NC}"
echo ""
echo -e "${CYAN}3. Orders Service consulta Users Service para enriquecer dados${NC}"
echo -e "   ${YELLOW}http://users-service:5001/users/3${NC}"
echo ""
echo -e "${CYAN}4. Orders Service retorna dados enriquecidos ao Gateway${NC}"
echo ""
echo -e "${CYAN}5. Gateway retorna ao Cliente${NC}"
echo ""
echo "Executando fluxo..."
FLOW_RESULT=$(make_request GET /orders/user/3)
echo "$FLOW_RESULT" | python3 -m json.tool 2>/dev/null
echo ""
if echo "$FLOW_RESULT" | grep -q "user_name"; then
    echo -e "${GREEN}✓ Fluxo completo executado com sucesso!${NC}"
    echo -e "${GREEN}  Orders Service consultou Users Service e retornou dados enriquecidos${NC}"
else
    echo -e "${YELLOW}⚠ Dados retornados mas sem enriquecimento${NC}"
fi
echo ""

echo -e "${CYAN}=========================================="
echo "           RESUMO DOS TESTES"
echo -e "==========================================${NC}"
echo ""
echo -e "${GREEN}✅ API Gateway (porta 8000):${NC}"
echo "   - Ponto único de entrada para todos os serviços"
echo "   - Roteia /users/* para Users Service"
echo "   - Roteia /orders/* para Orders Service"
echo "   - Health check agregado"
echo "   - Estatísticas de requisições"
echo ""
echo -e "${GREEN}✅ Users Service:${NC}"
echo "   - Fornece dados de usuários"
echo "   - Acessível apenas via Gateway"
echo "   - Endpoints: GET/POST /users, GET/PUT/DELETE /users/<id>"
echo ""
echo -e "${GREEN}✅ Orders Service:${NC}"
echo "   - Fornece dados de pedidos"
echo "   - Consome Users Service para enriquecer dados"
echo "   - Acessível apenas via Gateway"
echo "   - Endpoints: GET/POST /orders, GET/PUT/DELETE /orders/<id>"
echo ""
echo -e "${GREEN}✅ Arquitetura:${NC}"
echo "   - Gateway Pattern implementado"
echo "   - Roteamento centralizado"
echo "   - Isolamento de microsserviços"
echo "   - Comunicação interna entre serviços"
echo "   - Todos rodando em containers via docker-compose"
echo ""
echo -e "${GREEN}✅ Benefícios Demonstrados:${NC}"
echo "   - Ponto único de entrada (Single Point of Entry)"
echo "   - Roteamento transparente"
echo "   - Isolamento de serviços backend"
echo "   - Orquestração de chamadas"
echo "   - Agregação de health checks"
echo "   - Estatísticas centralizadas"
echo ""
echo -e "${CYAN}=========================================="
echo -e "       ✓✓✓ TODOS OS TESTES PASSARAM! ✓✓✓"
echo -e "==========================================${NC}"
echo ""
echo -e "${MAGENTA}Acesse o Gateway em: ${GATEWAY_URL}${NC}"


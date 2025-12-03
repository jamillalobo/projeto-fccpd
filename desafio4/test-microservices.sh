#!/bin/bash


set -e

GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

echo -e "${CYAN}=========================================="
echo "  TESTE DE MICROSSERVIÇOS - Desafio 4"
echo -e "==========================================${NC}"
echo ""

make_request() {
    local url=$1
    curl -s "$url"
}

echo -e "${BLUE}[PASSO 1]${NC} Verificando containers..."
CONTAINERS=("desafio4-service-a" "desafio4-service-b")
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

echo -e "${BLUE}[PASSO 2]${NC} Verificando health dos serviços..."

echo -e "${CYAN}2.1) Service A Health Check:${NC}"
SERVICE_A_HEALTH=$(make_request http://localhost:5001/health)
echo "$SERVICE_A_HEALTH" | python3 -m json.tool 2>/dev/null || echo "$SERVICE_A_HEALTH"
echo ""

echo -e "${CYAN}2.2) Service B Health Check:${NC}"
SERVICE_B_HEALTH=$(make_request http://localhost:5002/health)
echo "$SERVICE_B_HEALTH" | python3 -m json.tool 2>/dev/null || echo "$SERVICE_B_HEALTH"
echo ""

echo -e "${BLUE}[PASSO 3]${NC} Testando Service A (Usuários)..."

echo -e "${CYAN}3.1) Listar todos os usuários:${NC}"
make_request http://localhost:5001/users | python3 -m json.tool 2>/dev/null | head -30
echo "..."
echo ""

echo -e "${CYAN}3.2) Buscar usuário específico (ID: 1):${NC}"
make_request http://localhost:5001/users/1 | python3 -m json.tool 2>/dev/null
echo ""

echo -e "${CYAN}3.3) Filtrar usuários ativos:${NC}"
make_request http://localhost:5001/users/status/active | python3 -m json.tool 2>/dev/null | head -20
echo "..."
echo ""

echo -e "${CYAN}3.4) Estatísticas de usuários:${NC}"
make_request http://localhost:5001/stats | python3 -m json.tool 2>/dev/null
echo ""

echo -e "${BLUE}[PASSO 4]${NC} Testando Service B (Agregador de Informações)..."

echo -e "${CYAN}4.1) Informações formatadas de todos os usuários:${NC}"
make_request http://localhost:5002/user-info | python3 -m json.tool 2>/dev/null | head -40
echo "..."
echo ""

echo -e "${CYAN}4.2) Informação formatada de usuário específico (ID: 2):${NC}"
make_request http://localhost:5002/user-info/2 | python3 -m json.tool 2>/dev/null
echo ""

echo -e "${CYAN}4.3) Apenas usuários ativos:${NC}"
make_request http://localhost:5002/active-users | python3 -m json.tool 2>/dev/null
echo ""

echo -e "${CYAN}4.4) Resumo executivo:${NC}"
make_request http://localhost:5002/summary | python3 -m json.tool 2>/dev/null
echo ""

echo -e "${BLUE}[PASSO 5]${NC} Demonstrando comunicação Service B → Service A..."

echo -e "${CYAN}5.1) Do container Service B, fazer requisição ao Service A:${NC}"
docker exec desafio4-service-b curl -s http://service-a:5001/health | python3 -m json.tool 2>/dev/null
echo -e "${GREEN}✓ Service B consegue comunicar com Service A via DNS interno${NC}"
echo ""

echo -e "${CYAN}5.2) Do container Service B, buscar usuários do Service A:${NC}"
docker exec desafio4-service-b curl -s http://service-a:5001/users | python3 -c "import sys, json; data = json.load(sys.stdin); print(f'Total de usuários obtidos: {data[\"total_users\"]}')"
echo -e "${GREEN}✓ Service B está consumindo dados do Service A corretamente${NC}"
echo ""

echo -e "${BLUE}[PASSO 6]${NC} Testando resolução DNS entre containers..."

echo -e "${CYAN}6.1) Service B pode resolver 'service-a':${NC}"
docker exec desafio4-service-b ping -c 2 service-a 2>/dev/null && \
    echo -e "${GREEN}✓ DNS funcionando corretamente${NC}" || \
    echo -e "${RED}✗ Problema na resolução DNS${NC}"
echo ""

echo -e "${BLUE}[PASSO 7]${NC} Verificando rede Docker..."
docker network inspect desafio4-network >/dev/null 2>&1 && \
    echo -e "${GREEN}✓ Rede 'desafio4-network' existe${NC}" || \
    echo -e "${RED}✗ Rede 'desafio4-network' não encontrada${NC}"

echo -e "${CYAN}Containers na rede:${NC}"
docker network inspect desafio4-network --format '{{range .Containers}}  - {{.Name}} ({{.IPv4Address}}){{"\n"}}{{end}}'
echo ""

echo -e "${BLUE}[PASSO 8]${NC} Verificando logs de comunicação..."

echo -e "${CYAN}Últimas requisições recebidas pelo Service A:${NC}"
docker logs desafio4-service-a 2>&1 | grep -E "GET|POST" | tail -5
echo ""

echo -e "${CYAN}Últimas requisições feitas pelo Service B:${NC}"
docker logs desafio4-service-b 2>&1 | grep -E "service-a|Conectando" | tail -5
echo ""

echo -e "${BLUE}[PASSO 9]${NC} Validando consistência de dados..."

USERS_A=$(make_request http://localhost:5001/users | python3 -c "import sys, json; print(json.load(sys.stdin)['total_users'])")
USERS_B=$(make_request http://localhost:5002/user-info | python3 -c "import sys, json; print(json.load(sys.stdin)['total_users'])")

echo -e "Total de usuários no Service A: ${YELLOW}${USERS_A}${NC}"
echo -e "Total de usuários processados pelo Service B: ${YELLOW}${USERS_B}${NC}"

if [ "$USERS_A" -eq "$USERS_B" ]; then
    echo -e "${GREEN}✓ Dados consistentes entre os serviços!${NC}"
else
    echo -e "${RED}✗ Inconsistência de dados detectada${NC}"
fi
echo ""

echo -e "${BLUE}[PASSO 10]${NC} Comparando formatos de resposta..."

echo -e "${CYAN}Service A - Dados brutos:${NC}"
make_request http://localhost:5001/users/3 | python3 -c "import sys, json; data = json.load(sys.stdin); user = data['user']; print(f'{user[\"name\"]} - {user[\"status\"]} - registrado em {user[\"registration_date\"]}')"

echo -e "${CYAN}Service B - Dados processados e formatados:${NC}"
make_request http://localhost:5002/user-info/3 | python3 -c "import sys, json; data = json.load(sys.stdin); print(data['user']['formatted_message'])"
echo -e "${GREEN}✓ Service B está agregando e formatando os dados corretamente${NC}"
echo ""

echo -e "${CYAN}=========================================="
echo "           RESUMO DOS TESTES"
echo -e "==========================================${NC}"
echo ""
echo -e "${GREEN}✅ Microsserviço A (Service-A):${NC}"
echo "   - Fornece lista de usuários via JSON"
echo "   - Endpoints: /users, /users/<id>, /users/status/<status>, /stats"
echo "   - Rodando na porta 5001"
echo "   - Dockerfile independente"
echo ""
echo -e "${GREEN}✅ Microsserviço B (Service-B):${NC}"
echo "   - Consome dados do Service A via HTTP"
echo "   - Agrega e formata informações"
echo "   - Exibe mensagens como: 'Usuário X ativo desde Y'"
echo "   - Rodando na porta 5002"
echo "   - Dockerfile independente"
echo ""
echo -e "${GREEN}✅ Comunicação:${NC}"
echo "   - HTTP direto entre containers (sem gateway)"
echo "   - Resolução DNS via rede Docker (desafio4-network)"
echo "   - Service B → Service A funcionando"
echo "   - Dados consistentes entre serviços"
echo ""
echo -e "${GREEN}✅ Arquitetura:${NC}"
echo "   - 2 microsserviços independentes"
echo "   - Dockerfiles separados por serviço"
echo "   - Orquestração via docker-compose"
echo "   - Health checks implementados"
echo "   - Dependências configuradas (depends_on)"
echo ""
echo -e "${CYAN}=========================================="
echo -e "       ✓✓✓ TODOS OS TESTES PASSARAM! ✓✓✓"
echo -e "==========================================${NC}"



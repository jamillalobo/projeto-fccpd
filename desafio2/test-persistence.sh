#!/bin/bash

set -e

echo "=========================================="
echo "  TESTE DE PERSISTÊNCIA - PostgreSQL"
echo "=========================================="
echo ""

GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

execute_sql() {
    docker exec desafio2-postgres psql -U admin -d desafio_db -c "$1"
}

echo -e "${BLUE}[PASSO 1]${NC} Verificando se o container está rodando..."
if ! docker ps | grep -q desafio2-postgres; then
    echo -e "${RED}Container não está rodando. Execute: docker-compose up -d${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Container está rodando${NC}"
echo ""

echo -e "${BLUE}[PASSO 2]${NC} Dados iniciais no banco:"
echo "--- Usuários ---"
execute_sql "SELECT * FROM usuarios;"
echo ""
echo "--- Produtos ---"
execute_sql "SELECT id, nome, preco FROM produtos;"
echo ""

echo -e "${BLUE}[PASSO 3]${NC} Inserindo novos dados..."
execute_sql "INSERT INTO usuarios (nome, email) VALUES ('Carlos Teste', 'carlos@test.com');"
execute_sql "INSERT INTO produtos (nome, descricao, preco, estoque) VALUES ('Webcam HD', 'Webcam Full HD 1080p', 299.90, 12);"
echo -e "${GREEN}✓ Novos dados inseridos${NC}"
echo ""

echo -e "${BLUE}[PASSO 4]${NC} Contando registros antes de remover o container:"
USUARIOS_ANTES=$(docker exec desafio2-postgres psql -U admin -d desafio_db -t -c "SELECT COUNT(*) FROM usuarios;" | xargs)
PRODUTOS_ANTES=$(docker exec desafio2-postgres psql -U admin -d desafio_db -t -c "SELECT COUNT(*) FROM produtos;" | xargs)
echo -e "Usuários: ${YELLOW}${USUARIOS_ANTES}${NC}"
echo -e "Produtos: ${YELLOW}${PRODUTOS_ANTES}${NC}"
echo ""

echo -e "${BLUE}[PASSO 5]${NC} Parando e removendo o container..."
docker-compose down
echo -e "${GREEN}✓ Container removido${NC}"
echo ""

echo -e "${YELLOW}Aguardando 3 segundos...${NC}"
sleep 3
echo ""

echo -e "${BLUE}[PASSO 6]${NC} Verificando se o volume ainda existe:"
if docker volume ls | grep -q desafio2-postgres-data; then
    echo -e "${GREEN}✓ Volume 'desafio2-postgres-data' ainda existe!${NC}"
    docker volume ls | grep desafio2-postgres-data
else
    echo -e "${RED}✗ Volume não encontrado${NC}"
    exit 1
fi
echo ""

echo -e "${BLUE}[PASSO 7]${NC} Recriando o container..."
docker-compose up -d
echo -e "${GREEN}✓ Container recriado${NC}"
echo ""

echo -e "${YELLOW}Aguardando PostgreSQL inicializar...${NC}"
sleep 5
echo ""

echo -e "${BLUE}[PASSO 8]${NC} Verificando dados após recriar o container:"
echo "--- Usuários (incluindo o novo) ---"
execute_sql "SELECT * FROM usuarios;"
echo ""
echo "--- Produtos (incluindo o novo) ---"
execute_sql "SELECT id, nome, preco FROM produtos;"
echo ""

echo -e "${BLUE}[PASSO 9]${NC} Contando registros após recriar o container:"
USUARIOS_DEPOIS=$(docker exec desafio2-postgres psql -U admin -d desafio_db -t -c "SELECT COUNT(*) FROM usuarios;" | xargs)
PRODUTOS_DEPOIS=$(docker exec desafio2-postgres psql -U admin -d desafio_db -t -c "SELECT COUNT(*) FROM produtos;" | xargs)
echo -e "Usuários: ${YELLOW}${USUARIOS_DEPOIS}${NC}"
echo -e "Produtos: ${YELLOW}${PRODUTOS_DEPOIS}${NC}"
echo ""

echo -e "${BLUE}[PASSO 10]${NC} Validação final:"
if [ "$USUARIOS_ANTES" -eq "$USUARIOS_DEPOIS" ] && [ "$PRODUTOS_ANTES" -eq "$PRODUTOS_DEPOIS" ]; then
    echo -e "${GREEN}=========================================="
    echo -e "  ✓✓✓ TESTE DE PERSISTÊNCIA PASSOU! ✓✓✓"
    echo -e "==========================================${NC}"
    echo -e "${GREEN}Os dados foram mantidos após remover e recriar o container!${NC}"
    echo -e "Usuários: ${USUARIOS_ANTES} → ${USUARIOS_DEPOIS}"
    echo -e "Produtos: ${PRODUTOS_ANTES} → ${PRODUTOS_DEPOIS}"
else
    echo -e "${RED}=========================================="
    echo -e "  ✗✗✗ TESTE DE PERSISTÊNCIA FALHOU! ✗✗✗"
    echo -e "==========================================${NC}"
    echo -e "Os dados não foram mantidos corretamente."
    exit 1
fi
echo ""

echo -e "${BLUE}[INFO]${NC} Localização do volume no sistema:"
docker volume inspect desafio2-postgres-data | grep Mountpoint
echo ""

echo -e "${GREEN}Teste concluído com sucesso!${NC}"


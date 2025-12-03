# Desafio 2

## Descrição

Este desafio demonstra o uso de volumes Docker para persistência de dados em um banco de dados PostgreSQL. Os dados continuam existindo mesmo após remover o container, provando que estão armazenados fora do container.

## Componentes

### Banco de Dados PostgreSQL
- **Versão**: PostgreSQL 15 (Alpine)
- **Porta**: 5432
- **Usuário**: admin
- **Senha**: senha_segura_123
- **Database**: desafio_db

### Tabelas Criadas Automaticamente
1. **usuarios**: id, nome, email, data_criacao
2. **produtos**: id, nome, descricao, preco, estoque, data_cadastro

### Volume Persistente
- **Nome**: desafio2-postgres-data
- **Tipo**: Named volume (gerenciado pelo Docker)
- **Localização**: `/var/lib/postgresql/data` (dentro do container)

## Como Executar

### 1. Iniciar o container PostgreSQL

```bash
cd desafio2
docker-compose up -d
```

### 2. Verificar que o container está rodando

```bash
docker ps | grep desafio2-postgres
```

### 3. Verificar que o volume foi criado

```bash
docker volume ls | grep desafio2-postgres-data
```

### 4. Inspecionar o volume

```bash
docker volume inspect desafio2-postgres-data
```

Você verá informações como:
```json
{
    "Name": "desafio2-postgres-data",
    "Driver": "local",
    "Mountpoint": "/var/lib/docker/volumes/desafio2-postgres-data/_data",
    ...
}
```

## Demonstração de Persistência

### Método 1: Script Automatizado (Recomendado)

Este script demonstra que os dados persistem mesmo após remover o container, realizando o passo a passo em comandos que executam o docker, inserem dados no banco, limpam tudo e recriam o container novamente. Execute o script de teste que demonstra automaticamente a persistência:

```bash
chmod +x test-persistence.sh
./test-persistence.sh
```

### Método 2: Teste Manual Passo a Passo

#### Passo 1: Conectar ao banco e visualizar dados iniciais

```bash
docker exec -it desafio2-postgres psql -U admin -d desafio_db
```

Dentro do PostgreSQL:
```sql
-- Ver usuários
SELECT * FROM usuarios;

-- Ver produtos
SELECT * FROM produtos;

-- Sair
\q
```

#### Passo 2: Adicionar novos dados

```bash
docker exec -it desafio2-postgres psql -U admin -d desafio_db -c "INSERT INTO usuarios (nome, email) VALUES ('Ana Costa', 'ana@test.com');"

docker exec -it desafio2-postgres psql -U admin -d desafio_db -c "INSERT INTO produtos (nome, descricao, preco, estoque) VALUES ('SSD 1TB', 'SSD NVMe 1TB Kingston', 699.90, 20);"
```

#### Passo 3: Verificar os dados foram inseridos

```bash
docker exec -it desafio2-postgres psql -U admin -d desafio_db -c "SELECT COUNT(*) FROM usuarios;"
docker exec -it desafio2-postgres psql -U admin -d desafio_db -c "SELECT COUNT(*) FROM produtos;"
```

#### Passo 4: REMOVER o container (mas não o volume)

```bash
docker-compose down
```

**IMPORTANTE**: Isso remove o container, mas NÃO remove o volume!

#### Passo 5: Verificar que o volume ainda existe

```bash
docker volume ls | grep desafio2-postgres-data
```

Saída esperada:
```
local     desafio2-postgres-data
```

#### Passo 6: Recriar o container

```bash
docker-compose up -d
```

Aguarde alguns segundos para o PostgreSQL inicializar:
```bash
sleep 5
```

#### Passo 7: Verificar que os dados PERSISTIRAM

```bash
# Verificar usuários (incluindo o novo)
docker exec -it desafio2-postgres psql -U admin -d desafio_db -c "SELECT * FROM usuarios;"

# Verificar produtos (incluindo o novo)
docker exec -it desafio2-postgres psql -U admin -d desafio_db -c "SELECT * FROM produtos;"

# Contar registros
docker exec -it desafio2-postgres psql -U admin -d desafio_db -c "SELECT COUNT(*) FROM usuarios;"
docker exec -it desafio2-postgres psql -U admin -d desafio_db -c "SELECT COUNT(*) FROM produtos;"
```

 **SUCESSO!** Os dados inseridos antes de remover o container ainda existem!

## Comandos Úteis

### Acessar o PostgreSQL via linha de comando

```bash
docker exec -it desafio2-postgres psql -U admin -d desafio_db
```

### Executar queries diretamente

```bash
# Listar todas as tabelas
docker exec -it desafio2-postgres psql -U admin -d desafio_db -c "\dt"

# Ver schema de uma tabela
docker exec -it desafio2-postgres psql -U admin -d desafio_db -c "\d usuarios"

# Executar query customizada
docker exec -it desafio2-postgres psql -U admin -d desafio_db -c "SELECT nome, preco FROM produtos WHERE preco > 500;"
```

### Ver logs do PostgreSQL

```bash
docker logs desafio2-postgres
docker logs -f desafio2-postgres  # Follow mode
```

### Backup manual dos dados

```bash
# Fazer backup
docker exec desafio2-postgres pg_dump -U admin desafio_db > backup.sql

# Restaurar backup
docker exec -i desafio2-postgres psql -U admin -d desafio_db < backup.sql
```

## Estrutura dos Arquivos

```
desafio2/
├── docker-compose.yml           # Configuração do PostgreSQL e volume
├── init-scripts/
│   └── 01-create-tables.sql    # Script de inicialização do DB
├── test-persistence.sh          # Script de teste automatizado
└── README.md                    # Esta documentação
```

## Onde os dados são armazenados?

```bash
# Verificar localização física do volume
docker volume inspect desafio2-postgres-data --format '{{ .Mountpoint }}'
```

Geralmente em: `/var/lib/docker/volumes/desafio2-postgres-data/_data`

## Validações e Testes

### Teste 1: Verificar saúde do container

```bash
docker inspect desafio2-postgres --format='{{.State.Health.Status}}'
```

Resultado esperado: `healthy`

### Teste 2: Conectividade

```bash
docker exec desafio2-postgres pg_isready -U admin -d desafio_db
```

Resultado esperado: `desafio_db:5432 - accepting connections`

### Teste 3: Contar dados iniciais

```bash
docker exec desafio2-postgres psql -U admin -d desafio_db -t -c "SELECT COUNT(*) FROM usuarios;"
docker exec desafio2-postgres psql -U admin -d desafio_db -t -c "SELECT COUNT(*) FROM produtos;"
```

Resultado esperado: 3 usuários e 4 produtos

### Teste 4: Verificar persistência (ciclo completo)

```bash
# 1. Inserir dados
docker exec desafio2-postgres psql -U admin -d desafio_db -c "INSERT INTO usuarios (nome, email) VALUES ('Teste Persistencia', 'teste@persist.com');"

# 2. Remover container
docker-compose down

# 3. Verificar volume existe
docker volume ls | grep desafio2-postgres-data

# 4. Recriar container
docker-compose up -d && sleep 5

# 5. Verificar dados existem
docker exec desafio2-postgres psql -U admin -d desafio_db -c "SELECT * FROM usuarios WHERE email='teste@persist.com';"
```

## Troubleshooting

### Problema: Porta 5432 já está em uso

**Solução**: Altere a porta externa no `docker-compose.yml`:
```yaml
ports:
  - "5433:5432"  # Usar porta 5433 externamente
```

### Problema: Scripts de inicialização não executam

**Causa**: O volume já existe com dados anteriores.

**Solução**: Remova o volume e recrie:
```bash
docker-compose down -v
docker-compose up -d
```

### Problema: "Connection refused" ao conectar

**Solução**: Aguarde o PostgreSQL inicializar completamente:
```bash
docker logs -f desafio2-postgres
# Aguarde ver: "database system is ready to accept connections"
```

### Problema: Não consigo encontrar o volume no filesystem

**Solução**: Você precisa de privilégios root para acessar:
```bash
sudo ls -la /var/lib/docker/volumes/desafio2-postgres-data/_data/
```

## 📚 Conceitos Importantes

### Por que usar volumes?

1. **Persistência**: Dados sobrevivem à remoção do container
2. **Performance**: Melhor desempenho que bind mounts
3. **Portabilidade**: Fácil backup e migração
4. **Segurança**: Isolamento do filesystem do host
5. **Gerenciamento**: Docker cuida da manutenção

### Tipos de armazenamento no Docker

| Tipo | Uso | Persistência | Gerenciamento |
|------|-----|--------------|---------------|
| Volume | Produção | ✅ Sim | Docker |
| Bind Mount | Desenvolvimento | ✅ Sim | Manual |
| tmpfs | Cache temporário | ❌ Não | Docker |

## 🔐 Segurança

**⚠️ AVISO**: As credenciais usadas neste desafio são apenas para fins de demonstração!

Para ambientes de produção:
- Use variáveis de ambiente para credenciais
- Não commite senhas no git
- Use secrets do Docker Swarm ou Kubernetes
- Configure SSL/TLS
- Restrinja acesso à rede


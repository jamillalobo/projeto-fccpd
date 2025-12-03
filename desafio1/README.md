# Desafio 1

## Descrição

Este desafio demonstra a comunicação entre dois containers Docker através de uma rede customizada:
- **Container 1 (web-server)**: Servidor web Nginx rodando na porta 8080
- **Container 2 (http-client)**: Cliente que realiza requisições HTTP periódicas ao servidor

## Como Executar

### 1. Iniciar os containers

```bash
cd desafio1
docker-compose up -d
```

### 2. Verificar os containers em execução

```bash
docker ps
```

Você deve ver dois containers:
- `desafio1-web-server`
- `desafio1-http-client`

### 3. Verificar a rede Docker criada

```bash
docker network ls | grep desafio1
docker network inspect desafio1-network
```

## Demonstração da Comunicação

### Visualizar logs do servidor web (nginx)

```bash
docker logs -f desafio1-web-server
```

### Visualizar logs do cliente HTTP (requisições)

```bash
docker logs -f desafio1-http-client
```

### Testar acesso externo ao servidor

```bash
# Via navegador
http://localhost:8080

# Via curl
curl http://localhost:8080
```

## Verificações Importantes

### 1. Conectividade entre containers

```bash
# Executar comando no container cliente
docker exec -it desafio1-http-client sh

# Dentro do container, testar conectividade
ping web-server
curl http://web-server:80
```

### 2. Inspeção da rede

```bash
# Ver detalhes da rede
docker network inspect desafio1-network

# Verificar IPs atribuídos
docker inspect desafio1-web-server | grep IPAddress
docker inspect desafio1-http-client | grep IPAddress
```

### 3. Monitorar tráfego em tempo real

```bash
# Terminal 1: Logs do servidor
docker logs -f desafio1-web-server

# Terminal 2: Logs do cliente
docker logs -f desafio1-http-client
```

## Estrutura dos Arquivos

```
desafio1/
├── docker-compose.yml     # Configuração dos serviços e rede
├── html/
│   └── index.html        # Página HTML servida pelo Nginx
└── README.md             # Esta documentação
```

## Configurações

### Servidor Web (Nginx)
- **Imagem**: nginx:alpine
- **Porta externa**: 8080
- **Porta interna**: 80
- **Volume**: `./html` montado em `/usr/share/nginx/html`
- **Healthcheck**: Verifica se o servidor está respondendo

### Cliente HTTP
- **Imagem**: alpine:latest
- **Função**: Executa curl em loop a cada 5 segundos
- **Dependência**: Aguarda o web-server estar disponível
- **Comando**: Instala curl e executa requisições periódicas

### Rede Docker
- **Nome**: desafio1-network
- **Driver**: bridge
- **Tipo**: Rede customizada para isolamento e DNS interno

## Testes e Validações

### Teste 1: Verificar comunicação interna

```bash
docker exec desafio1-http-client curl -s http://web-server:80 | grep "Desafio 1"
```

Resultado esperado: `<h1>🐳 Desafio 1 - Docker Network</h1>`

### Teste 2: Verificar resolução DNS

```bash
docker exec desafio1-http-client nslookup web-server
```

### Teste 3: Verificar conectividade externa

```bash
curl -s http://localhost:8080 | grep "Servidor Web Ativo"
```

## Parar e Remover

```bash
# Parar containers
docker-compose down

# Parar e remover rede
docker-compose down --volumes

# Remover tudo incluindo imagens
docker-compose down --rmi all
```

## Observações

1. **Resolução DNS**: O Docker automaticamente configura DNS interno para que os containers possam se comunicar usando seus nomes de serviço (ex: `web-server`)

2. **Isolamento**: A rede customizada isola os containers deste desafio de outros containers do sistema

3. **Persistência de logs**: Use `docker logs` para acessar todo o histórico de requisições

4. **Intervalo de requisições**: Configurado para 5 segundos. Pode ser ajustado no `docker-compose.yml` modificando o `sleep 5`

## Troubleshooting

### Problema: Container cliente não consegue se conectar ao servidor

**Solução**: Verifique se ambos estão na mesma rede:
```bash
docker network inspect desafio1-network
```

### Problema: Porta 8080 já está em uso

**Solução**: Altere a porta externa no `docker-compose.yml`:
```yaml
ports:
  - "8081:80"  # Usar porta 8081 ao invés de 8080
```

### Problema: Logs não aparecem

**Solução**: Aguarde alguns segundos após iniciar os containers:
```bash
sleep 10 && docker logs desafio1-http-client
```


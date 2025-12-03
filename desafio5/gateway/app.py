from flask import Flask, jsonify, request, Response
from datetime import datetime
import requests
import os
import json

app = Flask(__name__)

SERVICE_NAME = os.getenv('SERVICE_NAME', 'API Gateway')
SERVICE_PORT = int(os.getenv('SERVICE_PORT', 8000))
USERS_SERVICE_URL = os.getenv('USERS_SERVICE_URL', 'http://users-service:5001')
ORDERS_SERVICE_URL = os.getenv('ORDERS_SERVICE_URL', 'http://orders-service:5002')
    
request_counter = {
    'total': 0,
    'users': 0,
    'orders': 0,
    'errors': 0
}

def forward_request(service_url, path, method='GET'):
    try:
        url = f"{service_url}{path}"
        
        request_counter['total'] += 1
        
        if method == 'GET':
            response = requests.get(url, timeout=10)
        elif method == 'POST':
            response = requests.post(
                url, 
                json=request.get_json(),
                headers={'Content-Type': 'application/json'},
                timeout=10
            )
        elif method == 'PUT':
            response = requests.put(
                url,
                json=request.get_json(),
                headers={'Content-Type': 'application/json'},
                timeout=10
            )
        elif method == 'DELETE':
            response = requests.delete(url, timeout=10)
        else:
            return jsonify({'error': 'Método não suportado'}), 405
        
        return Response(
            response.content,
            status=response.status_code,
            content_type='application/json'
        )
    
    except requests.exceptions.Timeout:
        request_counter['errors'] += 1
        return jsonify({
            'error': 'Timeout ao conectar com o serviço',
            'service': service_url,
            'gateway': SERVICE_NAME
        }), 504
    
    except requests.exceptions.ConnectionError:
        request_counter['errors'] += 1
        return jsonify({
            'error': 'Serviço indisponível',
            'service': service_url,
            'gateway': SERVICE_NAME
        }), 503
    
    except Exception as e:
        request_counter['errors'] += 1
        return jsonify({
            'error': f'Erro ao processar requisição: {str(e)}',
            'gateway': SERVICE_NAME
        }), 500

@app.route('/')
def home():
    return jsonify({
        "service": SERVICE_NAME,
        "version": "1.0.0",
        "description": "API Gateway centralizando acesso aos microsserviços",
        "architecture": "Gateway Pattern",
        "managed_services": {
            "users": USERS_SERVICE_URL,
            "orders": ORDERS_SERVICE_URL
        },
        "public_endpoints": {
            "/": "Informações do gateway",
            "/health": "Health check de todos os serviços",
            "/stats": "Estatísticas do gateway",
            "/users": "Gerenciamento de usuários (proxy para Users Service)",
            "/users/<id>": "Operações com usuário específico",
            "/orders": "Gerenciamento de pedidos (proxy para Orders Service)",
            "/orders/<id>": "Operações com pedido específico",
            "/orders/user/<user_id>": "Pedidos de um usuário específico"
        },
        "timestamp": datetime.now().isoformat()
    })

@app.route('/health')
def health():
    health_status = {
        'gateway': 'healthy',
        'timestamp': datetime.now().isoformat()
    }
    
    try:
        response = requests.get(f"{USERS_SERVICE_URL}/health", timeout=3)
        health_status['users_service'] = 'healthy' if response.status_code == 200 else 'unhealthy'
    except:
        health_status['users_service'] = 'unreachable'
    
    try:
        response = requests.get(f"{ORDERS_SERVICE_URL}/health", timeout=3)
        health_status['orders_service'] = 'healthy' if response.status_code == 200 else 'unhealthy'
    except:
        health_status['orders_service'] = 'unreachable'
    
    all_healthy = all(
        v == 'healthy' 
        for k, v in health_status.items() 
        if k not in ['timestamp']
    )
    
    health_status['overall'] = 'healthy' if all_healthy else 'degraded'
    
    status_code = 200 if all_healthy else 503
    return jsonify(health_status), status_code

@app.route('/stats')
def stats():
    return jsonify({
        'gateway': SERVICE_NAME,
        'request_statistics': request_counter,
        'uptime': 'running',
        'managed_services': ['users-service', 'orders-service'],
        'timestamp': datetime.now().isoformat()
    })

# ==================== ROTAS PARA USERS SERVICE ====================

@app.route('/users', methods=['GET', 'POST'])
def users():
    request_counter['users'] += 1
    return forward_request(USERS_SERVICE_URL, '/users', request.method)

@app.route('/users/<user_id>', methods=['GET', 'PUT', 'DELETE'])
def user_detail(user_id):
    request_counter['users'] += 1
    return forward_request(USERS_SERVICE_URL, f'/users/{user_id}', request.method)

@app.route('/users/search/<query>')
def user_search(query):
    request_counter['users'] += 1
    return forward_request(USERS_SERVICE_URL, f'/users/search/{query}', 'GET')

# ==================== ROTAS PARA ORDERS SERVICE ====================

@app.route('/orders', methods=['GET', 'POST'])
def orders():
    request_counter['orders'] += 1
    return forward_request(ORDERS_SERVICE_URL, '/orders', request.method)

@app.route('/orders/<order_id>', methods=['GET', 'PUT', 'DELETE'])
def order_detail(order_id):
    request_counter['orders'] += 1
    return forward_request(ORDERS_SERVICE_URL, f'/orders/{order_id}', request.method)

@app.route('/orders/user/<user_id>')
def orders_by_user(user_id):
    request_counter['orders'] += 1
    return forward_request(ORDERS_SERVICE_URL, f'/orders/user/{user_id}', 'GET')

@app.route('/orders/status/<status>')
def orders_by_status(status):
    request_counter['orders'] += 1
    return forward_request(ORDERS_SERVICE_URL, f'/orders/status/{status}', 'GET')

# ==================== HANDLERS DE ERRO ====================

@app.errorhandler(404)
def not_found(error):

    return jsonify({
        "gateway": SERVICE_NAME,
        "error": "Endpoint não encontrado no gateway",
        "path": request.path,
        "timestamp": datetime.now().isoformat()
    }), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({
        "gateway": SERVICE_NAME,
        "error": "Erro interno do gateway",
        "timestamp": datetime.now().isoformat()
    }), 500

if __name__ == '__main__':
    print("=" * 70)
    print(f"Iniciando {SERVICE_NAME}")
    print("=" * 70)
    print(f"Porta: {SERVICE_PORT}")
    print(f"Roteamento:")
    print(f"   /users/*      → {USERS_SERVICE_URL}")
    print(f"   /orders/*     → {ORDERS_SERVICE_URL}")
    print(f"Endpoints disponíveis:")
    print(f"   - http://localhost:{SERVICE_PORT}/")
    print(f"   - http://localhost:{SERVICE_PORT}/health")
    print(f"   - http://localhost:{SERVICE_PORT}/stats")
    print(f"   - http://localhost:{SERVICE_PORT}/users")
    print(f"   - http://localhost:{SERVICE_PORT}/orders")
    print("=" * 70)
    
    app.run(host='0.0.0.0', port=SERVICE_PORT, debug=True)


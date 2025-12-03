from flask import Flask, jsonify, request
from datetime import datetime, timedelta
import os
import requests
import random

app = Flask(__name__)

SERVICE_NAME = os.getenv('SERVICE_NAME', 'Orders Service')
SERVICE_PORT = int(os.getenv('SERVICE_PORT', 5002))
USERS_SERVICE_URL = os.getenv('USERS_SERVICE_URL', 'http://users-service:5001')

orders_db = {
    1: {
        "id": 1,
        "user_id": 2,
        "items": ["Notebook Dell", "Mouse Logitech"],
        "total": 3949.80,
        "status": "delivered",
        "created_at": "2023-10-15",
        "updated_at": "2023-10-20"
    },
    2: {
        "id": 2,
        "user_id": 3,
        "items": ["Monitor LG 24\"", "Teclado Mecânico"],
        "total": 1499.80,
        "status": "shipped",
        "created_at": "2023-11-20",
        "updated_at": "2023-11-22"
    },
    3: {
        "id": 3,
        "user_id": 2,
        "items": ["Webcam HD"],
        "total": 299.90,
        "status": "processing",
        "created_at": "2023-11-28",
        "updated_at": "2023-11-28"
    },
}

next_order_id = max(orders_db.keys()) + 1 if orders_db else 1

def get_user_info(user_id):
    try:
        response = requests.get(f"{USERS_SERVICE_URL}/users/{user_id}", timeout=5)
        if response.status_code == 200:
            data = response.json()
            return data.get('user')
        return None
    except:
        return None

@app.route('/')
def home():
    return jsonify({
        "service": SERVICE_NAME,
        "version": "1.0.0",
        "description": "Microsserviço de gerenciamento de pedidos",
        "total_orders": len(orders_db),
        "depends_on": USERS_SERVICE_URL,
        "endpoints": {
            "/": "Informações do serviço",
            "/health": "Health check",
            "/orders": "GET: Lista pedidos | POST: Cria pedido",
            "/orders/<id>": "GET: Obtém | PUT: Atualiza | DELETE: Remove",
            "/orders/user/<user_id>": "Lista pedidos de um usuário",
            "/orders/status/<status>": "Filtra pedidos por status"
        },
        "timestamp": datetime.now().isoformat()
    })

@app.route('/health')
def health():
    users_service_status = "unknown"
    try:
        response = requests.get(f"{USERS_SERVICE_URL}/health", timeout=3)
        users_service_status = "healthy" if response.status_code == 200 else "unhealthy"
    except:
        users_service_status = "unreachable"
    
    return jsonify({
        "status": "healthy",
        "service": SERVICE_NAME,
        "orders_count": len(orders_db),
        "dependencies": {
            "users_service": users_service_status
        },
        "timestamp": datetime.now().isoformat()
    }), 200

@app.route('/orders', methods=['GET'])
def get_orders():
    enriched_orders = []
    
    for order in orders_db.values():
        enriched_order = order.copy()
        
        user_info = get_user_info(order['user_id'])
        if user_info:
            enriched_order['user_name'] = user_info['name']
            enriched_order['user_email'] = user_info['email']
        
        enriched_orders.append(enriched_order)
    
    return jsonify({
        "service": SERVICE_NAME,
        "total_orders": len(enriched_orders),
        "orders": enriched_orders,
        "timestamp": datetime.now().isoformat()
    }), 200

@app.route('/orders', methods=['POST'])
def create_order():
    global next_order_id
    
    data = request.get_json()
    
    if not data or 'user_id' not in data or 'items' not in data or 'total' not in data:
        return jsonify({
            'service': SERVICE_NAME,
            'error': 'user_id, items e total são obrigatórios'
        }), 400
    
    user_info = get_user_info(data['user_id'])
    if not user_info:
        return jsonify({
            'service': SERVICE_NAME,
            'error': f'Usuário {data["user_id"]} não encontrado'
        }), 404
    
    now = datetime.now().strftime("%Y-%m-%d")
    new_order = {
        "id": next_order_id,
        "user_id": data['user_id'],
        "items": data['items'],
        "total": data['total'],
        "status": "pending",
        "created_at": now,
        "updated_at": now
    }
    
    orders_db[next_order_id] = new_order
    next_order_id += 1
    
    enriched_order = new_order.copy()
    enriched_order['user_name'] = user_info['name']
    enriched_order['user_email'] = user_info['email']
    
    return jsonify({
        "service": SERVICE_NAME,
        "message": "Pedido criado com sucesso",
        "order": enriched_order
    }), 201

@app.route('/orders/<int:order_id>', methods=['GET'])
def get_order(order_id):
    order = orders_db.get(order_id)
    
    if not order:
        return jsonify({
            'service': SERVICE_NAME,
            'error': 'Pedido não encontrado',
            'order_id': order_id
        }), 404
    
    enriched_order = order.copy()
    user_info = get_user_info(order['user_id'])
    if user_info:
        enriched_order['user_name'] = user_info['name']
        enriched_order['user_email'] = user_info['email']
    
    return jsonify({
        "service": SERVICE_NAME,
        "order": enriched_order,
        "timestamp": datetime.now().isoformat()
    }), 200

@app.route('/orders/<int:order_id>', methods=['PUT'])
def update_order(order_id):
    order = orders_db.get(order_id)
    
    if not order:
        return jsonify({
            'service': SERVICE_NAME,
            'error': 'Pedido não encontrado',
            'order_id': order_id
        }), 404
    
    data = request.get_json()
    
    if not data:
        return jsonify({
            'service': SERVICE_NAME,
            'error': 'Dados inválidos'
        }), 400
    
    if 'items' in data:
        order['items'] = data['items']
    if 'total' in data:
        order['total'] = data['total']
    if 'status' in data:
        order['status'] = data['status']
    
    order['updated_at'] = datetime.now().strftime("%Y-%m-%d")
    
    return jsonify({
        "service": SERVICE_NAME,
        "message": "Pedido atualizado com sucesso",
        "order": order
    }), 200

@app.route('/orders/<int:order_id>', methods=['DELETE'])
def delete_order(order_id):
    order = orders_db.get(order_id)
    
    if not order:
        return jsonify({
            'service': SERVICE_NAME,
            'error': 'Pedido não encontrado',
            'order_id': order_id
        }), 404
    
    del orders_db[order_id]
    
    return jsonify({
        "service": SERVICE_NAME,
        "message": "Pedido removido com sucesso",
        "order_id": order_id
    }), 200

@app.route('/orders/user/<int:user_id>')
def get_orders_by_user(user_id):
    user_info = get_user_info(user_id)
    if not user_info:
        return jsonify({
            'service': SERVICE_NAME,
            'error': f'Usuário {user_id} não encontrado',
            'user_id': user_id
        }), 404
    
    user_orders = [order for order in orders_db.values() if order['user_id'] == user_id]
    
    for order in user_orders:
        order['user_name'] = user_info['name']
        order['user_email'] = user_info['email']
    
    total_value = sum(order['total'] for order in user_orders)
    
    return jsonify({
        "service": SERVICE_NAME,
        "user_id": user_id,
        "user_name": user_info['name'],
        "total_orders": len(user_orders),
        "total_value": total_value,
        "orders": user_orders,
        "timestamp": datetime.now().isoformat()
    }), 200

@app.route('/orders/status/<status>')
def get_orders_by_status(status):
    filtered_orders = [
        order for order in orders_db.values() 
        if order['status'] == status
    ]
    
    for order in filtered_orders:
        user_info = get_user_info(order['user_id'])
        if user_info:
            order['user_name'] = user_info['name']
    
    return jsonify({
        "service": SERVICE_NAME,
        "status_filter": status,
        "total_orders": len(filtered_orders),
        "orders": filtered_orders,
        "timestamp": datetime.now().isoformat()
    }), 200

@app.errorhandler(404)
def not_found(error):
    return jsonify({
        "service": SERVICE_NAME,
        "error": "Endpoint não encontrado",
        "timestamp": datetime.now().isoformat()
    }), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({
        "service": SERVICE_NAME,
        "error": "Erro interno do servidor",
        "timestamp": datetime.now().isoformat()
    }), 500

if __name__ == '__main__':
    print("=" * 60)
    print(f" Iniciando {SERVICE_NAME}")
    print("=" * 60)
    print(f"Total de pedidos: {len(orders_db)}")
    print(f"Porta: {SERVICE_PORT}")
    print(f"Consome: {USERS_SERVICE_URL}")
    print(f"Acesso via Gateway na porta 8000")
    print("=" * 60)
    
    app.run(host='0.0.0.0', port=SERVICE_PORT, debug=True)


from flask import Flask, jsonify, request
from datetime import datetime
import os

app = Flask(__name__)

SERVICE_NAME = os.getenv('SERVICE_NAME', 'Users Service')
SERVICE_PORT = int(os.getenv('SERVICE_PORT', 5001))

users_db = {
    1: {
        "id": 1,
        "name": "Ana Silva",
        "email": "ana.silva@example.com",
        "role": "admin",
        "created_at": "2023-01-10"
    },
    2: {
        "id": 2,
        "name": "Bruno Costa",
        "email": "bruno.costa@example.com",
        "role": "customer",
        "created_at": "2023-02-15"
    },
    3: {
        "id": 3,
        "name": "Carla Mendes",
        "email": "carla.mendes@example.com",
        "role": "customer",
        "created_at": "2023-03-20"
    }
}

next_user_id = max(users_db.keys()) + 1 if users_db else 1

@app.route('/')
def home():
    return jsonify({
        "service": SERVICE_NAME,
        "version": "1.0.0",
        "description": "Microsserviço de gerenciamento de usuários",
        "total_users": len(users_db),
        "endpoints": {
            "/": "Informações do serviço",
            "/health": "Health check",
            "/users": "GET: Lista usuários | POST: Cria usuário",
            "/users/<id>": "GET: Obtém | PUT: Atualiza | DELETE: Remove",
            "/users/search/<query>": "Busca usuários por nome ou email"
        },
        "timestamp": datetime.now().isoformat()
    })

@app.route('/health')
def health():
    return jsonify({
        "status": "healthy",
        "service": SERVICE_NAME,
        "users_count": len(users_db),
        "timestamp": datetime.now().isoformat()
    }), 200

@app.route('/users', methods=['GET'])
def get_users():
    return jsonify({
        "service": SERVICE_NAME,
        "total_users": len(users_db),
        "users": list(users_db.values()),
        "timestamp": datetime.now().isoformat()
    }), 200

@app.route('/users', methods=['POST'])
def create_user():
    global next_user_id
    
    data = request.get_json()
    
    if not data or 'name' not in data or 'email' not in data:
        return jsonify({
            'service': SERVICE_NAME,
            'error': 'Nome e email são obrigatórios'
        }), 400
    
    for user in users_db.values():
        if user['email'] == data['email']:
            return jsonify({
                'service': SERVICE_NAME,
                'error': 'Email já cadastrado'
            }), 409
    
    new_user = {
        "id": next_user_id,
        "name": data['name'],
        "email": data['email'],
        "role": data.get('role', 'customer'),
        "created_at": datetime.now().strftime("%Y-%m-%d")
    }
    
    users_db[next_user_id] = new_user
    next_user_id += 1
    
    return jsonify({
        "service": SERVICE_NAME,
        "message": "Usuário criado com sucesso",
        "user": new_user
    }), 201

@app.route('/users/<int:user_id>', methods=['GET'])
def get_user(user_id):
    user = users_db.get(user_id)
    
    if not user:
        return jsonify({
            'service': SERVICE_NAME,
            'error': 'Usuário não encontrado',
            'user_id': user_id
        }), 404
    
    return jsonify({
        "service": SERVICE_NAME,
        "user": user,
        "timestamp": datetime.now().isoformat()
    }), 200

@app.route('/users/<int:user_id>', methods=['PUT'])
def update_user(user_id):
    user = users_db.get(user_id)
    
    if not user:
        return jsonify({
            'service': SERVICE_NAME,
            'error': 'Usuário não encontrado',
            'user_id': user_id
        }), 404
    
    data = request.get_json()
    
    if not data:
        return jsonify({
            'service': SERVICE_NAME,
            'error': 'Dados inválidos'
        }), 400
    
    if 'name' in data:
        user['name'] = data['name']
    if 'email' in data:
        for uid, u in users_db.items():
            if uid != user_id and u['email'] == data['email']:
                return jsonify({
                    'service': SERVICE_NAME,
                    'error': 'Email já cadastrado'
                }), 409
        user['email'] = data['email']
    if 'role' in data:
        user['role'] = data['role']
    
    return jsonify({
        "service": SERVICE_NAME,
        "message": "Usuário atualizado com sucesso",
        "user": user
    }), 200

@app.route('/users/<int:user_id>', methods=['DELETE'])
def delete_user(user_id):
    user = users_db.get(user_id)
    
    if not user:
        return jsonify({
            'service': SERVICE_NAME,
            'error': 'Usuário não encontrado',
            'user_id': user_id
        }), 404
    
    del users_db[user_id]
    
    return jsonify({
        "service": SERVICE_NAME,
        "message": "Usuário removido com sucesso",
        "user_id": user_id
    }), 200

@app.route('/users/search/<query>')
def search_users(query):
    query_lower = query.lower()
    
    results = [
        user for user in users_db.values()
        if query_lower in user['name'].lower() or query_lower in user['email'].lower()
    ]
    
    return jsonify({
        "service": SERVICE_NAME,
        "query": query,
        "total_results": len(results),
        "users": results,
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
    print(f"Total de usuários: {len(users_db)}")
    print(f"Porta: {SERVICE_PORT}")
    print(f"Acesso via Gateway na porta 8000")
    print("=" * 60)
    
    app.run(host='0.0.0.0', port=SERVICE_PORT, debug=True)


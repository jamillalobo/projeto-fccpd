from flask import Flask, jsonify
from datetime import datetime, timedelta
import random
import os

app = Flask(__name__)

SERVICE_NAME = os.getenv('SERVICE_NAME', 'Service-A')
SERVICE_PORT = int(os.getenv('SERVICE_PORT', 5001))

USERS_DATABASE = [
    {
        "id": 1,
        "name": "Alice Silva",
        "email": "alice.silva@example.com",
        "status": "active",
        "role": "admin",
        "registration_date": "2023-01-15"
    },
    {
        "id": 2,
        "name": "Bruno Santos",
        "email": "bruno.santos@example.com",
        "status": "active",
        "role": "user",
        "registration_date": "2023-03-22"
    },
    {
        "id": 3,
        "name": "Carla Oliveira",
        "email": "carla.oliveira@example.com",
        "status": "active",
        "role": "user",
        "registration_date": "2023-05-10"
    },
    {
        "id": 4,
        "name": "Daniel Costa",
        "email": "daniel.costa@example.com",
        "status": "inactive",
        "role": "user",
        "registration_date": "2022-11-05"
    },
    {
        "id": 5,
        "name": "Eva Martins",
        "email": "eva.martins@example.com",
        "status": "active",
        "role": "moderator",
        "registration_date": "2023-07-18"
    },
    {
        "id": 6,
        "name": "Felipe Almeida",
        "email": "felipe.almeida@example.com",
        "status": "active",
        "role": "user",
        "registration_date": "2023-09-03"
    },
    {
        "id": 7,
        "name": "Gabriela Rocha",
        "email": "gabriela.rocha@example.com",
        "status": "active",
        "role": "user",
        "registration_date": "2023-02-14"
    },
    {
        "id": 8,
        "name": "Henrique Lima",
        "email": "henrique.lima@example.com",
        "status": "suspended",
        "role": "user",
        "registration_date": "2022-12-20"
    }
]

@app.route('/')
def home():
    return jsonify({
        "service": SERVICE_NAME,
        "version": "1.0.0",
        "description": "Microsserviço que fornece informações de usuários",
        "endpoints": {
            "/": "Informações do serviço",
            "/health": "Health check",
            "/users": "Lista todos os usuários",
            "/users/<id>": "Obtém usuário específico por ID",
            "/users/status/<status>": "Filtra usuários por status",
            "/stats": "Estatísticas de usuários"
        },
        "timestamp": datetime.now().isoformat()
    })

@app.route('/health')
def health():
    return jsonify({
        "status": "healthy",
        "service": SERVICE_NAME,
        "timestamp": datetime.now().isoformat(),
        "uptime": "running"
    }), 200

@app.route('/users')
def get_users():
    return jsonify({
        "service": SERVICE_NAME,
        "total_users": len(USERS_DATABASE),
        "users": USERS_DATABASE,
        "timestamp": datetime.now().isoformat()
    }), 200

@app.route('/users/<int:user_id>')
def get_user(user_id):
    user = next((u for u in USERS_DATABASE if u['id'] == user_id), None)
    
    if user:
        return jsonify({
            "service": SERVICE_NAME,
            "user": user,
            "timestamp": datetime.now().isoformat()
        }), 200
    else:
        return jsonify({
            "service": SERVICE_NAME,
            "error": "Usuário não encontrado",
            "user_id": user_id,
            "timestamp": datetime.now().isoformat()
        }), 404

@app.route('/users/status/<status>')
def get_users_by_status(status):
    filtered_users = [u for u in USERS_DATABASE if u['status'] == status]
    
    return jsonify({
        "service": SERVICE_NAME,
        "status_filter": status,
        "total_users": len(filtered_users),
        "users": filtered_users,
        "timestamp": datetime.now().isoformat()
    }), 200

@app.route('/stats')
def get_stats():

    status_count = {}
    role_count = {}
    
    for user in USERS_DATABASE:
        status = user['status']
        status_count[status] = status_count.get(status, 0) + 1
        
        role = user['role']
        role_count[role] = role_count.get(role, 0) + 1
    
    return jsonify({
        "service": SERVICE_NAME,
        "statistics": {
            "total_users": len(USERS_DATABASE),
            "by_status": status_count,
            "by_role": role_count
        },
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
    print(f"Iniciando {SERVICE_NAME}")
    print("=" * 60)
    print(f"Total de usuários: {len(USERS_DATABASE)}")
    print(f"Porta: {SERVICE_PORT}")
    print(f"Endpoints disponíveis:")
    print(f"   - http://localhost:{SERVICE_PORT}/")
    print(f"   - http://localhost:{SERVICE_PORT}/users")
    print(f"   - http://localhost:{SERVICE_PORT}/users/<id>")
    print(f"   - http://localhost:{SERVICE_PORT}/users/status/<status>")
    print(f"   - http://localhost:{SERVICE_PORT}/stats")
    print("=" * 60)
    
    app.run(host='0.0.0.0', port=SERVICE_PORT, debug=True)



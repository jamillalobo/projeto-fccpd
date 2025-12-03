from flask import Flask, jsonify
from datetime import datetime, timedelta
import requests
import os
from dateutil import parser
from dateutil.relativedelta import relativedelta

app = Flask(__name__)


SERVICE_NAME = os.getenv('SERVICE_NAME', 'Service-B')
SERVICE_PORT = int(os.getenv('SERVICE_PORT', 5002))
SERVICE_A_URL = os.getenv('SERVICE_A_URL', 'http://service-a:5001')

def calculate_time_since(date_string):

    try:
        registration_date = parser.parse(date_string)
        now = datetime.now()

        diff = relativedelta(now, registration_date)

        parts = []
        if diff.years > 0:
            parts.append(f"{diff.years} ano{'s' if diff.years != 1 else ''}")
        if diff.months > 0:
            parts.append(f"{diff.months} mês{'es' if diff.months != 1 else ''}")
        if diff.days > 0 and not parts:  # Só mostrar dias se não houver anos/meses
            parts.append(f"{diff.days} dia{'s' if diff.days != 1 else ''}")
        
        if not parts:
            return "hoje"
        
        return ", ".join(parts)
    except:
        return "data desconhecida"

def fetch_users_from_service_a():
    try:
        response = requests.get(f"{SERVICE_A_URL}/users", timeout=5)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Erro ao conectar com Service A: {e}")
        return None

def fetch_user_by_id_from_service_a(user_id):
    try:
        response = requests.get(f"{SERVICE_A_URL}/users/{user_id}", timeout=5)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Erro ao conectar com Service A: {e}")
        return None

@app.route('/')
def home():
    return jsonify({
        "service": SERVICE_NAME,
        "version": "1.0.0",
        "description": "Microsserviço que agrega e exibe informações de usuários do Service A",
        "consumes": SERVICE_A_URL,
        "endpoints": {
            "/": "Informações do serviço",
            "/health": "Health check",
            "/user-info": "Lista usuários com informações formatadas",
            "/user-info/<id>": "Informações formatadas de usuário específico",
            "/active-users": "Lista apenas usuários ativos com tempo de registro",
            "/summary": "Resumo executivo de todos os usuários"
        },
        "timestamp": datetime.now().isoformat()
    })

@app.route('/health')
def health():
    service_a_status = "unknown"
    
    try:
        response = requests.get(f"{SERVICE_A_URL}/health", timeout=3)
        if response.status_code == 200:
            service_a_status = "healthy"
        else:
            service_a_status = "unhealthy"
    except:
        service_a_status = "unreachable"
    
    all_healthy = service_a_status == "healthy"
    
    return jsonify({
        "status": "healthy" if all_healthy else "degraded",
        "service": SERVICE_NAME,
        "dependencies": {
            "service-a": service_a_status
        },
        "timestamp": datetime.now().isoformat()
    }), 200 if all_healthy else 503

@app.route('/user-info')
def get_user_info():
    data = fetch_users_from_service_a()
    
    if not data:
        return jsonify({
            "service": SERVICE_NAME,
            "error": "Não foi possível conectar ao Service A",
            "timestamp": datetime.now().isoformat()
        }), 503
    
    formatted_users = []
    for user in data.get('users', []):
        time_since = calculate_time_since(user['registration_date'])
        
        status_emoji = {
            'active': '✅',
            'inactive': '⏸️',
            'suspended': '🚫'
        }.get(user['status'], '❓')
        
        role_emoji = {
            'admin': '👑',
            'moderator': '🛡️',
            'user': '👤'
        }.get(user['role'], '👤')
        
        formatted_info = (
            f"{status_emoji} Usuário {user['name']} ({role_emoji} {user['role']}) "
            f"está {user['status']} desde {time_since} atrás"
        )
        
        formatted_users.append({
            "id": user['id'],
            "name": user['name'],
            "email": user['email'],
            "status": user['status'],
            "role": user['role'],
            "registration_date": user['registration_date'],
            "time_since_registration": time_since,
            "formatted_message": formatted_info
        })
    
    return jsonify({
        "service": SERVICE_NAME,
        "source": "Service A",
        "total_users": len(formatted_users),
        "users": formatted_users,
        "timestamp": datetime.now().isoformat()
    }), 200

@app.route('/user-info/<int:user_id>')
def get_single_user_info(user_id):
    data = fetch_user_by_id_from_service_a(user_id)
    
    if not data:
        return jsonify({
            "service": SERVICE_NAME,
            "error": "Não foi possível conectar ao Service A",
            "timestamp": datetime.now().isoformat()
        }), 503
    
    if 'error' in data:
        return jsonify({
            "service": SERVICE_NAME,
            "error": data['error'],
            "user_id": user_id,
            "timestamp": datetime.now().isoformat()
        }), 404
    
    user = data.get('user', {})
    time_since = calculate_time_since(user['registration_date'])
    
    status_emoji = {
        'active': '✅',
        'inactive': '⏸️',
        'suspended': '🚫'
    }.get(user['status'], '❓')
    
    role_emoji = {
        'admin': '👑',
        'moderator': '🛡️',
        'user': '👤'
    }.get(user['role'], '👤')
    
    formatted_info = (
        f"{status_emoji} Usuário {user['name']} ({role_emoji} {user['role']}) "
        f"está {user['status']} desde {time_since} atrás"
    )
    
    return jsonify({
        "service": SERVICE_NAME,
        "source": "Service A",
        "user": {
            "id": user['id'],
            "name": user['name'],
            "email": user['email'],
            "status": user['status'],
            "role": user['role'],
            "registration_date": user['registration_date'],
            "time_since_registration": time_since,
            "formatted_message": formatted_info
        },
        "timestamp": datetime.now().isoformat()
    }), 200

@app.route('/active-users')
def get_active_users():
    data = fetch_users_from_service_a()
    
    if not data:
        return jsonify({
            "service": SERVICE_NAME,
            "error": "Não foi possível conectar ao Service A",
            "timestamp": datetime.now().isoformat()
        }), 503
    
    active_users = []
    for user in data.get('users', []):
        if user['status'] == 'active':
            time_since = calculate_time_since(user['registration_date'])
            
            active_users.append({
                "name": user['name'],
                "email": user['email'],
                "role": user['role'],
                "message": f"✅ {user['name']} ativo desde {time_since}"
            })
    
    return jsonify({
        "service": SERVICE_NAME,
        "source": "Service A",
        "total_active": len(active_users),
        "active_users": active_users,
        "timestamp": datetime.now().isoformat()
    }), 200

@app.route('/summary')
def get_summary():
    data = fetch_users_from_service_a()
    
    if not data:
        return jsonify({
            "service": SERVICE_NAME,
            "error": "Não foi possível conectar ao Service A",
            "timestamp": datetime.now().isoformat()
        }), 503
    
    users = data.get('users', [])
    
    status_count = {}
    role_count = {}
    oldest_user = None
    newest_user = None
    
    for user in users:
        status = user['status']
        status_count[status] = status_count.get(status, 0) + 1
        
        role = user['role']
        role_count[role] = role_count.get(role, 0) + 1
        
        reg_date = parser.parse(user['registration_date'])
        if not oldest_user or reg_date < parser.parse(oldest_user['registration_date']):
            oldest_user = user
        if not newest_user or reg_date > parser.parse(newest_user['registration_date']):
            newest_user = user
    
    summary_messages = []
    for user in users:
        time_since = calculate_time_since(user['registration_date'])
        summary_messages.append(
            f"{user['name']} ({user['status']}) - registrado há {time_since}"
        )
    
    return jsonify({
        "service": SERVICE_NAME,
        "source": "Service A",
        "summary": {
            "total_users": len(users),
            "by_status": status_count,
            "by_role": role_count,
            "oldest_user": {
                "name": oldest_user['name'] if oldest_user else None,
                "registered": calculate_time_since(oldest_user['registration_date']) if oldest_user else None
            },
            "newest_user": {
                "name": newest_user['name'] if newest_user else None,
                "registered": calculate_time_since(newest_user['registration_date']) if newest_user else None
            }
        },
        "all_users_summary": summary_messages,
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
    print(f"Porta: {SERVICE_PORT}")
    print(f"Consome dados de: {SERVICE_A_URL}")
    print(f"Endpoints disponíveis:")
    print(f"   - http://localhost:{SERVICE_PORT}/")
    print(f"   - http://localhost:{SERVICE_PORT}/user-info")
    print(f"   - http://localhost:{SERVICE_PORT}/user-info/<id>")
    print(f"   - http://localhost:{SERVICE_PORT}/active-users")
    print(f"   - http://localhost:{SERVICE_PORT}/summary")
    print("=" * 60)
    
    app.run(host='0.0.0.0', port=SERVICE_PORT, debug=True)



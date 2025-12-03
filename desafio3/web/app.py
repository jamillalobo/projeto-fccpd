from flask import Flask, jsonify, request
import psycopg2
import redis
import os
import time
import json
from datetime import datetime

app = Flask(__name__)


DATABASE_URL = os.getenv('DATABASE_URL')
REDIS_HOST = os.getenv('REDIS_HOST', 'cache')
REDIS_PORT = int(os.getenv('REDIS_PORT', 6379))
API_SECRET_KEY = os.getenv('API_SECRET_KEY')


def get_db_connection():

    try:
        conn = psycopg2.connect(DATABASE_URL)
        return conn
    except Exception as e:
        print(f"Erro ao conectar ao banco de dados: {e}")
        return None

def get_redis_connection():
    try:
        r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)
        r.ping()
        return r
    except Exception as e:
        print(f"Erro ao conectar ao Redis: {e}")
        return None


redis_client = get_redis_connection()

@app.route('/')
def home():
    return jsonify({
        'status': 'running',
        'message': 'API Multi-Serviços',
        'timestamp': datetime.now().isoformat(),
        'endpoints': {
            '/health': 'Verificar saúde dos serviços',
            '/users': 'GET: Listar usuários | POST: Criar usuário',
            '/users/<id>': 'GET: Obter usuário por ID',
            '/stats': 'Obter estatísticas de acesso',
            '/cache/test': 'Testar operações de cache'
        }
    })

@app.route('/health')
def health():
    health_status = {
        'web': 'healthy',
        'timestamp': datetime.now().isoformat()
    }
    
    try:
        conn = get_db_connection()
        if conn:
            cursor = conn.cursor()
            cursor.execute('SELECT 1')
            cursor.close()
            conn.close()
            health_status['database'] = 'healthy'
        else:
            health_status['database'] = 'unhealthy'
    except Exception as e:
        health_status['database'] = f'unhealthy: {str(e)}'
    
    try:
        if redis_client:
            redis_client.ping()
            health_status['cache'] = 'healthy'
        else:
            health_status['cache'] = 'unhealthy'
    except Exception as e:
        health_status['cache'] = f'unhealthy: {str(e)}'
    
    if redis_client:
        redis_client.incr('health_checks')
        health_status['total_health_checks'] = redis_client.get('health_checks')
    
    all_healthy = all(
        v == 'healthy' 
        for k, v in health_status.items() 
        if k not in ['timestamp', 'total_health_checks']
    )
    
    status_code = 200 if all_healthy else 503
    return jsonify(health_status), status_code

@app.route('/users', methods=['GET', 'POST'])
def users():
    
    if request.method == 'GET':
        cached_users = None
        if redis_client:
            cached_users = redis_client.get('users_list')
            if cached_users:
                redis_client.incr('cache_hits')
                return jsonify({
                    'source': 'cache',
                    'users': json.loads(cached_users),
                    'cached_at': redis_client.get('users_list_timestamp')
                })
        
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute('SELECT id, name, email, created_at FROM users ORDER BY id')
            users_data = cursor.fetchall()
            cursor.close()
            conn.close()
            
            users_list = [
                {
                    'id': row[0],
                    'name': row[1],
                    'email': row[2],
                    'created_at': row[3].isoformat() if row[3] else None
                }
                for row in users_data
            ]
            
            if redis_client:
                redis_client.setex(
                    'users_list', 
                        60,
                    json.dumps(users_list)
                )
                redis_client.set('users_list_timestamp', datetime.now().isoformat())
                redis_client.incr('cache_misses')
            
            return jsonify({
                'source': 'database',
                'users': users_list
            })
            
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    elif request.method == 'POST':
        data = request.get_json()
        
        if not data or 'name' not in data or 'email' not in data:
            return jsonify({'error': 'Nome e email são obrigatórios'}), 400
        
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute(
                'INSERT INTO users (name, email) VALUES (%s, %s) RETURNING id, name, email, created_at',
                (data['name'], data['email'])
            )
            new_user = cursor.fetchone()
            conn.commit()
            cursor.close()
            conn.close()
            
            if redis_client:
                redis_client.delete('users_list')
                redis_client.incr('users_created')
            
            return jsonify({
                'message': 'Usuário criado com sucesso',
                'user': {
                    'id': new_user[0],
                    'name': new_user[1],
                    'email': new_user[2],
                    'created_at': new_user[3].isoformat()
                }
            }), 201
            
        except Exception as e:
            return jsonify({'error': str(e)}), 500

@app.route('/users/<int:user_id>')
def get_user(user_id):
    
    cache_key = f'user:{user_id}'
    if redis_client:
        cached_user = redis_client.get(cache_key)
        if cached_user:
            redis_client.incr('cache_hits')
            return jsonify({
                'source': 'cache',
                'user': json.loads(cached_user)
            })
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT id, name, email, created_at FROM users WHERE id = %s', (user_id,))
        user_data = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if not user_data:
            return jsonify({'error': 'Usuário não encontrado'}), 404
        
        user = {
            'id': user_data[0],
            'name': user_data[1],
            'email': user_data[2],
            'created_at': user_data[3].isoformat()
        }
        
        if redis_client:
            redis_client.setex(cache_key, 300, json.dumps(user))
            redis_client.incr('cache_misses')
        
        return jsonify({
            'source': 'database',
            'user': user
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/stats')
def stats():
    
    if not redis_client:
        return jsonify({'error': 'Redis não disponível'}), 503
    
    try:
        statistics = {
            'health_checks': redis_client.get('health_checks') or 0,
            'cache_hits': redis_client.get('cache_hits') or 0,
            'cache_misses': redis_client.get('cache_misses') or 0,
            'users_created': redis_client.get('users_created') or 0,
            'timestamp': datetime.now().isoformat()
        }
        
        hits = int(statistics['cache_hits'])
        misses = int(statistics['cache_misses'])
        total = hits + misses
        
        if total > 0:
            statistics['cache_hit_rate'] = f"{(hits / total * 100):.2f}%"
        else:
            statistics['cache_hit_rate'] = "N/A"
        
        return jsonify(statistics)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/cache/test')
def test_cache():
    
    if not redis_client:
        return jsonify({'error': 'Redis não disponível'}), 503
    
    try:
        test_key = 'test_key'
        test_value = f'test_value_{int(time.time())}'

        redis_client.set(test_key, test_value)
        
        retrieved_value = redis_client.get(test_key)
        
        redis_client.setex('temp_key', 10, 'expires_in_10s')
        ttl = redis_client.ttl('temp_key')
        
        return jsonify({
            'message': 'Teste de cache executado com sucesso',
            'operations': {
                'set': {'key': test_key, 'value': test_value},
                'get': {'key': test_key, 'value': retrieved_value},
                'setex': {'key': 'temp_key', 'ttl_seconds': ttl}
            },
            'cache_info': {
                'keys_count': redis_client.dbsize(),
                'memory_used': redis_client.info('memory')['used_memory_human']
            }
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    print("=" * 50)
    print("Iniciando API Multi-Serviços")
    print("=" * 50)
    print(f"Database URL: {DATABASE_URL}")
    print(f"Redis Host: {REDIS_HOST}:{REDIS_PORT}")
    print(f"API Secret Key: {'*' * len(API_SECRET_KEY) if API_SECRET_KEY else 'Not set'}")
    print("=" * 50)
    
    print("Aguardando serviços...")
    time.sleep(2)
    
    if get_db_connection():
        print("Database conectado")
    else:
        print("Database não conectado")
    
    if redis_client:
        print("Redis conectado")
    else:
        print("Redis não conectado")
    
    print("=" * 50)
    
    app.run(host='0.0.0.0', port=5000, debug=True)


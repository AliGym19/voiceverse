"""Health and monitoring routes - System health, metrics, monitoring"""

from flask import Blueprint, jsonify, request
from datetime import datetime
import time

health_bp = Blueprint('health', __name__)

# Dependencies
db = None
metrics_collector = None

# Track start time
start_time = time.time()

def init_health(database, metrics):
    """Initialize health blueprint with dependencies"""
    global db, metrics_collector
    db = database
    metrics_collector = metrics

@health_bp.route('/health', methods=['GET'])
def health_check():
    """Comprehensive health check endpoint"""
    try:
        health_status = {
            'status': 'healthy',
            'timestamp': datetime.utcnow().isoformat(),
            'uptime_seconds': int(time.time() - start_time),
            'checks': {}
        }

        # Database check
        try:
            users = db.get_all_users()
            health_status['checks']['database'] = {
                'status': 'healthy',
                'user_count': len(users)
            }
        except Exception as e:
            health_status['status'] = 'degraded'
            health_status['checks']['database'] = {
                'status': 'unhealthy',
                'error': str(e)
            }

        # File system check
        try:
            import os
            upload_folder = 'saved_audio'
            if os.path.exists(upload_folder):
                file_count = len([f for f in os.listdir(upload_folder) if f.endswith('.mp3')])
                health_status['checks']['filesystem'] = {
                    'status': 'healthy',
                    'audio_files': file_count
                }
            else:
                health_status['checks']['filesystem'] = {
                    'status': 'warning',
                    'message': 'Upload folder does not exist'
                }
        except Exception as e:
            health_status['checks']['filesystem'] = {
                'status': 'error',
                'error': str(e)
            }

        # OpenAI API check (basic - just check if key is set)
        try:
            import os
            api_key = os.getenv('OPENAI_API_KEY')
            if api_key and len(api_key) > 20:
                health_status['checks']['openai_api'] = {
                    'status': 'configured',
                    'key_length': len(api_key)
                }
            else:
                health_status['status'] = 'degraded'
                health_status['checks']['openai_api'] = {
                    'status': 'not_configured',
                    'message': 'API key not set or invalid'
                }
        except Exception as e:
            health_status['checks']['openai_api'] = {
                'status': 'error',
                'error': str(e)
            }

        status_code = 200 if health_status['status'] == 'healthy' else 503
        return jsonify(health_status), status_code

    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'error': str(e),
            'timestamp': datetime.utcnow().isoformat()
        }), 503

@health_bp.route('/metrics', methods=['GET'])
def metrics_prometheus():
    """Prometheus-compatible metrics endpoint"""
    try:
        if not metrics_collector:
            return "# Metrics collector not initialized\n", 500

        metrics = metrics_collector.get_metrics()

        # Format as Prometheus metrics
        output = []
        output.append("# HELP tts_requests_total Total number of TTS requests")
        output.append("# TYPE tts_requests_total counter")
        output.append(f"tts_requests_total {metrics.get('total_requests', 0)}")

        output.append("# HELP tts_errors_total Total number of errors")
        output.append("# TYPE tts_errors_total counter")
        output.append(f"tts_errors_total {metrics.get('total_errors', 0)}")

        output.append("# HELP tts_latency_seconds Request latency in seconds")
        output.append("# TYPE tts_latency_seconds histogram")
        output.append(f"tts_latency_seconds_sum {metrics.get('total_latency', 0)}")
        output.append(f"tts_latency_seconds_count {metrics.get('total_requests', 0)}")

        return '\n'.join(output) + '\n', 200, {'Content-Type': 'text/plain; charset=utf-8'}

    except Exception as e:
        return f"# Error: {str(e)}\n", 500

@health_bp.route('/metrics/json', methods=['GET'])
def metrics_json():
    """JSON metrics endpoint"""
    try:
        if not metrics_collector:
            return jsonify({'error': 'Metrics collector not initialized'}), 500

        metrics = metrics_collector.get_metrics()
        return jsonify(metrics)

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@health_bp.route('/favicon.ico')
def favicon():
    """Handle favicon requests"""
    return '', 204

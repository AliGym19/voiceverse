#!/usr/bin/env python3
"""
Phase 4 Routes for VoiceVerse
Batch processing, audio enhancement, analytics, and cost estimation endpoints
"""

from flask import jsonify, request, session, send_file
from functools import wraps
import os
import json

# Import Phase 4 features
from features import BatchProcessor, AudioEnhancer, UserAnalytics, CostEstimator


def login_required_phase4(f):
    """Decorator for login requirement"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({'error': 'Authentication required'}), 401
        return f(*args, **kwargs)
    return decorated_function


def init_phase4_routes(app):
    """
    Initialize Phase 4 routes
    Call this function from main app with: init_phase4_routes(app)
    """

    # Initialize Phase 4 components
    batch_processor = BatchProcessor()
    audio_enhancer = AudioEnhancer()
    user_analytics = UserAnalytics()
    cost_estimator = CostEstimator()

    # ========== BATCH PROCESSING ROUTES ==========

    @app.route('/api/batch/create', methods=['POST'])
    @login_required_phase4
    def create_batch_job():
        """Create a new batch TTS job"""
        data = request.get_json()

        if not data or 'name' not in data or 'items' not in data:
            return jsonify({'error': 'Missing required fields: name, items'}), 400

        try:
            job_id = batch_processor.create_batch_job(
                user_id=session['user_id'],
                name=data['name'],
                items=data['items']
            )

            return jsonify({
                'success': True,
                'job_id': job_id,
                'message': f'Batch job created with {len(data["items"])} items'
            }), 201

        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @app.route('/api/batch/<int:job_id>', methods=['GET'])
    @login_required_phase4
    def get_batch_job(job_id):
        """Get batch job details"""
        job = batch_processor.get_batch_job(job_id)

        if not job:
            return jsonify({'error': 'Job not found'}), 404

        if job['user_id'] != session['user_id']:
            return jsonify({'error': 'Unauthorized'}), 403

        items = batch_processor.get_batch_items(job_id)

        return jsonify({
            'job': job,
            'items': items
        })

    @app.route('/api/batch/<int:job_id>/progress', methods=['GET'])
    @login_required_phase4
    def get_batch_progress(job_id):
        """Get batch job progress"""
        progress = batch_processor.get_job_progress(job_id)

        if 'error' in progress:
            return jsonify(progress), 404

        return jsonify(progress)

    @app.route('/api/batch/list', methods=['GET'])
    @login_required_phase4
    def list_batch_jobs():
        """List user's batch jobs"""
        limit = request.args.get('limit', 50, type=int)
        jobs = batch_processor.get_user_jobs(session['user_id'], limit=limit)

        return jsonify({'jobs': jobs})

    @app.route('/api/batch/<int:job_id>', methods=['DELETE'])
    @login_required_phase4
    def delete_batch_job(job_id):
        """Delete a batch job"""
        success, message = batch_processor.delete_batch_job(job_id, session['user_id'])

        if success:
            return jsonify({'success': True, 'message': message})
        else:
            return jsonify({'error': message}), 400

    @app.route('/api/batch/<int:job_id>/export', methods=['GET'])
    @login_required_phase4
    def export_batch_results(job_id):
        """Export batch results as JSON or CSV"""
        format_type = request.args.get('format', 'json')

        export_data = batch_processor.export_batch_results(job_id, format=format_type)

        if not export_data:
            return jsonify({'error': 'Job not found'}), 404

        if format_type == 'csv':
            return export_data, 200, {
                'Content-Type': 'text/csv',
                'Content-Disposition': f'attachment; filename=batch_{job_id}.csv'
            }
        else:
            return export_data, 200, {'Content-Type': 'application/json'}

    # ========== AUDIO ENHANCEMENT ROUTES ==========

    @app.route('/api/audio/filters', methods=['GET'])
    @login_required_phase4
    def get_audio_filters():
        """Get available audio filters"""
        return jsonify({
            'filters': audio_enhancer.get_available_filters(),
            'filter_info': audio_enhancer.get_filter_info()
        })

    @app.route('/api/audio/enhance', methods=['POST'])
    @login_required_phase4
    def enhance_audio():
        """Apply audio enhancement to a file"""
        data = request.get_json()

        if not data or 'file_path' not in data:
            return jsonify({'error': 'Missing file_path'}), 400

        file_path = data['file_path']

        if not os.path.exists(file_path):
            return jsonify({'error': 'File not found'}), 404

        try:
            options = data.get('options', {})
            output_path = audio_enhancer.enhance(file_path, options=options)

            return jsonify({
                'success': True,
                'output_path': output_path,
                'message': 'Audio enhanced successfully'
            })

        except Exception as e:
            return jsonify({'error': str(e)}), 500

    # ========== ANALYTICS ROUTES ==========

    @app.route('/api/analytics/user', methods=['GET'])
    @login_required_phase4
    def get_user_analytics():
        """Get user analytics"""
        days = request.args.get('days', 30, type=int)
        stats = user_analytics.get_user_stats(session['user_id'], days=days)

        return jsonify(stats)

    @app.route('/api/analytics/global', methods=['GET'])
    @login_required_phase4
    def get_global_analytics():
        """Get global platform statistics"""
        days = request.args.get('days', 30, type=int)
        stats = user_analytics.get_global_stats(days=days)

        return jsonify(stats)

    @app.route('/api/analytics/trends', methods=['GET'])
    @login_required_phase4
    def get_usage_trends():
        """Get usage trends"""
        days = request.args.get('days', 30, type=int)
        trends = user_analytics.get_usage_trends(days=days)

        return jsonify(trends)

    # ========== COST ESTIMATION ROUTES ==========

    @app.route('/api/cost/estimate', methods=['POST'])
    @login_required_phase4
    def estimate_cost():
        """Estimate cost for a text"""
        data = request.get_json()

        if not data or 'text' not in data:
            return jsonify({'error': 'Missing text'}), 400

        text = data['text']
        model = data.get('model', 'tts-1')

        cost = cost_estimator.estimate_cost(text, model)

        return jsonify({
            'text_length': len(text),
            'model': model,
            'estimated_cost_usd': round(cost, 6),
            'pricing_per_1k_chars': cost_estimator.PRICING.get(model, 0.015)
        })

    @app.route('/api/cost/user', methods=['GET'])
    @login_required_phase4
    def get_user_costs():
        """Get user's actual costs"""
        days = request.args.get('days', 30, type=int)
        costs = cost_estimator.get_user_costs(session['user_id'], days=days)

        return jsonify(costs)

    @app.route('/api/cost/global', methods=['GET'])
    @login_required_phase4
    def get_global_costs():
        """Get platform-wide costs"""
        days = request.args.get('days', 30, type=int)
        costs = cost_estimator.get_global_costs(days=days)

        return jsonify(costs)

    @app.route('/api/cost/projection', methods=['GET'])
    @login_required_phase4
    def get_cost_projection():
        """Get monthly cost projection"""
        sample_days = request.args.get('sample_days', 7, type=int)
        projection = cost_estimator.project_monthly_cost(days_sample=sample_days)

        return jsonify(projection)

    @app.route('/api/cost/by-user', methods=['GET'])
    @login_required_phase4
    def get_cost_by_user():
        """Get top users by cost"""
        days = request.args.get('days', 30, type=int)
        limit = request.args.get('limit', 10, type=int)

        users = cost_estimator.get_cost_by_user(days=days, limit=limit)

        return jsonify({'top_users': users})

    # ========== ANALYTICS DASHBOARD ROUTE ==========

    @app.route('/analytics/dashboard', methods=['GET'])
    @login_required_phase4
    def analytics_dashboard_page():
        """Analytics dashboard page"""
        html = '''<!DOCTYPE html>
<html>
<head>
    <title>VoiceVerse Analytics</title>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Arial, sans-serif;
            margin: 0;
            padding: 20px;
            background: #f5f5f5;
        }
        .container { max-width: 1400px; margin: 0 auto; }
        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            border-radius: 10px;
            margin-bottom: 30px;
        }
        .header h1 { margin: 0; font-size: 32px; }
        .header p { margin: 10px 0 0 0; opacity: 0.9; }
        .grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        .card {
            background: white;
            padding: 25px;
            border-radius: 10px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }
        .card h2 {
            margin: 0 0 20px 0;
            font-size: 18px;
            color: #333;
            border-bottom: 2px solid #667eea;
            padding-bottom: 10px;
        }
        .stat-row {
            display: flex;
            justify-content: space-between;
            padding: 10px 0;
            border-bottom: 1px solid #eee;
        }
        .stat-row:last-child { border-bottom: none; }
        .stat-label { color: #666; }
        .stat-value { font-weight: bold; color: #333; }
        .big-stat {
            font-size: 36px;
            font-weight: bold;
            color: #667eea;
            margin: 20px 0;
        }
        .refresh-btn {
            background: #667eea;
            color: white;
            border: none;
            padding: 12px 24px;
            border-radius: 6px;
            cursor: pointer;
            font-size: 14px;
            font-weight: bold;
        }
        .refresh-btn:hover { background: #5568d3; }
        .loading { text-align: center; padding: 40px; color: #666; }
        .error { color: #d32f2f; padding: 20px; text-align: center; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Analytics Dashboard</h1>
            <p>Comprehensive usage statistics and insights</p>
            <button class="refresh-btn" onclick="loadData()">Refresh Data</button>
        </div>

        <div id="content">
            <div class="loading">Loading analytics...</div>
        </div>
    </div>

    <script>
        async function loadData() {
            const content = document.getElementById('content');
            content.innerHTML = '<div class="loading">Loading analytics...</div>';

            try {
                const [userStats, costs, trends] = await Promise.all([
                    fetch('/api/analytics/user?days=30').then(r => r.json()),
                    fetch('/api/cost/user?days=30').then(r => r.json()),
                    fetch('/api/analytics/trends?days=30').then(r => r.json())
                ]);

                let html = '<div class="grid">';

                // User TTS Stats
                html += `
                    <div class="card">
                        <h2>TTS Generation Stats (30 Days)</h2>
                        <div class="big-stat">${userStats.tts.total_generations}</div>
                        <div class="stat-row">
                            <span class="stat-label">Total Characters:</span>
                            <span class="stat-value">${(userStats.tts.total_characters || 0).toLocaleString()}</span>
                        </div>
                        <div class="stat-row">
                            <span class="stat-label">Avg Characters/Gen:</span>
                            <span class="stat-value">${userStats.tts.avg_characters_per_generation}</span>
                        </div>
                        <div class="stat-row">
                            <span class="stat-label">Saved Audio:</span>
                            <span class="stat-value">${userStats.saved_audio_count}</span>
                        </div>
                    </div>
                `;

                // Cost Stats
                html += `
                    <div class="card">
                        <h2>Cost Analysis (30 Days)</h2>
                        <div class="big-stat">$${costs.total_cost_usd}</div>
                        <div class="stat-row">
                            <span class="stat-label">Analysis Period:</span>
                            <span class="stat-value">${costs.period_days} days</span>
                        </div>
                `;
                for (const [model, data] of Object.entries(costs.model_breakdown || {})) {
                    html += `
                        <div class="stat-row">
                            <span class="stat-label">${model}:</span>
                            <span class="stat-value">$${data.cost_usd}</span>
                        </div>
                    `;
                }
                html += '</div>';

                // Voice Usage
                html += `
                    <div class="card">
                        <h2>Voice Usage</h2>
                `;
                for (const [voice, count] of Object.entries(userStats.voice_usage || {})) {
                    html += `
                        <div class="stat-row">
                            <span class="stat-label">${voice}:</span>
                            <span class="stat-value">${count} uses</span>
                        </div>
                    `;
                }
                if (Object.keys(userStats.voice_usage || {}).length === 0) {
                    html += '<p>No voice usage data available</p>';
                }
                html += '</div>';

                html += '</div>';
                content.innerHTML = html;

            } catch (error) {
                content.innerHTML = `<div class="error">Error loading analytics: ${error.message}</div>`;
            }
        }

        loadData();
    </script>
</body>
</html>'''
        return html

    print("Phase 4 routes initialized successfully")
    print(f"  - Batch processing: {len([r for r in app.url_map.iter_rules() if 'batch' in r.rule])} routes")
    print(f"  - Audio enhancement: {len([r for r in app.url_map.iter_rules() if 'audio' in r.rule])} routes")
    print(f"  - Analytics: {len([r for r in app.url_map.iter_rules() if 'analytics' in r.rule])} routes")
    print(f"  - Cost estimation: {len([r for r in app.url_map.iter_rules() if 'cost' in r.rule])} routes")

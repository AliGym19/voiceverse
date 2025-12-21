# Phase 4 Integration Guide

## Quick Integration

To integrate Phase 4 features into `tts_app19.py`, add these two lines near the end of the file (before `if __name__ == '__main__':`):

```python
from phase4_routes import init_phase4_routes
init_phase4_routes(app)
```

## Complete Integration Example

Add this code block before the `if __name__ == '__main__':` line:

```python
# Phase 4: Feature Enhancements
try:
    from phase4_routes import init_phase4_routes
    init_phase4_routes(app)
    print("[Phase 4] Feature enhancements loaded successfully")
except ImportError as e:
    print(f"[Phase 4] Warning: Could not load Phase 4 features: {e}")
except Exception as e:
    print(f"[Phase 4] Error initializing Phase 4 features: {e}")
```

## Available Endpoints

### Batch Processing
- `POST /api/batch/create` - Create batch TTS job
- `GET /api/batch/<job_id>` - Get batch job details
- `GET /api/batch/<job_id>/progress` - Get job progress
- `GET /api/batch/list` - List user's batch jobs
- `DELETE /api/batch/<job_id>` - Delete batch job
- `GET /api/batch/<job_id>/export?format=json|csv` - Export results

### Audio Enhancement
- `GET /api/audio/filters` - Get available filters
- `POST /api/audio/enhance` - Apply enhancement

### Analytics
- `GET /api/analytics/user?days=30` - User statistics
- `GET /api/analytics/global?days=30` - Global statistics
- `GET /api/analytics/trends?days=30` - Usage trends
- `GET /analytics/dashboard` - Web dashboard

### Cost Estimation
- `POST /api/cost/estimate` - Estimate cost for text
- `GET /api/cost/user?days=30` - User costs
- `GET /api/cost/global?days=30` - Platform costs
- `GET /api/cost/projection?sample_days=7` - Monthly projection
- `GET /api/cost/by-user?days=30&limit=10` - Top users by cost

## Testing Phase 4 Features

```bash
# Test imports
python3 -c "from features import BatchProcessor, AudioEnhancer, UserAnalytics, CostEstimator; print('All imports successful')"

# Test batch processor
python3 features/batch_processor.py

# Test audio enhancer
python3 features/audio_filters.py

# Test analytics
python3 features/analytics.py
```

## Example Usage

### Create Batch Job (JavaScript)
```javascript
const response = await fetch('/api/batch/create', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({
        name: 'My Batch Job',
        items: [
            {text: 'Hello world', voice: 'alloy', model: 'tts-1', speed: 1.0},
            {text: 'Second item', voice: 'echo', model: 'tts-1', speed: 1.0}
        ]
    })
});
const data = await response.json();
console.log('Job ID:', data.job_id);
```

### Estimate Cost (JavaScript)
```javascript
const response = await fetch('/api/cost/estimate', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({
        text: 'Your text here',
        model: 'tts-1'
    })
});
const data = await response.json();
console.log('Estimated cost:', data.estimated_cost_usd);
```

### Get User Analytics (JavaScript)
```javascript
const response = await fetch('/api/analytics/user?days=30');
const stats = await response.json();
console.log('Total generations:', stats.tts.total_generations);
console.log('Total cost:', stats.total_cost_usd);
```

## Dependencies

All Phase 4 features use only standard library modules and existing dependencies:
- sqlite3 (standard library)
- wave, struct, io (standard library for audio processing)
- collections, datetime, pathlib (standard library)

No additional pip installations required beyond what's already in requirements.txt.

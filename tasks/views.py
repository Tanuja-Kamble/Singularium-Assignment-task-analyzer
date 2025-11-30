import json
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render

from .scoring import analyze_tasks, get_top_suggestions, detect_circular_dependencies


def index(request):
    """Serve the main frontend page with cache control headers."""
    response = render(request, 'index.html')
    response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response['Pragma'] = 'no-cache'
    response['Expires'] = '0'
    return response


@csrf_exempt
@require_http_methods(["POST"])
def analyze_tasks_view(request):
    """
    POST /api/tasks/analyze/
    
    Accept a list of tasks and return them sorted by priority score.
    
    Request body should contain:
    {
        "tasks": [...],  # List of task objects
        "strategy": "smart_balance"  # Optional: sorting strategy
    }
    
    Or just a list of tasks directly:
    [...]
    """
    try:
        body = json.loads(request.body)
        
        if isinstance(body, list):
            tasks = body
            strategy = 'smart_balance'
        elif isinstance(body, dict):
            tasks = body.get('tasks', [])
            strategy = body.get('strategy', 'smart_balance')
        else:
            return JsonResponse({
                'error': 'Invalid request format. Expected a list of tasks or an object with "tasks" key.',
                'example': {
                    'tasks': [
                        {
                            'id': 1,
                            'title': 'Example task',
                            'due_date': '2025-12-01',
                            'importance': 8,
                            'estimated_hours': 2,
                            'dependencies': []
                        }
                    ],
                    'strategy': 'smart_balance'
                }
            }, status=400)
        
        if not tasks:
            return JsonResponse({
                'error': 'No tasks provided.',
                'message': 'Please provide at least one task to analyze.'
            }, status=400)
        
        valid_strategies = ['smart_balance', 'fastest_wins', 'high_impact', 'deadline_driven']
        if strategy not in valid_strategies:
            strategy = 'smart_balance'
        
        circular_warnings = detect_circular_dependencies(tasks)
        
        sorted_tasks = analyze_tasks(tasks, strategy=strategy)
        
        response = {
            'success': True,
            'strategy_used': strategy,
            'total_tasks': len(sorted_tasks),
            'tasks': sorted_tasks
        }
        
        if circular_warnings:
            response['warnings'] = circular_warnings
        
        return JsonResponse(response)
    
    except json.JSONDecodeError:
        return JsonResponse({
            'error': 'Invalid JSON format.',
            'message': 'Please check your JSON syntax and try again.'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'error': 'An error occurred while analyzing tasks.',
            'details': str(e)
        }, status=500)


@csrf_exempt
@require_http_methods(["GET", "POST"])
def suggest_tasks_view(request):
    """
    GET/POST /api/tasks/suggest/
    
    Return the top 3 tasks the user should work on today with explanations.
    
    For GET: Uses sample/demo tasks
    For POST: Analyzes provided tasks and returns top 3 suggestions
    """
    try:
        if request.method == 'POST':
            body = json.loads(request.body)
            
            if isinstance(body, list):
                tasks = body
            elif isinstance(body, dict):
                tasks = body.get('tasks', [])
            else:
                return JsonResponse({
                    'error': 'Invalid request format.'
                }, status=400)
            
            if not tasks:
                return JsonResponse({
                    'error': 'No tasks provided for suggestions.'
                }, status=400)
        else:
            tasks = [
                {
                    'id': 1,
                    'title': 'Complete project documentation',
                    'due_date': '2025-11-30',
                    'importance': 7,
                    'estimated_hours': 3,
                    'dependencies': []
                },
                {
                    'id': 2,
                    'title': 'Fix critical login bug',
                    'due_date': '2025-11-29',
                    'importance': 9,
                    'estimated_hours': 1,
                    'dependencies': []
                },
                {
                    'id': 3,
                    'title': 'Review pull requests',
                    'due_date': '2025-12-05',
                    'importance': 5,
                    'estimated_hours': 2,
                    'dependencies': []
                }
            ]
        
        suggestions = get_top_suggestions(tasks, count=3)
        
        return JsonResponse({
            'success': True,
            'message': 'Here are your top 3 tasks for today:',
            'suggestions': suggestions
        })
    
    except json.JSONDecodeError:
        return JsonResponse({
            'error': 'Invalid JSON format.'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'error': 'An error occurred while generating suggestions.',
            'details': str(e)
        }, status=500)


@csrf_exempt
@require_http_methods(["GET"])
def health_check(request):
    """Simple health check endpoint."""
    return JsonResponse({
        'status': 'healthy',
        'service': 'Smart Task Analyzer API'
    })

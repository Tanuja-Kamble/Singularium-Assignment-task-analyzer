"""
Smart Task Analyzer - Priority Scoring Algorithm

This module contains the core logic for calculating task priority scores.
The algorithm considers multiple factors: urgency, importance, effort, and dependencies.

Algorithm Explanation:
----------------------
1. URGENCY (Weight: High)
   - Overdue tasks get maximum priority boost (+100 points)
   - Tasks due within 1 day: +80 points
   - Tasks due within 3 days: +50 points
   - Tasks due within 7 days: +30 points
   - Tasks due within 14 days: +15 points
   
2. IMPORTANCE (Weight: Medium-High)
   - User-provided rating (1-10) multiplied by 5
   - Maximum contribution: 50 points

3. EFFORT/QUICK WINS (Weight: Low-Medium)
   - Tasks under 2 hours: +15 points (quick wins)
   - Tasks 2-4 hours: +8 points
   - Tasks over 8 hours: -5 points (penalty for large tasks)

4. DEPENDENCIES (Weight: Medium)
   - Tasks that block others: +20 points per dependent task
   - Encourages completing blockers first

Different Strategies:
- smart_balance: Uses all factors with balanced weights
- fastest_wins: Prioritizes low-effort tasks
- high_impact: Prioritizes importance over everything
- deadline_driven: Prioritizes based on due date
"""

from datetime import date, datetime
from typing import Dict, List, Any, Optional


def parse_date(date_value: Any) -> Optional[date]:
    """
    Parse a date from various formats (string, date object, datetime).
    Returns None if parsing fails.
    """
    if date_value is None:
        return None
    
    if isinstance(date_value, date):
        return date_value
    
    if isinstance(date_value, datetime):
        return date_value.date()
    
    if isinstance(date_value, str):
        try:
            return datetime.strptime(date_value, '%Y-%m-%d').date()
        except ValueError:
            try:
                return datetime.strptime(date_value, '%m/%d/%Y').date()
            except ValueError:
                return None
    
    return None


def validate_task(task_data: Dict) -> Dict:
    """
    Validate and normalize task data, handling missing or invalid values.
    Returns a normalized task dictionary with default values for missing fields.
    """
    validated = {
        'title': task_data.get('title', 'Untitled Task'),
        'due_date': parse_date(task_data.get('due_date')),
        'importance': 5,
        'estimated_hours': 1,
        'dependencies': [],
        'id': task_data.get('id'),
        'validation_warnings': []
    }
    
    importance = task_data.get('importance')
    if importance is not None:
        try:
            importance = int(importance)
            if importance < 1:
                importance = 1
                validated['validation_warnings'].append('Importance adjusted to minimum (1)')
            elif importance > 10:
                importance = 10
                validated['validation_warnings'].append('Importance adjusted to maximum (10)')
            validated['importance'] = importance
        except (ValueError, TypeError):
            validated['validation_warnings'].append('Invalid importance value, using default (5)')
    else:
        validated['validation_warnings'].append('Missing importance, using default (5)')
    
    estimated_hours = task_data.get('estimated_hours')
    if estimated_hours is not None:
        try:
            estimated_hours = int(estimated_hours)
            if estimated_hours < 1:
                estimated_hours = 1
            validated['estimated_hours'] = estimated_hours
        except (ValueError, TypeError):
            validated['validation_warnings'].append('Invalid estimated_hours, using default (1)')
    
    dependencies = task_data.get('dependencies', [])
    if isinstance(dependencies, list):
        validated['dependencies'] = dependencies
    else:
        validated['validation_warnings'].append('Invalid dependencies format, using empty list')
    
    if validated['due_date'] is None:
        validated['validation_warnings'].append('Missing or invalid due_date')
    
    return validated


def calculate_urgency_score(due_date: Optional[date], today: date) -> tuple:
    """
    Calculate urgency score based on days until due date.
    Returns (score, explanation).
    """
    if due_date is None:
        return 0, "No due date specified"
    
    days_until_due = (due_date - today).days
    
    if days_until_due < 0:
        days_overdue = abs(days_until_due)
        return 100, f"OVERDUE by {days_overdue} day(s)!"
    elif days_until_due == 0:
        return 90, "Due TODAY!"
    elif days_until_due == 1:
        return 80, "Due tomorrow"
    elif days_until_due <= 3:
        return 50, f"Due in {days_until_due} days"
    elif days_until_due <= 7:
        return 30, f"Due in {days_until_due} days"
    elif days_until_due <= 14:
        return 15, f"Due in {days_until_due} days"
    else:
        return 5, f"Due in {days_until_due} days"


def calculate_importance_score(importance: int) -> tuple:
    """
    Calculate importance score.
    Returns (score, explanation).
    """
    score = importance * 5
    if importance >= 8:
        explanation = f"High importance ({importance}/10)"
    elif importance >= 5:
        explanation = f"Medium importance ({importance}/10)"
    else:
        explanation = f"Low importance ({importance}/10)"
    
    return score, explanation


def calculate_effort_score(estimated_hours: int) -> tuple:
    """
    Calculate effort score (quick wins get bonus).
    Returns (score, explanation).
    """
    if estimated_hours < 2:
        return 15, f"Quick win ({estimated_hours}h)"
    elif estimated_hours <= 4:
        return 8, f"Medium effort ({estimated_hours}h)"
    elif estimated_hours <= 8:
        return 0, f"Standard task ({estimated_hours}h)"
    else:
        return -5, f"Large task ({estimated_hours}h)"


def calculate_dependency_score(task_id: Any, all_tasks: List[Dict]) -> tuple:
    """
    Calculate dependency score based on how many other tasks depend on this one.
    Tasks that block others should be prioritized.
    Returns (score, explanation).
    """
    if task_id is None:
        return 0, "No dependency bonus"
    
    blocking_count = 0
    for task in all_tasks:
        deps = task.get('dependencies', [])
        if task_id in deps:
            blocking_count += 1
    
    if blocking_count > 0:
        score = blocking_count * 20
        return score, f"Blocks {blocking_count} other task(s)"
    
    return 0, "No dependency bonus"


def calculate_task_score(
    task_data: Dict,
    all_tasks: List[Dict] = None,
    strategy: str = 'smart_balance'
) -> Dict:
    """
    Calculate the priority score for a task using the specified strategy.
    
    Strategies:
    - smart_balance: Balanced algorithm considering all factors
    - fastest_wins: Prioritize low-effort tasks
    - high_impact: Prioritize importance over everything
    - deadline_driven: Prioritize based on due date
    
    Returns a dictionary with the task data, score, and explanation breakdown.
    """
    if all_tasks is None:
        all_tasks = []
    
    today = date.today()
    validated_task = validate_task(task_data)
    
    urgency_score, urgency_explanation = calculate_urgency_score(
        validated_task['due_date'], today
    )
    importance_score, importance_explanation = calculate_importance_score(
        validated_task['importance']
    )
    effort_score, effort_explanation = calculate_effort_score(
        validated_task['estimated_hours']
    )
    dependency_score, dependency_explanation = calculate_dependency_score(
        validated_task.get('id'), all_tasks
    )
    
    if strategy == 'fastest_wins':
        total_score = (effort_score * 3) + (urgency_score * 0.5) + (importance_score * 0.3)
        strategy_description = "Prioritizing quick wins"
    elif strategy == 'high_impact':
        total_score = (importance_score * 3) + (urgency_score * 0.5) + (effort_score * 0.2)
        strategy_description = "Prioritizing high-impact tasks"
    elif strategy == 'deadline_driven':
        total_score = (urgency_score * 3) + (importance_score * 0.5) + (effort_score * 0.2)
        strategy_description = "Prioritizing deadlines"
    else:
        total_score = urgency_score + importance_score + effort_score + dependency_score
        strategy_description = "Balanced priority scoring"
    
    priority_level = 'high' if total_score >= 100 else ('medium' if total_score >= 50 else 'low')
    
    explanation_parts = []
    if urgency_score > 0:
        explanation_parts.append(urgency_explanation)
    explanation_parts.append(importance_explanation)
    explanation_parts.append(effort_explanation)
    if dependency_score > 0:
        explanation_parts.append(dependency_explanation)
    
    return {
        'id': validated_task.get('id'),
        'title': validated_task['title'],
        'due_date': validated_task['due_date'].isoformat() if validated_task['due_date'] else None,
        'importance': validated_task['importance'],
        'estimated_hours': validated_task['estimated_hours'],
        'dependencies': validated_task['dependencies'],
        'score': round(total_score, 2),
        'priority_level': priority_level,
        'score_breakdown': {
            'urgency': urgency_score,
            'importance': importance_score,
            'effort': effort_score,
            'dependency': dependency_score
        },
        'explanation': ' | '.join(explanation_parts),
        'strategy': strategy_description,
        'validation_warnings': validated_task['validation_warnings']
    }


def analyze_tasks(tasks: List[Dict], strategy: str = 'smart_balance') -> List[Dict]:
    """
    Analyze a list of tasks and return them sorted by priority score.
    """
    scored_tasks = []
    
    for task in tasks:
        scored_task = calculate_task_score(task, tasks, strategy)
        scored_tasks.append(scored_task)
    
    scored_tasks.sort(key=lambda x: x['score'], reverse=True)
    
    return scored_tasks


def get_top_suggestions(tasks: List[Dict], count: int = 3) -> List[Dict]:
    """
    Get the top N task suggestions with detailed explanations for why they should be worked on first.
    """
    analyzed = analyze_tasks(tasks, strategy='smart_balance')
    top_tasks = analyzed[:count]
    
    suggestions = []
    for i, task in enumerate(top_tasks, 1):
        why_reasons = []
        breakdown = task['score_breakdown']
        
        if breakdown['urgency'] >= 80:
            why_reasons.append("This task is due very soon or overdue")
        elif breakdown['urgency'] >= 30:
            why_reasons.append("This task has an upcoming deadline")
        
        if task['importance'] >= 8:
            why_reasons.append("It has high importance to you")
        
        if breakdown['effort'] >= 10:
            why_reasons.append("It's a quick win that can be completed fast")
        
        if breakdown['dependency'] > 0:
            why_reasons.append("Other tasks are waiting on this one")
        
        if not why_reasons:
            why_reasons.append("It has a balanced priority based on all factors")
        
        suggestion = {
            **task,
            'rank': i,
            'why_work_on_this': why_reasons
        }
        suggestions.append(suggestion)
    
    return suggestions


def detect_circular_dependencies(tasks: List[Dict]) -> List[str]:
    """
    Detect circular dependencies in the task list.
    Returns a list of warning messages if circular dependencies are found.
    """
    warnings = []
    task_ids = {task.get('id') for task in tasks if task.get('id') is not None}
    
    def has_circular_dep(task_id, visited, rec_stack):
        visited.add(task_id)
        rec_stack.add(task_id)
        
        task = next((t for t in tasks if t.get('id') == task_id), None)
        if task:
            for dep_id in task.get('dependencies', []):
                if dep_id not in task_ids:
                    continue
                if dep_id not in visited:
                    if has_circular_dep(dep_id, visited, rec_stack):
                        return True
                elif dep_id in rec_stack:
                    return True
        
        rec_stack.remove(task_id)
        return False
    
    visited = set()
    for task in tasks:
        task_id = task.get('id')
        if task_id and task_id not in visited:
            rec_stack = set()
            if has_circular_dep(task_id, visited, rec_stack):
                warnings.append(f"Circular dependency detected involving task ID: {task_id}")
    
    return warnings

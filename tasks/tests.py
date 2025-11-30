"""
Unit Tests for Smart Task Analyzer Scoring Algorithm

Run tests with: python manage.py test tasks
"""

import unittest
from datetime import date, timedelta
from unittest.mock import patch

from .scoring import (
    parse_date,
    validate_task,
    calculate_urgency_score,
    calculate_importance_score,
    calculate_effort_score,
    calculate_dependency_score,
    calculate_task_score,
    analyze_tasks,
    detect_circular_dependencies,
    get_top_suggestions
)


class TestUrgencyScoring(unittest.TestCase):
    """Test urgency score calculations based on due dates."""
    
    def setUp(self):
        self.today = date.today()
    
    def test_overdue_task_gets_maximum_urgency(self):
        """Overdue tasks should receive 100 points (maximum urgency)."""
        yesterday = self.today - timedelta(days=1)
        score, explanation = calculate_urgency_score(yesterday, self.today)
        
        self.assertEqual(score, 100)
        self.assertIn("OVERDUE", explanation)
    
    def test_due_today_gets_high_urgency(self):
        """Tasks due today should receive 90 points."""
        score, explanation = calculate_urgency_score(self.today, self.today)
        
        self.assertEqual(score, 90)
        self.assertIn("TODAY", explanation)
    
    def test_due_tomorrow_gets_80_points(self):
        """Tasks due tomorrow should receive 80 points."""
        tomorrow = self.today + timedelta(days=1)
        score, explanation = calculate_urgency_score(tomorrow, self.today)
        
        self.assertEqual(score, 80)
        self.assertIn("tomorrow", explanation)
    
    def test_due_in_three_days_gets_50_points(self):
        """Tasks due within 3 days should receive 50 points."""
        in_three_days = self.today + timedelta(days=3)
        score, explanation = calculate_urgency_score(in_three_days, self.today)
        
        self.assertEqual(score, 50)
    
    def test_due_in_seven_days_gets_30_points(self):
        """Tasks due within 7 days should receive 30 points."""
        in_seven_days = self.today + timedelta(days=7)
        score, explanation = calculate_urgency_score(in_seven_days, self.today)
        
        self.assertEqual(score, 30)
    
    def test_no_due_date_gets_zero(self):
        """Tasks without a due date should receive 0 urgency points."""
        score, explanation = calculate_urgency_score(None, self.today)
        
        self.assertEqual(score, 0)
        self.assertIn("No due date", explanation)


class TestImportanceScoring(unittest.TestCase):
    """Test importance score calculations."""
    
    def test_max_importance_gives_50_points(self):
        """Maximum importance (10) should give 50 points."""
        score, explanation = calculate_importance_score(10)
        
        self.assertEqual(score, 50)
        self.assertIn("High importance", explanation)
    
    def test_medium_importance_gives_proportional_points(self):
        """Medium importance (5) should give 25 points."""
        score, explanation = calculate_importance_score(5)
        
        self.assertEqual(score, 25)
        self.assertIn("Medium importance", explanation)
    
    def test_low_importance_gives_proportional_points(self):
        """Low importance (2) should give 10 points."""
        score, explanation = calculate_importance_score(2)
        
        self.assertEqual(score, 10)
        self.assertIn("Low importance", explanation)


class TestEffortScoring(unittest.TestCase):
    """Test effort/quick wins score calculations."""
    
    def test_quick_task_gets_bonus(self):
        """Tasks under 2 hours should get +15 quick win bonus."""
        score, explanation = calculate_effort_score(1)
        
        self.assertEqual(score, 15)
        self.assertIn("Quick win", explanation)
    
    def test_medium_effort_gets_moderate_bonus(self):
        """Tasks 2-4 hours should get +8 points."""
        score, explanation = calculate_effort_score(3)
        
        self.assertEqual(score, 8)
        self.assertIn("Medium effort", explanation)
    
    def test_large_task_gets_penalty(self):
        """Tasks over 8 hours should get -5 penalty."""
        score, explanation = calculate_effort_score(10)
        
        self.assertEqual(score, -5)
        self.assertIn("Large task", explanation)


class TestDependencyScoring(unittest.TestCase):
    """Test dependency score calculations."""
    
    def test_blocking_task_gets_bonus(self):
        """Tasks that block others should get +20 per dependent task."""
        all_tasks = [
            {'id': 1, 'title': 'Task 1', 'dependencies': []},
            {'id': 2, 'title': 'Task 2', 'dependencies': [1]},
            {'id': 3, 'title': 'Task 3', 'dependencies': [1]}
        ]
        
        score, explanation = calculate_dependency_score(1, all_tasks)
        
        self.assertEqual(score, 40)
        self.assertIn("Blocks 2", explanation)
    
    def test_non_blocking_task_gets_no_bonus(self):
        """Tasks that don't block others should get 0 dependency points."""
        all_tasks = [
            {'id': 1, 'title': 'Task 1', 'dependencies': []},
            {'id': 2, 'title': 'Task 2', 'dependencies': []}
        ]
        
        score, explanation = calculate_dependency_score(1, all_tasks)
        
        self.assertEqual(score, 0)


class TestSortingStrategies(unittest.TestCase):
    """Test different sorting strategies produce different results."""
    
    def setUp(self):
        today = date.today()
        self.tasks = [
            {
                'id': 1,
                'title': 'Quick but not important',
                'due_date': (today + timedelta(days=7)).isoformat(),
                'importance': 3,
                'estimated_hours': 1,
                'dependencies': []
            },
            {
                'id': 2,
                'title': 'Very important but slow',
                'due_date': (today + timedelta(days=7)).isoformat(),
                'importance': 10,
                'estimated_hours': 8,
                'dependencies': []
            },
            {
                'id': 3,
                'title': 'Urgent deadline',
                'due_date': today.isoformat(),
                'importance': 5,
                'estimated_hours': 4,
                'dependencies': []
            }
        ]
    
    def test_fastest_wins_prioritizes_quick_tasks(self):
        """Fastest wins strategy should prioritize effort over urgency."""
        tasks_same_urgency = [
            {
                'id': 1,
                'title': 'Quick task',
                'due_date': (date.today() + timedelta(days=7)).isoformat(),
                'importance': 5,
                'estimated_hours': 1,
                'dependencies': []
            },
            {
                'id': 2,
                'title': 'Slow task',
                'due_date': (date.today() + timedelta(days=7)).isoformat(),
                'importance': 5,
                'estimated_hours': 10,
                'dependencies': []
            }
        ]
        result = analyze_tasks(tasks_same_urgency, strategy='fastest_wins')
        
        self.assertEqual(result[0]['title'], 'Quick task')
    
    def test_high_impact_prioritizes_important_tasks(self):
        """High impact strategy should put important task first."""
        result = analyze_tasks(self.tasks, strategy='high_impact')
        
        self.assertEqual(result[0]['title'], 'Very important but slow')
    
    def test_deadline_driven_prioritizes_urgent_tasks(self):
        """Deadline driven strategy should put urgent task first."""
        result = analyze_tasks(self.tasks, strategy='deadline_driven')
        
        self.assertEqual(result[0]['title'], 'Urgent deadline')


class TestEdgeCases(unittest.TestCase):
    """Test edge cases and data validation."""
    
    def test_missing_importance_defaults_to_five(self):
        """Tasks without importance should default to 5."""
        task = {'title': 'Test Task', 'due_date': '2025-12-01'}
        validated = validate_task(task)
        
        self.assertEqual(validated['importance'], 5)
        self.assertTrue(any('Missing importance' in w for w in validated['validation_warnings']))
    
    def test_importance_clamped_to_valid_range(self):
        """Importance should be clamped between 1 and 10."""
        task_too_high = {'title': 'Test', 'importance': 15}
        task_too_low = {'title': 'Test', 'importance': -5}
        
        validated_high = validate_task(task_too_high)
        validated_low = validate_task(task_too_low)
        
        self.assertEqual(validated_high['importance'], 10)
        self.assertEqual(validated_low['importance'], 1)
    
    def test_missing_hours_defaults_to_one(self):
        """Tasks without estimated_hours should default to 1."""
        task = {'title': 'Test Task'}
        validated = validate_task(task)
        
        self.assertEqual(validated['estimated_hours'], 1)
    
    def test_invalid_date_format_handled(self):
        """Invalid date formats should be handled gracefully."""
        task = {'title': 'Test', 'due_date': 'not-a-date'}
        validated = validate_task(task)
        
        self.assertIsNone(validated['due_date'])
        self.assertTrue(any('due_date' in w for w in validated['validation_warnings']))
    
    def test_empty_title_gets_default(self):
        """Tasks without title should get 'Untitled Task'."""
        task = {'importance': 5}
        validated = validate_task(task)
        
        self.assertEqual(validated['title'], 'Untitled Task')


class TestCircularDependencyDetection(unittest.TestCase):
    """Test circular dependency detection."""
    
    def test_simple_circular_dependency_detected(self):
        """Simple A -> B -> A cycle should be detected."""
        tasks = [
            {'id': 1, 'title': 'Task A', 'dependencies': [2]},
            {'id': 2, 'title': 'Task B', 'dependencies': [1]}
        ]
        
        warnings = detect_circular_dependencies(tasks)
        
        self.assertTrue(len(warnings) > 0)
        self.assertTrue(any('Circular dependency' in w for w in warnings))
    
    def test_complex_circular_dependency_detected(self):
        """Complex A -> B -> C -> A cycle should be detected."""
        tasks = [
            {'id': 1, 'title': 'Task A', 'dependencies': [2]},
            {'id': 2, 'title': 'Task B', 'dependencies': [3]},
            {'id': 3, 'title': 'Task C', 'dependencies': [1]}
        ]
        
        warnings = detect_circular_dependencies(tasks)
        
        self.assertTrue(len(warnings) > 0)
    
    def test_no_circular_dependency_no_warnings(self):
        """Valid dependency chain should not produce warnings."""
        tasks = [
            {'id': 1, 'title': 'Task A', 'dependencies': []},
            {'id': 2, 'title': 'Task B', 'dependencies': [1]},
            {'id': 3, 'title': 'Task C', 'dependencies': [2]}
        ]
        
        warnings = detect_circular_dependencies(tasks)
        
        self.assertEqual(len(warnings), 0)


class TestDateParsing(unittest.TestCase):
    """Test date parsing from various formats."""
    
    def test_parse_iso_format(self):
        """ISO format (YYYY-MM-DD) should parse correctly."""
        result = parse_date('2025-12-25')
        
        self.assertEqual(result, date(2025, 12, 25))
    
    def test_parse_us_format(self):
        """US format (MM/DD/YYYY) should parse correctly."""
        result = parse_date('12/25/2025')
        
        self.assertEqual(result, date(2025, 12, 25))
    
    def test_parse_date_object(self):
        """Date object should be returned as-is."""
        input_date = date(2025, 12, 25)
        result = parse_date(input_date)
        
        self.assertEqual(result, input_date)
    
    def test_parse_invalid_returns_none(self):
        """Invalid date string should return None."""
        result = parse_date('invalid-date')
        
        self.assertIsNone(result)


class TestGetTopSuggestions(unittest.TestCase):
    """Test the suggestion generation functionality."""
    
    def test_returns_correct_count(self):
        """Should return the requested number of suggestions."""
        today = date.today()
        tasks = [
            {'id': i, 'title': f'Task {i}', 'due_date': (today + timedelta(days=i)).isoformat(), 'importance': 5}
            for i in range(1, 6)
        ]
        
        suggestions = get_top_suggestions(tasks, count=3)
        
        self.assertEqual(len(suggestions), 3)
    
    def test_suggestions_include_rank(self):
        """Each suggestion should include a rank."""
        today = date.today()
        tasks = [
            {'id': 1, 'title': 'Task 1', 'due_date': today.isoformat(), 'importance': 8}
        ]
        
        suggestions = get_top_suggestions(tasks, count=1)
        
        self.assertEqual(suggestions[0]['rank'], 1)
    
    def test_suggestions_include_reasons(self):
        """Each suggestion should include 'why work on this' reasons."""
        today = date.today()
        tasks = [
            {'id': 1, 'title': 'Urgent Important Task', 'due_date': today.isoformat(), 'importance': 9, 'estimated_hours': 1}
        ]
        
        suggestions = get_top_suggestions(tasks, count=1)
        
        self.assertIn('why_work_on_this', suggestions[0])
        self.assertTrue(len(suggestions[0]['why_work_on_this']) > 0)


if __name__ == '__main__':
    unittest.main()

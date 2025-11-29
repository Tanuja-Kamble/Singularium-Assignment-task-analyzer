from django.db import models


class Task(models.Model):
    """
    Task model representing a task with priority-related fields.
    """
    title = models.CharField(max_length=200)
    due_date = models.DateField()
    importance = models.IntegerField(default=5)
    estimated_hours = models.IntegerField(default=1)
    dependencies = models.JSONField(default=list, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title

    def to_dict(self):
        """Convert model instance to dictionary for API responses."""
        return {
            'id': self.id,
            'title': self.title,
            'due_date': self.due_date.isoformat() if self.due_date else None,
            'importance': self.importance,
            'estimated_hours': self.estimated_hours,
            'dependencies': self.dependencies or [],
        }

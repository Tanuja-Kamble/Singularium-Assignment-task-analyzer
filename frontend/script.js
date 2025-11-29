let pendingTasks = [];
let taskIdCounter = 1;

document.addEventListener('DOMContentLoaded', function() {
    initializeApp();
});

function initializeApp() {
    const today = new Date().toISOString().split('T')[0];
    document.getElementById('dueDate').value = today;

    document.querySelectorAll('.toggle-btn').forEach(btn => {
        btn.addEventListener('click', function() {
            const mode = this.dataset.mode;
            switchInputMode(mode);
        });
    });

    document.getElementById('taskForm').addEventListener('submit', handleFormSubmit);
    document.getElementById('loadJsonBtn').addEventListener('click', loadJsonTasks);
    document.getElementById('analyzeBtn').addEventListener('click', analyzeTasks);
    document.getElementById('suggestBtn').addEventListener('click', getSuggestions);
    document.getElementById('clearBtn').addEventListener('click', clearAll);

    updateTaskList();
    updateAnalyzeButton();
}

function switchInputMode(mode) {
    document.querySelectorAll('.toggle-btn').forEach(btn => {
        btn.classList.toggle('active', btn.dataset.mode === mode);
    });
    document.querySelectorAll('.input-mode').forEach(el => {
        el.classList.toggle('active', el.id === mode + 'Input');
    });
}

function handleFormSubmit(e) {
    e.preventDefault();
    
    const title = document.getElementById('title').value.trim();
    const dueDate = document.getElementById('dueDate').value;
    const importance = parseInt(document.getElementById('importance').value) || 5;
    const estimatedHours = parseInt(document.getElementById('estimatedHours').value) || 1;
    const dependenciesInput = document.getElementById('dependencies').value.trim();
    
    let dependencies = [];
    if (dependenciesInput) {
        dependencies = dependenciesInput.split(',')
            .map(d => parseInt(d.trim()))
            .filter(d => !isNaN(d));
    }

    if (!title || !dueDate) {
        showError('Please fill in all required fields (Title and Due Date)');
        return;
    }

    const task = {
        id: taskIdCounter++,
        title: title,
        due_date: dueDate,
        importance: Math.min(10, Math.max(1, importance)),
        estimated_hours: Math.max(1, estimatedHours),
        dependencies: dependencies
    };

    pendingTasks.push(task);
    updateTaskList();
    updateAnalyzeButton();
    
    document.getElementById('taskForm').reset();
    document.getElementById('dueDate').value = new Date().toISOString().split('T')[0];
    document.getElementById('importance').value = 5;
    document.getElementById('estimatedHours').value = 1;
    
    hideError();
}

function loadJsonTasks() {
    const jsonText = document.getElementById('jsonTextarea').value.trim();
    
    if (!jsonText) {
        showError('Please enter JSON data');
        return;
    }

    try {
        const tasks = JSON.parse(jsonText);
        
        if (!Array.isArray(tasks)) {
            showError('JSON must be an array of tasks');
            return;
        }

        tasks.forEach(task => {
            if (!task.id) {
                task.id = taskIdCounter++;
            } else if (task.id >= taskIdCounter) {
                taskIdCounter = task.id + 1;
            }
            pendingTasks.push(task);
        });

        updateTaskList();
        updateAnalyzeButton();
        hideError();
        
        switchInputMode('form');
    } catch (e) {
        showError('Invalid JSON format: ' + e.message);
    }
}

function removeTask(id) {
    pendingTasks = pendingTasks.filter(t => t.id !== id);
    updateTaskList();
    updateAnalyzeButton();
}

function updateTaskList() {
    const container = document.getElementById('taskList');
    const countSpan = document.getElementById('taskCount');
    
    countSpan.textContent = pendingTasks.length;
    
    if (pendingTasks.length === 0) {
        container.innerHTML = '<p class="empty-state" style="padding: 1rem;">No tasks added yet</p>';
        return;
    }

    container.innerHTML = pendingTasks.map(task => `
        <div class="preview-task">
            <div>
                <span class="task-title">${escapeHtml(task.title)}</span>
                <span class="task-meta"> | Due: ${task.due_date} | Importance: ${task.importance}/10</span>
            </div>
            <button class="remove-btn" onclick="removeTask(${task.id})" title="Remove task">&times;</button>
        </div>
    `).join('');
}

function updateAnalyzeButton() {
    const analyzeBtn = document.getElementById('analyzeBtn');
    analyzeBtn.disabled = pendingTasks.length === 0;
}

async function analyzeTasks() {
    if (pendingTasks.length === 0) {
        showError('Please add at least one task to analyze');
        return;
    }

    const strategy = document.getElementById('strategy').value;
    
    showLoading(true);
    hideError();
    hideWarning();

    try {
        const response = await fetch('/api/tasks/analyze/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                tasks: pendingTasks,
                strategy: strategy
            })
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.error || 'Failed to analyze tasks');
        }

        if (data.warnings && data.warnings.length > 0) {
            showWarning(data.warnings.join('. '));
        }

        displayResults(data);
    } catch (error) {
        showError('Error analyzing tasks: ' + error.message);
    } finally {
        showLoading(false);
    }
}

async function getSuggestions() {
    showLoading(true);
    hideError();
    hideWarning();

    try {
        let response;
        
        if (pendingTasks.length > 0) {
            response = await fetch('/api/tasks/suggest/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ tasks: pendingTasks })
            });
        } else {
            response = await fetch('/api/tasks/suggest/');
        }

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.error || 'Failed to get suggestions');
        }

        displaySuggestions(data);
    } catch (error) {
        showError('Error getting suggestions: ' + error.message);
    } finally {
        showLoading(false);
    }
}

function displayResults(data) {
    const container = document.getElementById('resultsContainer');
    
    if (!data.tasks || data.tasks.length === 0) {
        container.innerHTML = '<div class="empty-state"><p>No tasks to display</p></div>';
        return;
    }

    let html = `
        <div class="results-summary">
            <div class="summary-item">
                <span>Total Tasks:</span>
                <strong>${data.total_tasks}</strong>
            </div>
            <div class="summary-item">
                <span>Strategy:</span>
                <strong>${formatStrategy(data.strategy_used)}</strong>
            </div>
        </div>
    `;

    html += data.tasks.map((task, index) => createTaskCard(task, index + 1)).join('');
    
    container.innerHTML = html;
}

function displaySuggestions(data) {
    const container = document.getElementById('resultsContainer');
    
    if (!data.suggestions || data.suggestions.length === 0) {
        container.innerHTML = '<div class="empty-state"><p>No suggestions available</p></div>';
        return;
    }

    let html = `
        <div class="results-summary">
            <div class="summary-item">
                <strong>${data.message}</strong>
            </div>
        </div>
    `;

    html += data.suggestions.map(task => createSuggestionCard(task)).join('');
    
    container.innerHTML = html;
}

function createTaskCard(task, rank) {
    const priorityClass = `priority-${task.priority_level}`;
    
    return `
        <div class="task-card ${priorityClass}">
            <div class="task-header">
                <div class="task-title-section">
                    <div class="task-rank">#${rank}</div>
                    <h3>${escapeHtml(task.title)}</h3>
                </div>
                <div class="task-score">
                    <span class="score-value">${task.score}</span>
                    <span class="priority-badge">${task.priority_level}</span>
                </div>
            </div>
            
            <div class="task-details">
                <div class="detail-item">
                    <span class="detail-label">Due Date</span>
                    <span class="detail-value">${task.due_date || 'Not set'}</span>
                </div>
                <div class="detail-item">
                    <span class="detail-label">Importance</span>
                    <span class="detail-value">${task.importance}/10</span>
                </div>
                <div class="detail-item">
                    <span class="detail-label">Effort</span>
                    <span class="detail-value">${task.estimated_hours}h</span>
                </div>
                <div class="detail-item">
                    <span class="detail-label">Dependencies</span>
                    <span class="detail-value">${task.dependencies.length > 0 ? task.dependencies.join(', ') : 'None'}</span>
                </div>
            </div>
            
            <div class="task-explanation">
                <strong>Why this score:</strong> ${escapeHtml(task.explanation)}
                <div class="score-breakdown">
                    ${createScoreBreakdown(task.score_breakdown)}
                </div>
            </div>
            
            ${task.validation_warnings && task.validation_warnings.length > 0 ? `
                <div class="task-warnings">
                    Warnings: ${task.validation_warnings.join(', ')}
                </div>
            ` : ''}
        </div>
    `;
}

function createSuggestionCard(task) {
    const priorityClass = `priority-${task.priority_level}`;
    
    return `
        <div class="task-card ${priorityClass}">
            <div class="task-header">
                <div class="task-title-section">
                    <div class="task-rank">#${task.rank} Priority</div>
                    <h3>${escapeHtml(task.title)}</h3>
                </div>
                <div class="task-score">
                    <span class="score-value">${task.score}</span>
                    <span class="priority-badge">${task.priority_level}</span>
                </div>
            </div>
            
            <div class="task-details">
                <div class="detail-item">
                    <span class="detail-label">Due Date</span>
                    <span class="detail-value">${task.due_date || 'Not set'}</span>
                </div>
                <div class="detail-item">
                    <span class="detail-label">Importance</span>
                    <span class="detail-value">${task.importance}/10</span>
                </div>
                <div class="detail-item">
                    <span class="detail-label">Effort</span>
                    <span class="detail-value">${task.estimated_hours}h</span>
                </div>
            </div>
            
            <div class="why-reasons">
                <h4>Why work on this:</h4>
                <ul>
                    ${task.why_work_on_this.map(reason => `<li>${escapeHtml(reason)}</li>`).join('')}
                </ul>
            </div>
        </div>
    `;
}

function createScoreBreakdown(breakdown) {
    if (!breakdown) return '';
    
    const items = [];
    
    if (breakdown.urgency !== 0) {
        const cls = breakdown.urgency > 0 ? 'positive' : 'negative';
        items.push(`<span class="breakdown-item ${cls}">Urgency: ${breakdown.urgency > 0 ? '+' : ''}${breakdown.urgency}</span>`);
    }
    
    if (breakdown.importance !== 0) {
        items.push(`<span class="breakdown-item positive">Importance: +${breakdown.importance}</span>`);
    }
    
    if (breakdown.effort !== 0) {
        const cls = breakdown.effort > 0 ? 'positive' : 'negative';
        items.push(`<span class="breakdown-item ${cls}">Effort: ${breakdown.effort > 0 ? '+' : ''}${breakdown.effort}</span>`);
    }
    
    if (breakdown.dependency > 0) {
        items.push(`<span class="breakdown-item positive">Blocks others: +${breakdown.dependency}</span>`);
    }
    
    return items.join('');
}

function formatStrategy(strategy) {
    const strategies = {
        'smart_balance': 'Smart Balance',
        'fastest_wins': 'Fastest Wins',
        'high_impact': 'High Impact',
        'deadline_driven': 'Deadline Driven'
    };
    return strategies[strategy] || strategy;
}

function clearAll() {
    pendingTasks = [];
    taskIdCounter = 1;
    updateTaskList();
    updateAnalyzeButton();
    
    document.getElementById('resultsContainer').innerHTML = `
        <div class="empty-state">
            <p>Add tasks and click "Analyze Tasks" to see prioritized results</p>
        </div>
    `;
    
    document.getElementById('jsonTextarea').value = '';
    hideError();
    hideWarning();
}

function showLoading(show) {
    const indicator = document.getElementById('loadingIndicator');
    indicator.classList.toggle('hidden', !show);
}

function showError(message) {
    const errorDiv = document.getElementById('errorMessage');
    errorDiv.textContent = message;
    errorDiv.classList.remove('hidden');
}

function hideError() {
    document.getElementById('errorMessage').classList.add('hidden');
}

function showWarning(message) {
    const warningDiv = document.getElementById('warningMessage');
    warningDiv.textContent = message;
    warningDiv.classList.remove('hidden');
}

function hideWarning() {
    document.getElementById('warningMessage').classList.add('hidden');
}

function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

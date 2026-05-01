const API_BASE = ''; 

// State management
let currentToken = localStorage.getItem('access_token');
let currentUser = null;

// Initialization
document.addEventListener('DOMContentLoaded', () => {
    if (currentToken) {
        showAppView();
        navigate('dashboard');
    } else {
        showAuthView();
    }
});

// UI Navigation
function switchAuthTab(tab) {
    document.querySelectorAll('.tab-btn').forEach(btn => btn.classList.remove('active'));
    document.getElementById(`tab-${tab}`).classList.add('active');

    if (tab === 'login') {
        document.getElementById('login-form').style.display = 'block';
        document.getElementById('register-form').style.display = 'none';
    } else {
        document.getElementById('login-form').style.display = 'none';
        document.getElementById('register-form').style.display = 'block';
    }
}

function showAuthView() {
    document.getElementById('auth-view').classList.add('active');
    document.getElementById('app-view').classList.remove('active');
}

function showAppView() {
    document.getElementById('auth-view').classList.remove('active');
    document.getElementById('app-view').classList.add('active');
}

function navigate(viewName) {
    document.querySelectorAll('.sidebar-nav a').forEach(a => a.classList.remove('active'));
    document.getElementById(`nav-${viewName}`).classList.add('active');

    document.querySelectorAll('.sub-view').forEach(v => v.style.display = 'none');
    document.getElementById(`view-${viewName}`).style.display = 'block';

    const titles = {
        'dashboard': 'Dashboard',
        'projects': 'Projects',
        'tasks': 'Tasks'
    };
    document.getElementById('current-view-title').textContent = titles[viewName];

    // Load corresponding data
    if (viewName === 'dashboard') loadDashboard();
    if (viewName === 'projects') loadProjects();
    if (viewName === 'tasks') loadTasks();
}

// Modals
function openModal(id) {
    document.getElementById(id).classList.add('active');
}

function closeModal(id) {
    document.getElementById(id).classList.remove('active');
}

async function openTaskModal() {
    // Need to load projects and users for the dropdowns first
    await populateProjectDropdown();
    await populateAssigneeDropdown();
    openModal('task-modal');
}

// API Helpers
async function apiCall(endpoint, options = {}) {
    const headers = {
        'Content-Type': 'application/json',
        ...options.headers
    };

    if (currentToken) {
        headers['Authorization'] = `Bearer ${currentToken}`;
    }

    const config = {
        ...options,
        headers
    };

    // OAuth2 expects form-urlencoded for the token endpoint
    if (options.isForm) {
        headers['Content-Type'] = 'application/x-www-form-urlencoded';
    }

    const response = await fetch(`${API_BASE}${endpoint}`, config);
    if (!response.ok) {
        let errorMsg = 'An error occurred';
        try {
            const errorData = await response.json();
            errorMsg = errorData.detail || errorMsg;
        } catch(e) {}
        throw new Error(errorMsg);
    }
    if (response.status === 204) {
        return null;
    }
    return response.json();
}

// Authentication
async function handleLogin(e) {
    e.preventDefault();
    const email = document.getElementById('login-email').value;
    const password = document.getElementById('login-password').value;
    const errorEl = document.getElementById('login-error');
    
    errorEl.textContent = '';

    const formData = new URLSearchParams();
    formData.append('username', email);
    formData.append('password', password);

    try {
        const data = await apiCall('/auth/token', {
            method: 'POST',
            body: formData,
            isForm: true
        });
        
        currentToken = data.access_token;
        localStorage.setItem('access_token', currentToken);
        showAppView();
        navigate('dashboard');
    } catch (err) {
        errorEl.textContent = err.message;
    }
}

async function handleRegister(e) {
    e.preventDefault();
    const email = document.getElementById('reg-email').value;
    const phone = document.getElementById('reg-phone').value;
    const role = document.getElementById('reg-role').value;
    const password = document.getElementById('reg-password').value;
    const errorEl = document.getElementById('reg-error');

    errorEl.textContent = '';

    try {
        await apiCall('/auth/register', {
            method: 'POST',
            body: JSON.stringify({ email, phone_number: phone, role, password })
        });
        
        // Auto-login after successful registration could be added here
        switchAuthTab('login');
        document.getElementById('login-email').value = email;
        alert('Registration successful. Please log in.');
    } catch (err) {
        errorEl.textContent = err.message;
    }
}

function handleLogout() {
    currentToken = null;
    localStorage.removeItem('access_token');
    showAuthView();
}

// Dashboard
async function loadDashboard() {
    try {
        const stats = await apiCall('/dashboard/');
        document.getElementById('stat-total').textContent = stats.total_tasks || 0;
        document.getElementById('stat-pending').textContent = stats.pending_tasks || 0;
        document.getElementById('stat-progress').textContent = stats.in_progress_tasks || 0;
        document.getElementById('stat-completed').textContent = stats.completed_tasks || 0;
        document.getElementById('stat-overdue').textContent = stats.overdue_tasks_count || 0;
    } catch (err) {
        if (err.message.includes('validate credentials') || err.message.includes('Not authenticated')) {
            handleLogout();
        }
        console.error('Failed to load dashboard:', err);
    }
}

// Projects
async function loadProjects() {
    try {
        const projects = await apiCall('/projects/');
        const container = document.getElementById('projects-list');
        container.innerHTML = '';
        
        if (projects.length === 0) {
            container.innerHTML = '<p class="subtitle">No projects found. Create one to get started!</p>';
            return;
        }

        projects.forEach(p => {
            const el = document.createElement('div');
            el.className = 'project-card';
            el.innerHTML = `
                <div class="card-header">
                    <h3>${p.title}</h3>
                    <button class="delete-btn" onclick="deleteProject(${p.id})">Delete</button>
                </div>
                <p>${p.description || 'No description provided.'}</p>
            `;
            container.appendChild(el);
        });
    } catch (err) {
        console.error('Failed to load projects:', err);
    }
}

async function handleCreateProject(e) {
    e.preventDefault();
    const title = document.getElementById('project-title').value;
    const description = document.getElementById('project-desc').value;

    try {
        await apiCall('/projects/', {
            method: 'POST',
            body: JSON.stringify({ title, description })
        });
        closeModal('project-modal');
        document.getElementById('create-project-form').reset();
        loadProjects();
    } catch (err) {
        alert(err.message);
    }
}

// Tasks
async function loadTasks() {
    try {
        const tasks = await apiCall('/tasks/');
        const container = document.getElementById('tasks-list');
        container.innerHTML = '';

        if (tasks.length === 0) {
            container.innerHTML = '<p class="subtitle">No tasks found.</p>';
            return;
        }

        tasks.forEach(t => {
            const statusClass = t.status.replace(' ', '-');
            const el = document.createElement('div');
            el.className = 'task-item';
            el.innerHTML = `
                <div class="task-info">
                    <h4>${t.title}</h4>
                    <span class="task-meta">${t.description || ''} • Priority: ${t.priority}</span>
                </div>
                <div class="task-actions" style="display: flex; gap: 0.5rem; align-items: center;">
                    <select class="status-select status-${statusClass}" onchange="updateTaskStatus(${t.id}, this.value)">
                        <option value="Pending" ${t.status === 'Pending' ? 'selected' : ''}>Pending</option>
                        <option value="In Progress" ${t.status === 'In Progress' ? 'selected' : ''}>In Progress</option>
                        <option value="Completed" ${t.status === 'Completed' ? 'selected' : ''}>Completed</option>
                    </select>
                    <button class="delete-btn" onclick="deleteTask(${t.id})">Delete</button>
                </div>
            `;
            container.appendChild(el);
        });
    } catch (err) {
        console.error('Failed to load tasks:', err);
    }
}

async function updateTaskStatus(taskId, newStatus) {
    try {
        await apiCall(`/tasks/${taskId}`, {
            method: 'PUT',
            body: JSON.stringify({ status: newStatus })
        });
        loadTasks(); // reload to show updated colors
        loadDashboard(); // reload dashboard stats
    } catch (err) {
        alert("Failed to update status: " + err.message);
        loadTasks(); // revert dropdown on error
    }
}

async function deleteProject(projectId) {
    if (!confirm("Are you sure you want to delete this project? All associated tasks will also be deleted.")) return;
    try {
        await apiCall(`/projects/${projectId}`, { method: 'DELETE' });
        loadProjects();
        loadDashboard();
    } catch (err) {
        alert("Failed to delete project: " + err.message);
    }
}

async function deleteTask(taskId) {
    if (!confirm("Are you sure you want to delete this task?")) return;
    try {
        await apiCall(`/tasks/${taskId}`, { method: 'DELETE' });
        loadTasks();
        loadDashboard();
    } catch (err) {
        alert("Failed to delete task: " + err.message);
    }
}

async function populateProjectDropdown() {
    try {
        const projects = await apiCall('/projects/');
        const select = document.getElementById('task-project-id');
        select.innerHTML = '';
        projects.forEach(p => {
            const opt = document.createElement('option');
            opt.value = p.id;
            opt.textContent = p.title;
            select.appendChild(opt);
        });
    } catch (err) {
        console.error('Failed to load projects for dropdown:', err);
    }
}

async function populateAssigneeDropdown() {
    try {
        const users = await apiCall('/users/');
        const select = document.getElementById('task-assignee-id');
        select.innerHTML = '<option value="">Unassigned</option>';
        users.forEach(u => {
            const opt = document.createElement('option');
            opt.value = u.id;
            opt.textContent = `${u.email} (${u.role})`;
            select.appendChild(opt);
        });
    } catch (err) {
        console.error('Failed to load users for dropdown:', err);
    }
}

async function handleCreateTask(e) {
    e.preventDefault();
    const title = document.getElementById('task-title').value;
    const description = document.getElementById('task-desc').value;
    const project_id = document.getElementById('task-project-id').value;
    const assignee_id = document.getElementById('task-assignee-id').value;
    const priority = document.getElementById('task-priority').value;

    const payload = { 
        title, 
        description, 
        project_id: parseInt(project_id), 
        priority: parseInt(priority),
        status: 'Pending'
    };

    if (assignee_id) {
        payload.assignee_id = parseInt(assignee_id);
    }

    try {
        await apiCall('/tasks/', {
            method: 'POST',
            body: JSON.stringify(payload)
        });
        closeModal('task-modal');
        document.getElementById('create-task-form').reset();
        loadTasks();
    } catch (err) {
        alert(err.message);
    }
}

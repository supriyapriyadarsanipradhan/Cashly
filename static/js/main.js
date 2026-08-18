document.addEventListener('DOMContentLoaded', () => {
    // Determine active page based on elements present
    if (document.getElementById('dashboard-view')) {
        initDashboard();
    }
    if (document.getElementById('expenses-view')) {
        initExpenses();
    }
    if (document.getElementById('budgets-view')) {
        initBudgets();
    }
    if (document.getElementById('goals-view')) {
        initGoals();
    }
    if (document.getElementById('chat-view')) {
        initChat();
    }
});

// --- HELPER UTILITIES ---

function formatCurrency(amount) {
    return new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR' }).format(amount);
}

function getCategoryClass(category) {
    const map = {
        'Food & Dining': 'cat-food-dining',
        'Housing & Rent': 'cat-housing-rent',
        'Utilities & Bills': 'cat-utilities-bills',
        'Transportation': 'cat-transportation',
        'Entertainment': 'cat-entertainment',
        'Shopping': 'cat-shopping',
        'Health & Fitness': 'cat-health-fitness'
    };
    return map[category] || 'cat-other';
}

function parseMarkdown(text) {
    if (!text) return '';
    let html = text
        .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
        .replace(/\*(.*?)\*/g, '<em>$1</em>')
        .replace(/`([^`]+)`/g, '<code>$1</code>')
        .replace(/\n/g, '<br>');
    return html;
}

// --- DASHBOARD CONTROLLER ---

let breakdownChart = null;
let trendsChart = null;

function initDashboard() {
    loadDashboardData();
    
    // Income update form handler
    const incomeForm = document.getElementById('incomeForm');
    if (incomeForm) {
        incomeForm.addEventListener('submit', (e) => {
            e.preventDefault();
            const incomeVal = document.getElementById('monthlyIncomeInput').value;
            
            fetch('/api/user/income', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ monthly_income: incomeVal })
            })
            .then(res => res.json())
            .then(data => {
                if (data.error) {
                    alert(data.error);
                } else {
                    const bootstrapModal = bootstrap.Modal.getInstance(document.getElementById('incomeModal'));
                    bootstrapModal.hide();
                    loadDashboardData();
                    // Show a message to user
                    showToast('Income updated successfully!', 'success');
                }
            })
            .catch(err => console.error('Error updating income:', err));
        });
    }
}

function loadDashboardData() {
    fetch('/api/ai/analyze')
        .then(res => res.json())
        .then(data => {
            const income = data.monthly_income || 0;
            const spent = data.current_month_spent || 0;
            const savings = Math.max(0, income - spent);
            
            // Set values
            document.getElementById('total-income').innerText = formatCurrency(income);
            document.getElementById('total-spent').innerText = formatCurrency(spent);
            document.getElementById('total-savings').innerText = formatCurrency(savings);
            
            // Health Score gauge
            const healthScore = data.financial_health.score;
            document.getElementById('health-score-val').innerText = healthScore;
            
            // Update SVG circle path
            const circleFill = document.getElementById('health-score-fill');
            if (circleFill) {
                const radius = 58;
                const circumference = 2 * Math.PI * radius;
                const offset = circumference - (healthScore / 100) * circumference;
                circleFill.style.strokeDasharray = `${circumference} ${circumference}`;
                circleFill.style.strokeDashoffset = offset;
                
                // Color adjustment
                if (healthScore >= 80) {
                    circleFill.style.stroke = '#10b981'; // Green
                } else if (healthScore >= 50) {
                    circleFill.style.stroke = '#f59e0b'; // Yellow
                } else {
                    circleFill.style.stroke = '#ef4444'; // Red
                }
            }
            
            // Tips checklist
            const tipsContainer = document.getElementById('health-tips');
            if (tipsContainer) {
                tipsContainer.innerHTML = '';
                if (data.financial_health.tips && data.financial_health.tips.length > 0) {
                    data.financial_health.tips.forEach(tip => {
                        const li = document.createElement('li');
                        li.className = 'mb-2 text-secondary d-flex align-items-start gap-2';
                        li.innerHTML = `<i class="fas fa-info-circle mt-1 text-emerald"></i> <span>${tip}</span>`;
                        tipsContainer.appendChild(li);
                    });
                } else {
                    tipsContainer.innerHTML = '<li class="text-muted">No tips available yet. Add transactions or set budgets to begin.</li>';
                }
            }
            
            // Prediction section
            loadPrediction();

            // Render Charts
            renderBreakdownChart(data.category_breakdown);
            renderTrendsChart(data.monthly_trends);
        })
        .catch(err => console.error('Error fetching dashboard analysis:', err));
}

function loadPrediction() {
    const predictionInsight = document.getElementById('prediction-insight');
    if (!predictionInsight) return;
    
    fetch('/api/ai/predict')
        .then(res => res.json())
        .then(data => {
            document.getElementById('predicted-spending').innerText = formatCurrency(data.predicted_spending);
            predictionInsight.innerText = data.insight;
        })
        .catch(err => console.error('Error getting prediction:', err));
}

function renderBreakdownChart(breakdownData) {
    const ctx = document.getElementById('breakdownChart');
    if (!ctx) return;
    
    const categories = Object.keys(breakdownData);
    const amounts = Object.values(breakdownData);
    
    if (categories.length === 0) {
        // Draw standard empty state on parent element or render placeholder
        ctx.style.display = 'none';
        document.getElementById('breakdown-empty').classList.remove('d-none');
        return;
    }
    
    ctx.style.display = 'block';
    document.getElementById('breakdown-empty').classList.add('d-none');
    
    if (breakdownChart) {
        breakdownChart.destroy();
    }
    
    breakdownChart = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: categories,
            datasets: [{
                data: amounts,
                backgroundColor: [
                    '#10b981', // Emerald
                    '#f59e0b', // Yellow
                    '#3b82f6', // Info blue
                    '#8b5cf6', // Purple
                    '#ec4899', // Pink
                    '#f43f5e', // Rose
                    '#14b8a6', // Teal
                    '#6b7280'  // Slate gray
                ],
                borderColor: '#161920',
                borderWidth: 2
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: { color: '#f3f4f6', font: { family: 'Inter', size: 11 } }
                }
            }
        }
    });
}

function renderTrendsChart(trendsData) {
    const ctx = document.getElementById('trendsChart');
    if (!ctx) return;
    
    const months = Object.keys(trendsData);
    const amounts = Object.values(trendsData);
    
    if (months.length === 0) {
        ctx.style.display = 'none';
        document.getElementById('trends-empty').classList.remove('d-none');
        return;
    }
    
    ctx.style.display = 'block';
    document.getElementById('trends-empty').classList.add('d-none');
    
    if (trendsChart) {
        trendsChart.destroy();
    }
    
    trendsChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: months,
            datasets: [{
                label: 'Monthly Expenditures',
                data: amounts,
                borderColor: '#10b981',
                backgroundColor: 'rgba(16, 185, 129, 0.1)',
                borderWidth: 3,
                fill: true,
                tension: 0.3,
                pointBackgroundColor: '#10b981',
                pointHoverRadius: 7
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false }
            },
            scales: {
                x: {
                    grid: { color: '#2a313e' },
                    ticks: { color: '#9ca3af', font: { family: 'Inter' } }
                },
                y: {
                    grid: { color: '#2a313e' },
                    ticks: { color: '#9ca3af', font: { family: 'Inter' } }
                }
            }
        }
    });
}


// --- EXPENSES CONTROLLER ---

let selectedExpenseId = null;

function initExpenses() {
    loadExpenseList();
    
    // Auto-category suggestion while typing descriptions
    const descInput = document.getElementById('exp-description');
    const categorySelect = document.getElementById('exp-category');
    
    if (descInput && categorySelect) {
        descInput.addEventListener('blur', () => {
            const desc = descInput.value.strip ? descInput.value.strip() : descInput.value;
            if (desc.length > 2 && categorySelect.value === 'Other') {
                fetch('/api/expenses/suggest-category', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ description: desc })
                })
                .then(res => res.json())
                .then(data => {
                    if (data.category && data.category !== 'Other') {
                        categorySelect.value = data.category;
                        showToast(`Auto-categorized as: ${data.category}`, 'info');
                    }
                });
            }
        });
    }
    
    // Add/Edit forms
    const expenseForm = document.getElementById('expenseForm');
    if (expenseForm) {
        expenseForm.addEventListener('submit', (e) => {
            e.preventDefault();
            const amount = document.getElementById('exp-amount').value;
            const description = document.getElementById('exp-description').value;
            const category = document.getElementById('exp-category').value;
            const date = document.getElementById('exp-date').value;
            
            const payload = { amount, description, category, date };
            
            let url = '/api/expenses';
            let method = 'POST';
            
            if (selectedExpenseId) {
                url = `/api/expenses/${selectedExpenseId}`;
                method = 'PUT';
            }
            
            fetch(url, {
                method: method,
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            })
            .then(res => res.json())
            .then(data => {
                if (data.error) {
                    alert(data.error);
                } else {
                    const modal = bootstrap.Modal.getInstance(document.getElementById('expenseModal'));
                    modal.hide();
                    loadExpenseList();
                    showToast(selectedExpenseId ? 'Transaction updated!' : 'Transaction added!', 'success');
                }
            })
            .catch(err => console.error('Error saving transaction:', err));
        });
    }
    
    // Delete validation handler
    const confirmDeleteBtn = document.getElementById('confirmDeleteBtn');
    if (confirmDeleteBtn) {
        confirmDeleteBtn.addEventListener('click', () => {
            if (!selectedExpenseId) return;
            fetch(`/api/expenses/${selectedExpenseId}`, { method: 'DELETE' })
                .then(res => res.json())
                .then(() => {
                    const modal = bootstrap.Modal.getInstance(document.getElementById('deleteModal'));
                    modal.hide();
                    loadExpenseList();
                    showToast('Transaction deleted.', 'danger');
                })
                .catch(err => console.error(err));
        });
    }
}

function loadExpenseList() {
    const tableBody = document.getElementById('expenses-table-body');
    if (!tableBody) return;
    
    fetch('/api/expenses')
        .then(res => res.json())
        .then(expenses => {
            tableBody.innerHTML = '';
            if (expenses.length === 0) {
                tableBody.innerHTML = `<tr><td colspan="5" class="text-center text-muted py-4">No expenses recorded yet. click "+ Log Expense" to start.</td></tr>`;
                return;
            }
            
            expenses.forEach(e => {
                const tr = document.createElement('tr');
                tr.innerHTML = `
                    <td>${e.date}</td>
                    <td>${e.description || '<em class="text-muted">No description</em>'}</td>
                    <td><span class="category-pill ${getCategoryClass(e.category)}">${e.category}</span></td>
                    <td class="fw-bold">${formatCurrency(e.amount)}</td>
                    <td class="text-end">
                        <button class="btn btn-sm btn-outline-custom me-1 py-1 px-2" onclick="openEditModal(${e.id}, '${e.amount}', '${e.description}', '${e.category}', '${e.date}')">
                            <i class="fas fa-edit"></i>
                        </button>
                        <button class="btn btn-sm btn-outline-danger py-1 px-2" style="border-radius: var(--radius-sm); font-size: 0.75rem" onclick="openDeleteModal(${e.id})">
                            <i class="fas fa-trash-alt"></i>
                        </button>
                    </td>
                `;
                tableBody.appendChild(tr);
            });
        })
        .catch(err => console.error(err));
}

function openAddModal() {
    selectedExpenseId = null;
    document.getElementById('expenseModalLabel').innerText = 'Log Expense';
    document.getElementById('expenseForm').reset();
    document.getElementById('exp-date').value = new Date().toISOString().substring(0, 10);
    const modal = new bootstrap.Modal(document.getElementById('expenseModal'));
    modal.show();
}

function openEditModal(id, amount, description, category, date) {
    selectedExpenseId = id;
    document.getElementById('expenseModalLabel').innerText = 'Edit Expense';
    document.getElementById('exp-amount').value = amount;
    document.getElementById('exp-description').value = description === 'null' ? '' : description;
    document.getElementById('exp-category').value = category;
    document.getElementById('exp-date').value = date;
    const modal = new bootstrap.Modal(document.getElementById('expenseModal'));
    modal.show();
}

function openDeleteModal(id) {
    selectedExpenseId = id;
    const modal = new bootstrap.Modal(document.getElementById('deleteModal'));
    modal.show();
}


// --- BUDGETS CONTROLLER ---

function initBudgets() {
    loadBudgetsList();
    
    // Add/Update budget forms
    const budgetForm = document.getElementById('budgetForm');
    if (budgetForm) {
        budgetForm.addEventListener('submit', (e) => {
            e.preventDefault();
            const category = document.getElementById('budget-category').value;
            const amount = document.getElementById('budget-amount').value;
            
            fetch('/api/budgets', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ category, amount })
            })
            .then(res => res.json())
            .then(data => {
                if (data.error) {
                    alert(data.error);
                } else {
                    const modal = bootstrap.Modal.getInstance(document.getElementById('budgetModal'));
                    modal.hide();
                    loadBudgetsList();
                    showToast('Budget configured!', 'success');
                }
            })
            .catch(err => console.error(err));
        });
    }
}

function loadBudgetsList() {
    const listContainer = document.getElementById('budgets-list');
    if (!listContainer) return;
    
    fetch('/api/budgets')
        .then(res => res.json())
        .then(budgets => {
            listContainer.innerHTML = '';
            if (budgets.length === 0) {
                listContainer.innerHTML = `<div class="col-12 text-center text-muted py-5">
                    <p>No budgets configured.</p>
                    <button class="btn btn-emerald mt-2" onclick="setupRecommendedBudgets()">Auto-Setup Budgets (50/30/20 Rule)</button>
                </div>`;
                return;
            }
            
            budgets.forEach(b => {
                const pct = b.amount > 0 ? (b.spent / b.amount) * 100 : 0;
                
                // Color configuration
                let barColor = 'bg-success';
                let alertClass = '';
                if (pct >= 100) {
                    barColor = 'bg-danger';
                    alertClass = 'text-danger font-weight-bold';
                } else if (pct >= 75) {
                    barColor = 'bg-warning';
                    alertClass = 'text-warning';
                }
                
                const col = document.createElement('div');
                col.className = 'col-md-6 mb-4';
                col.innerHTML = `
                    <div class="card-custom">
                        <div class="d-flex justify-content-between align-items-center mb-3">
                            <span class="category-pill ${getCategoryClass(b.category)}">${b.category}</span>
                            <button class="btn btn-link text-secondary p-0" onclick="deleteCategoryBudget(${b.id})">
                                <i class="fas fa-trash-alt"></i>
                            </button>
                        </div>
                        <div class="d-flex justify-content-between align-items-baseline mb-2">
                            <div>
                                <span class="fs-4 fw-bold ${alertClass}">${formatCurrency(b.spent)}</span>
                                <span class="text-secondary font-weight-normal"> spent</span>
                            </div>
                            <span class="text-secondary font-weight-bold">Limit: ${formatCurrency(b.amount)}</span>
                        </div>
                        
                        <div class="progress progress-custom">
                            <div class="progress-bar progress-bar-custom ${barColor}" role="progressbar" style="width: ${Math.min(100, pct)}%"></div>
                        </div>
                        
                        <div class="d-flex justify-content-between mt-2 font-size-sm text-secondary">
                            <span>${pct.toFixed(0)}% utilized</span>
                            <span>${pct >= 100 ? 'Limit exceeded!' : formatCurrency(b.amount - b.spent) + ' remaining'}</span>
                        </div>
                    </div>
                `;
                listContainer.appendChild(col);
            });
        });
}

function deleteCategoryBudget(id) {
    if (!confirm('Are you sure you want to remove this budget?')) return;
    fetch(`/api/budgets/${id}`, { method: 'DELETE' })
        .then(() => {
            loadBudgetsList();
            showToast('Budget deleted.', 'danger');
        });
}

function setupRecommendedBudgets() {
    fetch('/api/ai/recommend-budgets')
        .then(res => res.json())
        .then(recs => {
            if (Object.keys(recs).length === 0) {
                alert('Please set your monthly income in the Dashboard first to generate budget recommendations.');
                return;
            }
            // Sequentially post all recommendations
            const promises = Object.keys(recs).map(category => {
                return fetch('/api/budgets', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ category, amount: recs[category] })
                });
            });
            
            Promise.all(promises).then(() => {
                loadBudgetsList();
                showToast('Created budgets based on 50/30/20 rule!', 'success');
            });
        });
}


// --- SAVINGS GOALS CONTROLLER ---

let selectedGoalId = null;

function initGoals() {
    loadGoalsList();
    
    const goalForm = document.getElementById('goalForm');
    if (goalForm) {
        goalForm.addEventListener('submit', (e) => {
            e.preventDefault();
            const name = document.getElementById('goal-name').value;
            const target_amount = document.getElementById('goal-target').value;
            const current_amount = document.getElementById('goal-current').value;
            const target_date = document.getElementById('goal-date').value;
            
            const payload = { name, target_amount, current_amount, target_date };
            let url = '/api/goals';
            let method = 'POST';
            
            if (selectedGoalId) {
                url = `/api/goals/${selectedGoalId}`;
                method = 'PUT';
            }
            
            fetch(url, {
                method: method,
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            })
            .then(res => res.json())
            .then(data => {
                if (data.error) {
                    alert(data.error);
                } else {
                    const modal = bootstrap.Modal.getInstance(document.getElementById('goalModal'));
                    modal.hide();
                    loadGoalsList();
                    showToast(selectedGoalId ? 'Goal updated!' : 'Goal created!', 'success');
                }
            })
            .catch(err => console.error(err));
        });
    }
}

function loadGoalsList() {
    const goalsContainer = document.getElementById('goals-list');
    if (!goalsContainer) return;
    
    fetch('/api/goals')
        .then(res => res.json())
        .then(goals => {
            goalsContainer.innerHTML = '';
            if (goals.length === 0) {
                goalsContainer.innerHTML = `<div class="col-12 text-center text-muted py-5">No active saving goals. Let's create one now!</div>`;
                return;
            }
            
            goals.forEach(g => {
                const pct = g.target_amount > 0 ? (g.current_amount / g.target_amount) * 100 : 0;
                const remaining = Math.max(0, g.target_amount - g.current_amount);
                
                const col = document.createElement('div');
                col.className = 'col-md-4 mb-4';
                col.innerHTML = `
                    <div class="goal-progress-card">
                        <div class="goal-header">
                            <span class="goal-name">${g.name}</span>
                            <div class="dropdown">
                                <button class="btn btn-sm btn-link text-secondary p-0" data-bs-toggle="dropdown">
                                    <i class="fas fa-ellipsis-v"></i>
                                </button>
                                <ul class="dropdown-menu dropdown-menu-dark dropdown-menu-end border-color" style="background-color: var(--bg-tertiary)">
                                    <li><a class="dropdown-item py-2" href="#" onclick="openEditGoalModal(${g.id}, '${g.name}', '${g.target_amount}', '${g.current_amount}', '${g.target_date}')"><i class="fas fa-edit me-2 text-emerald"></i> Edit Details</a></li>
                                    <li><hr class="dropdown-divider border-color"></li>
                                    <li><a class="dropdown-item py-2 text-danger" href="#" onclick="deleteGoalItem(${g.id})"><i class="fas fa-trash-alt me-2"></i> Delete Goal</a></li>
                                </ul>
                            </div>
                        </div>
                        
                        <div class="d-flex justify-content-between align-items-baseline">
                            <span class="fs-3 fw-bold text-emerald">${formatCurrency(g.current_amount)}</span>
                            <span class="text-secondary font-size-sm">Target: ${formatCurrency(g.target_amount)}</span>
                        </div>
                        
                        <div class="progress progress-custom">
                            <div class="progress-bar progress-bar-custom bg-emerald" role="progressbar" style="width: ${Math.min(100, pct)}%"></div>
                        </div>
                        
                        <div class="d-flex justify-content-between text-secondary font-size-sm" style="font-size: 0.85rem">
                            <span>${pct.toFixed(0)}% reached</span>
                            <span>Target Date: ${g.target_date}</span>
                        </div>
                    </div>
                `;
                goalsContainer.appendChild(col);
            });
        });
}

function openAddGoalModal() {
    selectedGoalId = null;
    document.getElementById('goalModalLabel').innerText = 'Create Goal';
    document.getElementById('goalForm').reset();
    document.getElementById('goal-date').value = new Date(new Date().setMonth(new Date().getMonth() + 6)).toISOString().substring(0, 10);
    const modal = new bootstrap.Modal(document.getElementById('goalModal'));
    modal.show();
}

function openEditGoalModal(id, name, target, current, target_date) {
    selectedGoalId = id;
    document.getElementById('goalModalLabel').innerText = 'Edit Savings Goal';
    document.getElementById('goal-name').value = name;
    document.getElementById('goal-target').value = target;
    document.getElementById('goal-current').value = current;
    document.getElementById('goal-date').value = target_date;
    const modal = new bootstrap.Modal(document.getElementById('goalModal'));
    modal.show();
}

function deleteGoalItem(id) {
    if (!confirm('Are you sure you want to remove this goal?')) return;
    fetch(`/api/goals/${id}`, { method: 'DELETE' })
        .then(() => {
            loadGoalsList();
            showToast('Goal deleted.', 'danger');
        });
}


// --- CHAT ASSISTANT CONTROLLER ---

function initChat() {
    const chatForm = document.getElementById('chatForm');
    const chatInput = document.getElementById('chatInput');
    
    if (chatForm) {
        chatForm.addEventListener('submit', (e) => {
            e.preventDefault();
            const msg = chatInput.value.trim();
            if (!msg) return;
            
            chatInput.value = '';
            sendMessageToAI(msg);
        });
    }
}

function sendChipPrompt(promptText) {
    sendMessageToAI(promptText);
}

function sendMessageToAI(message) {
    const messagesContainer = document.getElementById('chat-messages');
    if (!messagesContainer) return;
    
    // Append user message
    const userMsgDiv = document.createElement('div');
    userMsgDiv.className = 'chat-message user';
    userMsgDiv.innerText = message;
    messagesContainer.appendChild(userMsgDiv);
    scrollChatToBottom();
    
    // Append typing indicator
    const typingDiv = document.createElement('div');
    typingDiv.className = 'chat-message assistant typing-indicator-msg';
    typingDiv.innerHTML = '<span class="text-secondary"><i class="fas fa-spinner fa-spin me-2"></i>CASHLY AI is analyzing...</span>';
    messagesContainer.appendChild(typingDiv);
    scrollChatToBottom();
    
    // AJAX Call
    fetch('/api/ai/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: message })
    })
    .then(res => res.json())
    .then(data => {
        // Remove typing
        const typingEl = messagesContainer.querySelector('.typing-indicator-msg');
        if (typingEl) typingEl.remove();
        
        if (data.error) {
            appendAssistantMessage(`An error occurred: ${data.error}`);
        } else {
            appendAssistantMessage(data.response);
        }
    })
    .catch(err => {
        const typingEl = messagesContainer.querySelector('.typing-indicator-msg');
        if (typingEl) typingEl.remove();
        appendAssistantMessage("I couldn't contact my analysis brain. Please verify that the local server is operating correctly.");
    });
}

function appendAssistantMessage(text) {
    const messagesContainer = document.getElementById('chat-messages');
    if (!messagesContainer) return;
    
    const botMsgDiv = document.createElement('div');
    botMsgDiv.className = 'chat-message assistant chat-message-markdown';
    botMsgDiv.innerHTML = parseMarkdown(text);
    messagesContainer.appendChild(botMsgDiv);
    scrollChatToBottom();
}

function scrollChatToBottom() {
    const messagesContainer = document.getElementById('chat-messages');
    if (messagesContainer) {
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }
}


// --- TOAST NOTIFICATIONS ---

function showToast(message, type = 'success') {
    // Create toast element
    const container = document.body;
    
    let existingToast = document.querySelector('.toast-custom-alert');
    if (existingToast) existingToast.remove();
    
    const toast = document.createElement('div');
    toast.className = `toast-custom-alert alert alert-${type}`;
    toast.style.position = 'fixed';
    toast.style.bottom = '20px';
    toast.style.right = '20px';
    toast.style.zIndex = '9999';
    toast.style.boxShadow = '0 10px 15px -3px rgba(0, 0, 0, 0.4)';
    toast.style.margin = '0';
    toast.style.opacity = '0';
    toast.style.transition = 'opacity 0.3s ease-out';
    toast.innerHTML = `<i class="fas ${type === 'success' ? 'fa-check-circle' : type === 'danger' ? 'fa-times-circle' : 'fa-info-circle'} me-2"></i> ${message}`;
    
    container.appendChild(toast);
    
    // Fade in
    setTimeout(() => { toast.style.opacity = '1'; }, 50);
    
    // Auto remove
    setTimeout(() => {
        toast.style.opacity = '0';
        setTimeout(() => { toast.remove(); }, 300);
    }, 3000);
}

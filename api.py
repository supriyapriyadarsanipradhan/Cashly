from flask import Blueprint, jsonify, request
from flask_login import login_required, current_user
from datetime import datetime
from models import db, Expense, Budget, Goal, User
from ai_engine import (
    suggest_category,
    calculate_financial_health_score,
    predict_future_spending,
    recommend_budgets,
    query_financial_assistant,
    db_extract_month_year
)

api_bp = Blueprint('api', __name__, url_prefix='/api')

# --- EXPENSE ENDPOINTS ---

@api_bp.route('/expenses', methods=['GET'])
@login_required
def get_expenses():
    query = Expense.query.filter_by(user_id=current_user.id)
    
    # Optional filtering
    category = request.args.get('category')
    month = request.args.get('month', type=int)
    year = request.args.get('year', type=int)
    search = request.args.get('search')
    
    if category:
        query = query.filter_by(category=category)
    if month and year:
        query = query.filter(db_extract_month_year(Expense.date, month, year))
    if search:
        query = query.filter(Expense.description.ilike(f'%{search}%'))
        
    expenses = query.order_by(Expense.date.desc(), Expense.created_at.desc()).all()
    return jsonify([e.to_dict() for e in expenses])

@api_bp.route('/expenses', methods=['POST'])
@login_required
def create_expense():
    data = request.get_json() or {}
    
    amount = data.get('amount')
    description = data.get('description', '').strip()
    date_str = data.get('date')
    category = data.get('category', '').strip()
    
    if not amount or not date_str:
        return jsonify({'error': 'Amount and Date are required fields.'}), 400
        
    try:
        amount = float(amount)
        if amount <= 0:
            return jsonify({'error': 'Amount must be greater than zero.'}), 400
    except ValueError:
        return jsonify({'error': 'Invalid amount value.'}), 400
        
    try:
        txn_date = datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError:
        return jsonify({'error': 'Invalid date format. Use YYYY-MM-DD.'}), 400
        
    # AI Autocategorization if category is not provided
    if not category or category == 'Other':
        all_user_expenses = Expense.query.filter_by(user_id=current_user.id).all()
        category = suggest_category(description, all_user_expenses)
        
    new_expense = Expense(
        user_id=current_user.id,
        amount=amount,
        category=category,
        description=description,
        date=txn_date
    )
    
    db.session.add(new_expense)
    db.session.commit()
    
    return jsonify(new_expense.to_dict()), 201

@api_bp.route('/expenses/<int:expense_id>', methods=['PUT'])
@login_required
def update_expense(expense_id):
    expense = Expense.query.filter_by(id=expense_id, user_id=current_user.id).first_or_404()
    data = request.get_json() or {}
    
    amount = data.get('amount')
    description = data.get('description')
    date_str = data.get('date')
    category = data.get('category')
    
    if amount is not None:
        try:
            amount = float(amount)
            if amount <= 0:
                return jsonify({'error': 'Amount must be greater than zero.'}), 400
            expense.amount = amount
        except ValueError:
            return jsonify({'error': 'Invalid amount value.'}), 400
            
    if date_str:
        try:
            expense.date = datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            return jsonify({'error': 'Invalid date format. Use YYYY-MM-DD.'}), 400
            
    if description is not None:
        expense.description = description.strip()
        
    if category is not None:
        expense.category = category.strip() or 'Other'
        
    db.session.commit()
    return jsonify(expense.to_dict())

@api_bp.route('/expenses/<int:expense_id>', methods=['DELETE'])
@login_required
def delete_expense(expense_id):
    expense = Expense.query.filter_by(id=expense_id, user_id=current_user.id).first_or_404()
    db.session.delete(expense)
    db.session.commit()
    return jsonify({'message': 'Expense deleted successfully.'})

@api_bp.route('/expenses/suggest-category', methods=['POST'])
@login_required
def get_suggested_category():
    data = request.get_json() or {}
    description = data.get('description', '').strip()
    
    all_user_expenses = Expense.query.filter_by(user_id=current_user.id).all()
    suggested = suggest_category(description, all_user_expenses)
    return jsonify({'category': suggested})


# --- BUDGET ENDPOINTS ---

@api_bp.route('/budgets', methods=['GET'])
@login_required
def get_budgets():
    budgets = Budget.query.filter_by(user_id=current_user.id).all()
    
    # Calculate spent amounts for current month for each budget
    today = datetime.today()
    current_month_expenses = Expense.query.filter(
        Expense.user_id == current_user.id,
        db_extract_month_year(Expense.date, today.month, today.year)
    ).all()
    
    results = []
    for b in budgets:
        spent = sum(e.amount for e in current_month_expenses if e.category == b.category)
        b_dict = b.to_dict()
        b_dict['spent'] = round(spent, 2)
        results.append(b_dict)
        
    return jsonify(results)

@api_bp.route('/budgets', methods=['POST'])
@login_required
def create_or_update_budget():
    data = request.get_json() or {}
    category = data.get('category', '').strip()
    amount = data.get('amount')
    
    if not category or amount is None:
        return jsonify({'error': 'Category and Amount are required.'}), 400
        
    try:
        amount = float(amount)
        if amount < 0:
            return jsonify({'error': 'Budget amount cannot be negative.'}), 400
    except ValueError:
        return jsonify({'error': 'Invalid budget amount.'}), 400
        
    # Check if budget already exists for this category
    budget = Budget.query.filter_by(user_id=current_user.id, category=category).first()
    if budget:
        budget.amount = amount
        status = 200
    else:
        budget = Budget(user_id=current_user.id, category=category, amount=amount)
        db.session.add(budget)
        status = 201
        
    db.session.commit()
    return jsonify(budget.to_dict()), status

@api_bp.route('/budgets/<int:budget_id>', methods=['DELETE'])
@login_required
def delete_budget(budget_id):
    budget = Budget.query.filter_by(id=budget_id, user_id=current_user.id).first_or_404()
    db.session.delete(budget)
    db.session.commit()
    return jsonify({'message': 'Budget deleted successfully.'})


# --- SAVINGS GOAL ENDPOINTS ---

@api_bp.route('/goals', methods=['GET'])
@login_required
def get_goals():
    goals = Goal.query.filter_by(user_id=current_user.id).all()
    return jsonify([g.to_dict() for g in goals])

@api_bp.route('/goals', methods=['POST'])
@login_required
def create_goal():
    data = request.get_json() or {}
    name = data.get('name', '').strip()
    target_amount = data.get('target_amount')
    current_amount = data.get('current_amount', 0.0)
    target_date_str = data.get('target_date')
    
    if not name or not target_amount or not target_date_str:
        return jsonify({'error': 'Name, target amount, and target date are required.'}), 400
        
    try:
        target_amount = float(target_amount)
        current_amount = float(current_amount)
        if target_amount <= 0 or current_amount < 0:
            return jsonify({'error': 'Amounts must be positive.'}), 400
    except ValueError:
        return jsonify({'error': 'Invalid amount value.'}), 400
        
    try:
        target_date = datetime.strptime(target_date_str, '%Y-%m-%d').date()
    except ValueError:
        return jsonify({'error': 'Invalid target date. Use YYYY-MM-DD.'}), 400
        
    new_goal = Goal(
        user_id=current_user.id,
        name=name,
        target_amount=target_amount,
        current_amount=current_amount,
        target_date=target_date
    )
    
    db.session.add(new_goal)
    db.session.commit()
    return jsonify(new_goal.to_dict()), 201

@api_bp.route('/goals/<int:goal_id>', methods=['PUT'])
@login_required
def update_goal(goal_id):
    goal = Goal.query.filter_by(id=goal_id, user_id=current_user.id).first_or_404()
    data = request.get_json() or {}
    
    name = data.get('name')
    target_amount = data.get('target_amount')
    current_amount = data.get('current_amount')
    target_date_str = data.get('target_date')
    
    if name is not None:
        goal.name = name.strip()
    if target_amount is not None:
        try:
            goal.target_amount = float(target_amount)
        except ValueError:
            return jsonify({'error': 'Invalid target amount.'}), 400
    if current_amount is not None:
        try:
            goal.current_amount = float(current_amount)
        except ValueError:
            return jsonify({'error': 'Invalid current amount.'}), 400
    if target_date_str:
        try:
            goal.target_date = datetime.strptime(target_date_str, '%Y-%m-%d').date()
        except ValueError:
            return jsonify({'error': 'Invalid target date. Use YYYY-MM-DD.'}), 400
            
    db.session.commit()
    return jsonify(goal.to_dict())

@api_bp.route('/goals/<int:goal_id>', methods=['DELETE'])
@login_required
def delete_goal(goal_id):
    goal = Goal.query.filter_by(id=goal_id, user_id=current_user.id).first_or_404()
    db.session.delete(goal)
    db.session.commit()
    return jsonify({'message': 'Goal deleted successfully.'})


# --- USER PROFILE & INCOME ---

@api_bp.route('/user/income', methods=['POST'])
@login_required
def update_income():
    data = request.get_json() or {}
    income = data.get('monthly_income')
    
    if income is None:
        return jsonify({'error': 'Monthly income is required.'}), 400
        
    try:
        income = float(income)
        if income < 0:
            return jsonify({'error': 'Income cannot be negative.'}), 400
    except ValueError:
        return jsonify({'error': 'Invalid income value.'}), 400
        
    current_user.monthly_income = income
    db.session.commit()
    
    # Auto-generate recommended budgets based on 50/30/20 rule if user does not have budgets set up
    existing_budgets = Budget.query.filter_by(user_id=current_user.id).count()
    recs_created = 0
    if existing_budgets == 0 and income > 0:
        recs = recommend_budgets(income)
        for category, amt in recs.items():
            db.session.add(Budget(user_id=current_user.id, category=category, amount=amt))
        db.session.commit()
        recs_created = len(recs)
        
    return jsonify({
        'monthly_income': current_user.monthly_income,
        'message': 'Income updated successfully.',
        'budgets_created': recs_created
    })


# --- AI INSIGHTS & ANALYTICS ---

@api_bp.route('/ai/analyze', methods=['GET'])
@login_required
def get_ai_analysis():
    today = datetime.today()
    expenses = Expense.query.filter_by(user_id=current_user.id).all()
    current_month_exps = [e for e in expenses if e.date.month == today.month and e.date.year == today.year]
    
    total_spent = sum(e.amount for e in current_month_exps)
    
    # Category totals
    category_totals = {}
    for e in current_month_exps:
        category_totals[e.category] = category_totals.get(e.category, 0.0) + e.amount
    
    # Round totals
    category_totals = {k: round(v, 2) for k, v in category_totals.items()}
    
    # Financial health score
    score, tips = calculate_financial_health_score(current_user)
    
    # Spend history for last 6 months (for frontend trends chart)
    monthly_trends = {}
    for e in expenses:
        key = e.date.strftime('%Y-%m')
        monthly_trends[key] = monthly_trends.get(key, 0.0) + e.amount
        
    # Get last 6 months in order
    sorted_trend_months = sorted(monthly_trends.keys())[-6:]
    trend_data = {m: round(monthly_trends[m], 2) for m in sorted_trend_months}
    
    return jsonify({
        'monthly_income': current_user.monthly_income,
        'current_month_spent': round(total_spent, 2),
        'category_breakdown': category_totals,
        'financial_health': {
            'score': score,
            'tips': tips
        },
        'monthly_trends': trend_data
    })

@api_bp.route('/ai/predict', methods=['GET'])
@login_required
def get_ai_prediction():
    expenses = Expense.query.filter_by(user_id=current_user.id).all()
    predicted_val, message = predict_future_spending(expenses)
    return jsonify({
        'predicted_spending': predicted_val,
        'insight': message
    })

@api_bp.route('/ai/recommend-budgets', methods=['GET'])
@login_required
def get_recommended_budgets():
    recs = recommend_budgets(current_user.monthly_income)
    return jsonify(recs)

@api_bp.route('/ai/chat', methods=['POST'])
@login_required
def chat_with_assistant():
    data = request.get_json() or {}
    message = data.get('message', '').strip()
    
    if not message:
        return jsonify({'error': 'Message is empty.'}), 400
        
    response_text = query_financial_assistant(current_user, message)
    return jsonify({'response': response_text})

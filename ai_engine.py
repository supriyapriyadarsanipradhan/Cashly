import re
from datetime import datetime, date
import statistics
from models import Expense, Budget, Goal, User

# Predefined categories and keyword matchers
CATEGORY_KEYWORDS = {
    'Food & Dining': [r'food', r'restaurant', r'grocery', r'groceries', r'mcdonald', r'starbucks', 
                      r'coffee', r'pizza', r'dinner', r'lunch', r'cafe', r'supermarket', r'eat', r'burger', r'deli'],
    'Housing & Rent': [r'rent', r'mortgage', r'landlord', r'apartment', r'housing', r'lease'],
    'Utilities & Bills': [r'electric', r'water', r'gas', r'internet', r'wifi', r'phone', r'mobile', 
                          r'bill', r'subscription', r'netflix', r'spotify', r'hulu', r'disney', r'insurance', r'power'],
    'Transportation': [r'uber', r'lyft', r'taxi', r'bus', r'subway', r'train', r'metro', r'gasoline', 
                       r'fuel', r'petrol', r'car', r'parking', r'toll', r'airline', r'flight'],
    'Entertainment': [r'movie', r'cinema', r'theater', r'game', r'steam', r'playstation', r'concert', 
                      r'show', r'pub', r'bar', r'club', r'ticket', r'museum', r'event'],
    'Shopping': [r'amazon', r'clothing', r'shoes', r'target', r'walmart', r'ebay', r'electronics', 
                 r'furniture', r'apparel', r'store', r'mall', r'gift'],
    'Health & Fitness': [r'doctor', r'dentist', r'pharmacy', r'medicine', r'hospital', r'clinic', 
                         r'health', r'fitness', r'gym', r'therapy', r'dentistry']
}

def suggest_category(description, user_expenses=None):
    """
    Suggests a category for an expense description.
    First checks historical user expenses for exact or similar descriptions.
    If no matches, falls back to keyword matching.
    """
    if not description:
        return 'Other'
        
    desc_clean = description.lower().strip()
    
    # 1. Check historical matches from the user's expenses
    if user_expenses:
        # Look for exact match first
        for exp in user_expenses:
            if exp.description and exp.description.lower().strip() == desc_clean:
                return exp.category
        
        # Look for partial matches in history
        for exp in user_expenses:
            if exp.description and (exp.description.lower().strip() in desc_clean or desc_clean in exp.description.lower().strip()):
                return exp.category
                
    # 2. Predefined keyword matching
    for category, keywords in CATEGORY_KEYWORDS.items():
        for keyword in keywords:
            if re.search(keyword, desc_clean):
                return category
                
    return 'Other'

def calculate_financial_health_score(user):
    """
    Calculates a financial health score (0-100) for a user based on:
    1. Savings rate (income vs expenses) - 40% weight
    2. Budget compliance - 30% weight
    3. Goal progress - 20% weight
    4. Expense-to-Income ratio stability - 10% weight
    """
    income = user.monthly_income
    if not income or income <= 0:
        return 50, ["Update your monthly income in profile settings to get a precise financial health score."]
        
    # Get current month expenses
    today = date.today()
    current_month_expenses = Expense.query.filter(
        Expense.user_id == user.id,
        db_extract_month_year(Expense.date, today.month, today.year)
    ).all()
    
    total_spent = sum(e.amount for e in current_month_expenses)
    
    tips = []
    
    # 1. Savings Rate Score
    savings = income - total_spent
    savings_rate = (savings / income) if income > 0 else 0
    
    if savings_rate >= 0.30:
        savings_score = 100
        tips.append("Excellent saving rate! You are saving 30%+ of your income.")
    elif savings_rate >= 0.20:
        savings_score = 85
        tips.append("Good saving rate (20%-30%). Try to invest your savings.")
    elif savings_rate >= 0.10:
        savings_score = 60
        tips.append("Moderate saving rate (10%-20%). Try to trim some non-essential expenses.")
    elif savings_rate >= 0:
        savings_score = 40
        tips.append("Low saving rate (0%-10%). You are living close to your budget limit.")
    else:
        savings_score = 10
        tips.append("Negative savings! You spent more than your income this month. Review your spending immediately.")
        
    # 2. Budget Compliance Score
    budgets = Budget.query.filter_by(user_id=user.id).all()
    budget_score = 100
    if budgets:
        over_budget_count = 0
        for b in budgets:
            category_spent = sum(e.amount for e in current_month_expenses if e.category == b.category)
            if category_spent > b.amount:
                over_budget_count += 1
                tips.append(f"You exceeded your budget for '{b.category}' by ₹{category_spent - b.amount:.2f}.")
        
        if over_budget_count > 0:
            pct_over = over_budget_count / len(budgets)
            budget_score = max(0, 100 - int(pct_over * 100))
        else:
            tips.append("Great job! You are within all your category budgets.")
    else:
        budget_score = 50
        tips.append("Set category budgets to track your limits and improve your score.")
        
    # 3. Savings Goal Progress Score
    goals = Goal.query.filter_by(user_id=user.id).all()
    goal_score = 100
    if goals:
        total_goal_progress = 0
        for g in goals:
            pct = (g.current_amount / g.target_amount) if g.target_amount > 0 else 0
            total_goal_progress += min(1.0, pct)
        avg_progress = total_goal_progress / len(goals)
        goal_score = int(avg_progress * 100)
        
        # Tip for goals
        slow_goals = [g for g in goals if (g.current_amount / g.target_amount) < 0.5 and (g.target_date - today).days < 90]
        if slow_goals:
            tips.append(f"You have {len(slow_goals)} goals approaching their deadlines with less than 50% completed.")
    else:
        goal_score = 50
        tips.append("Set financial goals (e.g., Emergency Fund) to build discipline.")
        
    # 4. Expense to Income Stability Score
    ratio = total_spent / income
    if ratio < 0.5:
        stability_score = 100
    elif ratio < 0.8:
        stability_score = 80
    elif ratio <= 1.0:
        stability_score = 50
    else:
        stability_score = 10
        
    # Final Weighted Score
    final_score = int((savings_score * 0.40) + (budget_score * 0.30) + (goal_score * 0.20) + (stability_score * 0.10))
    
    # Filter duplicate tips
    seen = set()
    unique_tips = []
    for t in tips:
        if t not in seen:
            seen.add(t)
            unique_tips.append(t)
            
    return final_score, unique_tips[:4]

def predict_future_spending(user_expenses):
    """
    Predicts next month's spending using linear regression calculated on monthly spending aggregates.
    Requires at least 2 months of historical data for linear trend, falls back to average otherwise.
    """
    if not user_expenses:
        return 0.0, "No transactions available to generate a prediction."
        
    # Group spending by month/year
    monthly_spending = {}
    for exp in user_expenses:
        key = exp.date.strftime('%Y-%m') # e.g. "2026-08"
        monthly_spending[key] = monthly_spending.get(key, 0.0) + exp.amount
        
    sorted_months = sorted(monthly_spending.keys())
    
    if len(sorted_months) < 2:
        # Fallback to simple average or current total
        avg_spending = sum(monthly_spending.values()) / len(monthly_spending) if monthly_spending else 0
        return round(avg_spending, 2), "Prediction based on historical average due to limited history (need at least 2 months)."

    # Convert sorted months to numeric indices: 0, 1, 2...
    x = list(range(len(sorted_months)))
    y = [monthly_spending[m] for m in sorted_months]
    
    # Simple linear regression calculations: y = mx + c
    n = len(x)
    sum_x = sum(x)
    sum_y = sum(y)
    sum_xx = sum(val**2 for val in x)
    sum_xy = sum(x[i] * y[i] for i in range(n))
    
    denominator = (n * sum_xx) - (sum_x ** 2)
    if denominator == 0:
        # Fallback if x coordinates are uniform (shouldn't happen with range)
        avg_spending = sum(y) / n
        return round(avg_spending, 2), "Prediction based on simple average."
        
    m = ((n * sum_xy) - (sum_x * sum_y)) / denominator
    c = (sum_y - (m * sum_x)) / n
    
    # Predict for index n (next month)
    predicted_val = (m * n) + c
    predicted_val = max(0.0, predicted_val) # spending cannot be negative
    
    trend = "increasing" if m > 0 else "decreasing"
    confidence_msg = f"Predicted spending of ₹{predicted_val:.2f} based on a {trend} monthly trend (+₹{m:.2f}/month)."
    
    return round(predicted_val, 2), confidence_msg

def recommend_budgets(monthly_income):
    """
    Recommends monthly category budgets based on the 50/30/20 rule.
    Needs (50%): Housing & Rent (30%), Utilities & Bills (10%), Transportation (10%)
    Wants (30%): Food & Dining (15%), Entertainment (10%), Shopping (5%)
    Savings (20%): Health & Fitness / General Savings (20%)
    """
    if not monthly_income or monthly_income <= 0:
        return {}
        
    recommendations = {
        'Housing & Rent': round(monthly_income * 0.30, 2),
        'Food & Dining': round(monthly_income * 0.15, 2),
        'Utilities & Bills': round(monthly_income * 0.10, 2),
        'Transportation': round(monthly_income * 0.10, 2),
        'Entertainment': round(monthly_income * 0.10, 2),
        'Shopping': round(monthly_income * 0.05, 2),
        'Health & Fitness': round(monthly_income * 0.05, 2),
        'Other': round(monthly_income * 0.05, 2)
    }
    
    return recommendations

def query_financial_assistant(user, prompt):
    """
    CASHLY AI Financial Assistant.
    Parses intent from the prompt, runs analysis on user's databases, and answers in normal language.
    """
    if not prompt:
        return "How can I help you manage your finances today?"
        
    p_clean = prompt.lower().strip()
    
    # Get current state
    today = date.today()
    all_expenses = Expense.query.filter_by(user_id=user.id).order_by(Expense.date.desc()).all()
    current_month_expenses = [e for e in all_expenses if e.date.month == today.month and e.date.year == today.year]
    total_spent_current = sum(e.amount for e in current_month_expenses)
    income = user.monthly_income
    
    # 1. Financial Health Score
    if any(k in p_clean for k in ['health score', 'financial score', 'how is my score', 'how am i doing', 'financial health']):
        score, tips = calculate_financial_health_score(user)
        tips_list = "\n".join([f"- {t}" for t in tips])
        return (f"Your CASHLY Financial Health Score is **{score}/100**.\n\n"
                f"Here are my personalized recommendations for you:\n{tips_list}")
                
    # 2. Predictions
    if any(k in p_clean for k in ['predict', 'next month', 'future spend', 'forecast', 'estimate next month']):
        val, msg = predict_future_spending(all_expenses)
        return (f"Here is my forecast for your spending next month:\n\n"
                f"**Estimated Spending: ₹{val:.2f}**\n"
                f"Analysis: {msg}\n\n"
                f"Remember, you can lower this prediction by tightening your budgets today!")

    # 3. Current Month Spending / Budgets
    if any(k in p_clean for k in ['spend this month', 'how much did i spend', 'current spending', 'spending so far']):
        if not current_month_expenses:
            return f"You haven't logged any expenses for {today.strftime('%B %Y')} yet. Add your transactions to start tracking!"
        return (f"You have spent **₹{total_spent_current:.2f}** so far in {today.strftime('%B %Y')}.\n"
                f"With a monthly income of **₹{income:.2f}**, you have **₹{max(0, income - total_spent_current):.2f}** remaining.")

    # 4. Spending Breakdown / Categories
    if any(k in p_clean for k in ['category', 'breakdown', 'where did i spend', 'top categories', 'distribution']):
        if not current_month_expenses:
            return "You don't have any expenses registered this month to analyze."
            
        cat_spending = {}
        for e in current_month_expenses:
            cat_spending[e.category] = cat_spending.get(e.category, 0.0) + e.amount
            
        sorted_cats = sorted(cat_spending.items(), key=lambda x: x[1], reverse=True)
        breakdown_str = "\n".join([f"- **{cat}**: ₹{amt:.2f} ({ (amt/total_spent_current)*100:.1f}%)" for cat, amt in sorted_cats])
        
        top_cat = sorted_cats[0][0]
        return (f"Here is your category spending breakdown for {today.strftime('%B %Y')}:\n\n"
                f"{breakdown_str}\n\n"
                f"Your highest spending category is **{top_cat}**.")

    # 5. Budgets
    if any(k in p_clean for k in ['budget', 'over budget', 'limits']):
        budgets = Budget.query.filter_by(user_id=user.id).all()
        if not budgets:
            return ("You haven't set up any budgets yet. Head over to the Budgets page to create limit alerts! "
                    "Based on your income, I recommend starting with the 50/30/20 rule.")
        
        status_lines = []
        over_budget = []
        for b in budgets:
            spent = sum(e.amount for e in current_month_expenses if e.category == b.category)
            pct = (spent / b.amount) * 100 if b.amount > 0 else 0
            status_lines.append(f"- **{b.category}**: Spent ₹{spent:.2f} of ₹{b.amount:.2f} ({pct:.1f}%)")
            if spent > b.amount:
                over_budget.append(b.category)
                
        status_str = "\n".join(status_lines)
        if over_budget:
            warning = f"\n\n⚠️ **Warning**: You are over budget in: **{', '.join(over_budget)}**!"
        else:
            warning = "\n\n✅ You are keeping within all your budgets. Excellent self-control!"
            
        return f"Here is your current budget status:\n\n{status_str}{warning}"

    # 6. Saving Tips
    if any(k in p_clean for k in ['tip', 'save money', 'advice', 'help me save', 'how to save']):
        return ("Here are 4 classic financial tips tailored for CASHLY users:\n\n"
                "1. **Adopt the 50/30/20 Rule**: Allocate 50% of your income to Needs, 30% to Wants, and 20% directly to Savings and Debt payoff.\n"
                "2. **Utilize Automatic Categorization**: Keep tags accurate to spot leakages in categories like 'Food & Dining' and 'Shopping'.\n"
                "3. **Build an Emergency Fund**: Set a target Goal of 3-6 months' expenses on your Goals page. Add to it monthly.\n"
                "4. **Analyze Before Spending**: Before buying non-essentials, wait 24 hours to see if you still feel the same urge.")

    # Fallback
    return ("Hi! I'm the CASHLY AI Assistant. I can help analyze your transactions, predict next month's spending, check budget status, or look at your financial health score.\n\n"
            "Try asking me:\n"
            "- *'What is my financial health score?'*\n"
            "- *'How much did I spend this month?'*\n"
            "- *'Where did I spend my money?'*\n"
            "- *'Predict my spending next month'*")

def db_extract_month_year(column, month, year):
    """
    SQLAlchemy-compatible filter helper to extract month and year from a Date/DateTime field.
    Works for both SQLite (using strftime) and MySQL (using MONTH() and YEAR()).
    """
    # Import here to avoid circular imports
    from sqlalchemy import extract
    return (extract('month', column) == month) & (extract('year', column) == year)

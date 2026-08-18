import unittest
from datetime import datetime, date
from app import create_app
from models import db, User, Expense, Budget, Goal
from config import Config
from ai_engine import suggest_category, recommend_budgets, predict_future_spending, calculate_financial_health_score

class TestConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:' # Use in-memory database for fast testing
    WTF_CSRF_ENABLED = False

class CashlyTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app(TestConfig)
        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()
        
        # Create a test user
        self.user = User(username='testuser', email='test@example.com', password_hash='dummyhash', monthly_income=5000.0)
        db.session.add(self.user)
        db.session.commit()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_ai_categorization(self):
        """Test rule-based keyword matching for categorization."""
        # Predefined rules
        self.assertEqual(suggest_category("Starbucks Coffee"), "Food & Dining")
        self.assertEqual(suggest_category("Uber Trip XYZ"), "Transportation")
        self.assertEqual(suggest_category("Netflix Subscription"), "Utilities & Bills")
        
        # Test historical matching fallback
        hist_expense = Expense(user_id=self.user.id, amount=100.0, category="Housing & Rent", description="Custom Landlord Fee", date=date.today())
        db.session.add(hist_expense)
        db.session.commit()
        
        all_user_expenses = Expense.query.filter_by(user_id=self.user.id).all()
        self.assertEqual(suggest_category("Custom Landlord Fee", all_user_expenses), "Housing & Rent")

    def test_budget_recommendations(self):
        """Test budget calculation based on 50/30/20 rule."""
        recs = recommend_budgets(5000.0)
        self.assertEqual(recs['Housing & Rent'], 1500.0)  # 30%
        self.assertEqual(recs['Food & Dining'], 750.0)    # 15%
        self.assertEqual(recs['Transportation'], 500.0)   # 10%

    def test_regression_prediction(self):
        """Test linear regression calculations for future spending."""
        # Simulate 3 months of spending
        exp1 = Expense(user_id=self.user.id, amount=1000.0, category="Other", description="m1", date=date(2026, 5, 15))
        exp2 = Expense(user_id=self.user.id, amount=1200.0, category="Other", description="m2", date=date(2026, 6, 15))
        exp3 = Expense(user_id=self.user.id, amount=1400.0, category="Other", description="m3", date=date(2026, 7, 15))
        db.session.add_all([exp1, exp2, exp3])
        db.session.commit()
        
        all_expenses = Expense.query.filter_by(user_id=self.user.id).all()
        pred, msg = predict_future_spending(all_expenses)
        
        # Indices: 0 (1000), 1 (1200), 2 (1400)
        # Trend is +200/month
        # Predicted for index 3 is: 1400 + 200 = 1600.0
        self.assertEqual(pred, 1600.0)
        self.assertIn("increasing", msg)

    def test_health_score(self):
        """Test calculations for financial health score."""
        # Since income is 5000, if they spend 2500, ratio is 50%, savings rate is 50%
        # Let's add some expenses for current month (August 2026 as per user request metadata)
        exp1 = Expense(user_id=self.user.id, amount=1500.0, category="Food & Dining", description="Spent", date=date(2026, 8, 10))
        db.session.add(exp1)
        db.session.commit()
        
        score, tips = calculate_financial_health_score(self.user)
        self.assertTrue(0 <= score <= 100)
        self.assertTrue(len(tips) > 0)

if __name__ == '__main__':
    unittest.main()

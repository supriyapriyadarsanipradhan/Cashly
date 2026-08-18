# 💰 Cashly — AI-Powered Personal Finance & Expense Tracker

![Python](https://img.shields.io/badge/Python-3.8+-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Flask](https://img.shields.io/badge/Flask-3.0.3-000000?style=for-the-badge&logo=flask&logoColor=white)
![SQLite](https://img.shields.io/badge/SQLite-07405E?style=for-the-badge&logo=sqlite&logoColor=white)
![JavaScript](https://img.shields.io/badge/JavaScript-ES6+-F7DF1E?style=for-the-badge&logo=javascript&logoColor=black)
![License](https://img.shields.io/badge/License-MIT-green.svg?style=for-the-badge)

**Cashly** is an intelligent, modern personal finance management and budgeting web application. Powered by Flask and an embedded AI analytics engine, Cashly helps users seamlessly track expenses, automate categorization, predict future spending trends, manage dynamic budgets (including 50/30/20 rule recommendations), track savings goals, and consult an interactive AI financial assistant.

---

## ✨ Features

- **📊 Comprehensive Financial Dashboard**: Real-time overview of monthly income, total expenses, net savings, budget utilization, and recent transactions with interactive Chart.js charts.
- **🤖 AI-Powered Auto-Categorization**: Automatically categorizes transactions based on keyword analysis and historical user spending patterns.
- **📈 Predictive Spending & Forecasting**: Regression-based analytics to forecast future month-end spending based on historical trends.
- **🎯 50/30/20 Smart Budgeting**: Set category-specific budgets with visual progress indicators, over-budget alerts, and automated budget recommendations based on the 50/30/20 financial rule.
- **🏆 Savings Goals Tracker**: Set financial targets with target dates, track progress, log contributions, and celebrate financial milestones.
- **💬 Interactive AI Financial Assistant**: Natural language financial assistant providing real-time personalized spending insights, budgeting tips, and health checks.
- **🩺 Financial Health Score (0–100)**: Proprietary multi-factor financial wellness scoring based on savings rate, budget compliance, goal trajectory, and spending stability.
- **🔐 Secure Authentication & Data Isolation**: User registration and login protected with modern password hashing (`scrypt`), session management, and per-user data isolation.
- **🗄️ Flexible Database Support**: Default zero-config SQLite with seamless support for MySQL / PostgreSQL via SQLAlchemy.

---

## 🛠️ Tech Stack

- **Backend**: Python 3, Flask, Flask-SQLAlchemy, Flask-Login, Werkzeug, PyMySQL, Cryptography
- **Frontend**: HTML5, Vanilla CSS3 (Custom Glassmorphism & Modern Dark Theme), JavaScript (ES6+), Chart.js
- **Database**: SQLite (Default) / MySQL / PostgreSQL
- **Testing**: Python `unittest` suite with in-memory SQLite fixtures

---

## 📁 Project Structure

```text
Cashly/
├── app.py              # Application factory, route registrations, server entry point
├── config.py           # Configuration settings (database URI, secret keys)
├── models.py           # SQLAlchemy database models (User, Expense, Budget, Goal)
├── auth.py             # User authentication blueprint (Register, Login, Logout)
├── api.py              # RESTful API endpoints for transactions, budgets, goals & AI
├── ai_engine.py        # AI engine for categorization, predictions, recommendations & health scoring
├── test_app.py         # Unit test suite for validation & regression testing
├── start.bat           # 1-click startup batch script for Windows
├── requirements.txt    # Python package dependencies
├── .gitignore          # Git exclusion rules
├── templates/          # Jinja2 HTML templates
│   ├── base.html       # Base layout with navigation and theme shell
│   ├── dashboard.html  # Main analytics dashboard
│   ├── expenses.html   # Expense tracking and log management
│   ├── budgets.html    # Budget creation and tracking
│   ├── goals.html      # Financial goals and milestone manager
│   ├── ai_assistant.html # Interactive AI advisor interface
│   ├── login.html      # User login page
│   └── register.html   # User registration page
└── static/             # Static web assets
    ├── css/
    │   └── style.css   # Custom CSS stylesheet
    └── js/
        └── main.js     # Frontend application logic, API calls, and charts
```

---

## 🚀 Installation & Setup Guide

### 1. Prerequisites

Ensure you have the following installed on your machine:
- **Python 3.8+** ([Download Python](https://www.python.org/downloads/))
- **Git** ([Download Git](https://git-scm.com/downloads))

---

### 2. Clone the Repository

```bash
git clone https://github.com/supriyapriyadarsanipradhan/Cashly.git
cd Cashly
```

---

### 3. Create & Activate a Virtual Environment (Recommended)

#### Windows (Command Prompt / PowerShell):
```cmd
python -m venv venv
venv\Scripts\activate
```

#### macOS / Linux:
```bash
python3 -m venv venv
source venv/bin/activate
```

---

### 4. Install Dependencies

Install all required Python packages using `pip`:

```bash
pip install -r requirements.txt
```

---

## ▶️ Running the Application

### Option A: One-Click Quick Start (Windows)
Double-click `start.bat` or run it from your command prompt:
```cmd
start.bat
```
*This automatically launches your browser to `http://127.0.0.1:5000/` and starts the Flask server.*

---

### Option B: Manual Startup

Run the Flask application via Python:
```bash
python app.py
```

Open your web browser and navigate to:
```
http://127.0.0.1:5000/
```

---

## ⚙️ Configuration & Environment Variables

Cashly works out of the box with zero configuration using SQLite. If you wish to customize your configuration or connect to a MySQL/PostgreSQL database, configure the following environment variables:

| Variable | Default | Description |
| :--- | :--- | :--- |
| `SECRET_KEY` | `cashly-secret-key-3982471047-xyz` | Secret key for session security |
| `DATABASE_URL` | `sqlite:///cashly.db` | SQLAlchemy database connection string |

#### Example: Using MySQL
```bash
# Windows PowerShell
$env:DATABASE_URL="mysql+pymysql://username:password@localhost:3306/cashly"
python app.py

# Linux / macOS
export DATABASE_URL="mysql+pymysql://username:password@localhost:3306/cashly"
python app.py
```

---

## 🧪 Running Automated Tests

Cashly comes with a comprehensive suite of unit tests verifying AI logic, budget calculations, predictions, and health score algorithms:

```bash
python -m unittest test_app.py
```

---

## 📡 REST API Overview

Cashly provides a modular RESTful API under `/api`:

| Endpoint | Method | Description |
| :--- | :--- | :--- |
| `/api/expenses` | `GET` | Retrieve list of expenses (with optional filters) |
| `/api/expenses` | `POST` | Add a new expense (with AI auto-categorization) |
| `/api/expenses/<id>` | `PUT` | Update an existing expense |
| `/api/expenses/<id>` | `DELETE` | Delete an expense |
| `/api/budgets` | `GET` | Fetch all user budgets & spending progress |
| `/api/budgets` | `POST` | Create or update category budgets |
| `/api/budgets/<id>` | `DELETE` | Remove a budget |
| `/api/budgets/recommend` | `GET` | Get 50/30/20 rule budget recommendations |
| `/api/goals` | `GET` | Fetch all financial goals |
| `/api/goals` | `POST` | Create a new financial goal |
| `/api/goals/<id>` | `PUT` | Update goal or record contributions |
| `/api/goals/<id>` | `DELETE` | Remove a financial goal |
| `/api/ai/health-score` | `GET` | Calculate current financial health score & tips |
| `/api/ai/predict` | `GET` | Generate spending trend forecast |
| `/api/ai/assistant` | `POST` | Query conversational AI financial assistant |
| `/api/dashboard/stats` | `GET` | Fetch aggregated monthly statistics for dashboard |

---

## 🤝 Contributing

Contributions, issues, and feature requests are welcome!
1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

---

## 📝 License

Distributed under the MIT License. See `LICENSE` for more information.

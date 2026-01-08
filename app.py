import sqlite3
from datetime import datetime
from typing import Dict, List
from flask import Flask, jsonify, request, render_template
from flask_cors import CORS

app = Flask(__name__)
CORS(app)


class BusinessDashboard:
    """Main business dashboard class for managing employees and sales with SQLite"""

    def __init__(self, db_name: str = "business_dashboard.db"):
        self.db_name = db_name
        self._init_database()

    def get_connection(self):
        conn = sqlite3.connect(self.db_name)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_database(self):
        conn = self.get_connection()
        cursor = conn.cursor()

        # Create employees table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS employees (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                position TEXT NOT NULL,
                salary REAL NOT NULL,
                hired_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Create sales table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS sales (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                product TEXT NOT NULL,
                amount REAL NOT NULL,
                customer TEXT NOT NULL,
                sale_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        conn.commit()
        conn.close()

    # Employee methods
    def add_employee(self, name: str, position: str, salary: float) -> bool:
        if not name or not position or salary < 0:
            return False
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO employees (name, position, salary, hired_date)
                VALUES (?, ?, ?, ?)
            ''', (name, position, salary, datetime.now()))
            conn.commit()
            conn.close()
            return True
        except sqlite3.Error:
            return False

    def get_employees(self) -> List[Dict]:
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM employees ORDER BY id DESC')
        result = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return result

    def get_employee_count(self) -> int:
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) as count FROM employees')
        count = cursor.fetchone()['count']
        conn.close()
        return count

    # Sales methods
    def add_sale(self, product: str, amount: float, customer: str) -> bool:
        if not product or not customer or amount <= 0:
            return False
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO sales (product, amount, customer, sale_date)
                VALUES (?, ?, ?, ?)
            ''', (product, amount, customer, datetime.now()))
            conn.commit()
            conn.close()
            return True
        except sqlite3.Error:
            return False

    def get_sales(self) -> List[Dict]:
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM sales ORDER BY id DESC LIMIT 100')
        result = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return result

    def get_total_revenue(self) -> float:
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT COALESCE(SUM(amount), 0) as total FROM sales')
        total = cursor.fetchone()['total']
        conn.close()
        return total

    def get_sales_count(self) -> int:
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) as count FROM sales')
        count = cursor.fetchone()['count']
        conn.close()
        return count

    def get_average_sale(self) -> float:
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT AVG(amount) as avg FROM sales')
        result = cursor.fetchone()['avg']
        conn.close()
        return result if result else 0.0

    def get_dashboard_summary(self) -> Dict:
        return {
            "total_employees": self.get_employee_count(),
            "total_sales": self.get_sales_count(),
            "total_revenue": self.get_total_revenue(),
            "average_sale": self.get_average_sale(),
        }


# Initialize dashboard
dashboard = BusinessDashboard()


# Flask routes

@app.route("/")
def dashboard_ui():
    """Main combined dashboard view with summary, employees and sales."""
    summary = dashboard.get_dashboard_summary()
    employees = dashboard.get_employees()
    sales = dashboard.get_sales()
    return render_template(
        "dashboard.html",
        summary=summary,
        employees=employees,
        sales=sales,
    )


@app.route("/employees")
def employees_page():
    """Employees management page."""
    employees = dashboard.get_employees()
    summary = dashboard.get_dashboard_summary()
    return render_template(
        "employees.html",
        summary=summary,
        employees=employees,
    )


@app.route("/sales")
def sales_page():
    """Sales management page."""
    sales = dashboard.get_sales()
    summary = dashboard.get_dashboard_summary()
    return render_template(
        "sales.html",
        summary=summary,
        sales=sales,
    )


@app.route('/health')
def health():
    return jsonify({"status": "healthy", "timestamp": datetime.now().isoformat()})


@app.route('/api/dashboard')
def get_dashboard():
    return jsonify(dashboard.get_dashboard_summary())


@app.route('/api/employees', methods=['GET'])
def get_employees():
    employees = dashboard.get_employees()
    return jsonify({"employees": employees, "count": len(employees)})


@app.route('/api/employees', methods=['POST'])
def add_employee():
    data = request.get_json()
    try:
        name = data.get('name')
        position = data.get('position')
        salary = float(data.get('salary'))
    except (TypeError, ValueError):
        return jsonify({"error": "Invalid input"}), 400
    if not name or not position or salary < 0:
        return jsonify({"error": "Invalid employee data"}), 400

    success = dashboard.add_employee(name, position, salary)
    return (
        jsonify({"message": "Employee added successfully"}), 201
        if success else
        (jsonify({"error": "Failed to add employee"}), 400)
    )


@app.route('/api/sales', methods=['GET'])
def get_sales():
    sales = dashboard.get_sales()
    return jsonify({"sales": sales, "count": len(sales)})


@app.route('/api/sales', methods=['POST'])
def add_sale():
    data = request.get_json()
    try:
        product = data.get('product')
        customer = data.get('customer')
        amount = float(data.get('amount'))
    except (TypeError, ValueError):
        return jsonify({"error": "Invalid input"}), 400
    if not product or not customer or amount <= 0:
        return jsonify({"error": "Invalid sale data"}), 400

    success = dashboard.add_sale(product, amount, customer)
    return (
        jsonify({"message": "Sale added successfully"}), 201
        if success else
        (jsonify({"error": "Failed to add sale"}), 400)
    )


if __name__ == '__main__':
    # Seed sample data if empty
    if dashboard.get_employee_count() == 0:
        dashboard.add_employee("John Doe", "Manager", 75000)
        dashboard.add_employee("Jane Smith", "Developer", 85000)
        dashboard.add_sale("Product A", 1200.50, "Acme Corp")
        dashboard.add_sale("Product B", 850.00, "Tech Industries")

    app.run(debug=True, host='0.0.0.0', port=5000)

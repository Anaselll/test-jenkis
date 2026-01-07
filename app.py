
import sqlite3
from datetime import datetime
from typing import Dict, List, Optional
from flask import Flask, jsonify, request, render_template
from flask_cors import CORS

app = Flask(__name__)
CORS(app)


class BusinessDashboard:
    """Main business dashboard class for managing metrics and data with SQLite"""
    
    def __init__(self, db_name: str = "business_dashboard.db"):
        self.db_name = db_name
        self._init_database()
    
    def get_connection(self):
        """Get a new database connection"""
        conn = sqlite3.connect(self.db_name)
        conn.row_factory = sqlite3.Row
        return conn
    
    def _init_database(self):
        """Initialize database and create tables"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Create metrics table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS metrics (
                name TEXT PRIMARY KEY,
                value REAL NOT NULL,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
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
    
    def add_metric(self, name: str, value: float) -> bool:
        """Add or update a business metric"""
        if not name or not isinstance(value, (int, float)):
            return False
        
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO metrics (name, value, updated_at)
                VALUES (?, ?, ?)
                ON CONFLICT(name) DO UPDATE SET
                    value = excluded.value,
                    updated_at = excluded.updated_at
            ''', (name, float(value), datetime.now()))
            conn.commit()
            conn.close()
            return True
        except sqlite3.Error:
            return False
    
    def get_metric(self, name: str) -> Optional[float]:
        """Get a specific metric value"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT value FROM metrics WHERE name = ?', (name,))
        row = cursor.fetchone()
        conn.close()
        return row['value'] if row else None
    
    def get_all_metrics(self) -> Dict[str, float]:
        """Get all metrics"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT name, value FROM metrics')
        result = {row['name']: row['value'] for row in cursor.fetchall()}
        conn.close()
        return result
    
    def add_employee(self, name: str, position: str, salary: float) -> bool:
        """Add a new employee"""
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
        """Get all employees"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM employees ORDER BY id DESC')
        result = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return result
    
    def get_employee_count(self) -> int:
        """Get total number of employees"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) as count FROM employees')
        count = cursor.fetchone()['count']
        conn.close()
        return count
    
    def add_sale(self, product: str, amount: float, customer: str) -> bool:
        """Record a new sale"""
        if not product or amount <= 0 or not customer:
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
        """Get all sales"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM sales ORDER BY id DESC LIMIT 100')
        result = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return result
    
    def get_total_revenue(self) -> float:
        """Calculate total revenue from all sales"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT COALESCE(SUM(amount), 0) as total FROM sales')
        total = cursor.fetchone()['total']
        conn.close()
        return total
    
    def get_sales_count(self) -> int:
        """Get total number of sales"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) as count FROM sales')
        count = cursor.fetchone()['count']
        conn.close()
        return count
    
    def get_average_sale(self) -> float:
        """Calculate average sale amount"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT AVG(amount) as avg FROM sales')
        result = cursor.fetchone()['avg']
        conn.close()
        return result if result else 0.0
    
    def get_dashboard_summary(self) -> Dict:
        """Get a complete dashboard summary"""
        return {
            "total_employees": self.get_employee_count(),
            "total_sales": self.get_sales_count(),
            "total_revenue": self.get_total_revenue(),
            "average_sale": self.get_average_sale(),
            "metrics": self.get_all_metrics()
        }


# Initialize dashboard
dashboard = BusinessDashboard()


@app.route('/')
def dashboard_ui():
    summary = dashboard.get_dashboard_summary()
    employees = dashboard.get_employees()
    sales = dashboard.get_sales()

    return render_template(
        "dashboard.html",
        summary=summary,
        employees=employees,
        sales=sales
    )
@app.route('/health')
def health():
    """Health check endpoint"""
    return jsonify({"status": "healthy", "timestamp": datetime.now().isoformat()})


@app.route('/api/dashboard')
def get_dashboard():
    """Get complete dashboard summary"""
    summary = dashboard.get_dashboard_summary()
    return jsonify(summary)


@app.route('/api/metrics', methods=['GET'])
def get_metrics():
    """Get all metrics"""
    metrics = dashboard.get_all_metrics()
    return jsonify({"metrics": metrics})


@app.route('/api/metrics', methods=['POST'])
def add_metric():
    data = request.get_json()

    try:
        name = data.get('name')
        value = float(data.get('value'))
    except (TypeError, ValueError):
        return jsonify({"error": "Invalid input"}), 400

    if not name:
        return jsonify({"error": "Metric name required"}), 400

    success = dashboard.add_metric(name, value)

    return (
        jsonify({"message": "Metric added successfully"}), 201
        if success else
        (jsonify({"error": "Failed to add metric"}), 400)
    )

@app.route('/api/employees', methods=['GET'])
def get_employees():
    """Get all employees"""
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
    """Get all sales"""
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
    # Initialize with some sample data on first run
    if dashboard.get_employee_count() == 0:
        dashboard.add_metric("customer_satisfaction", 4.5)
        dashboard.add_metric("monthly_growth", 12.5)
        dashboard.add_employee("John Doe", "Manager", 75000)
        dashboard.add_employee("Jane Smith", "Developer", 85000)
        dashboard.add_sale("Product A", 1200.50, "Acme Corp")
        dashboard.add_sale("Product B", 850.00, "Tech Industries")
    
    app.run(debug=True, host='0.0.0.0', port=5000)
from flask import Flask, render_template, request, redirect
import mysql.connector
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

db = mysql.connector.connect(
    host=os.getenv("DB_HOST"),
    user=os.getenv("DB_USER"),
    password=os.getenv("DB_PASSWORD"),
    database=os.getenv("DB_NAME")
)

cursor = db.cursor()

@app.route('/')
def index():
    cursor.execute("SELECT * FROM suppliers")
    suppliers = cursor.fetchall()

    cursor.execute("SELECT * FROM products")
    products = cursor.fetchall()

    cursor.execute("""
        SELECT sp.supplier_id, sp.product_id, s.name, p.product_name, sp.quantity_supplied, sp.supply_date
        FROM supplier_products sp
        JOIN suppliers s ON sp.supplier_id = s.supplier_id
        JOIN products p ON sp.product_id = p.product_id
    """)
    supply = cursor.fetchall()

    return render_template(
        'index.html',
        suppliers=suppliers,
        products=products,
        supply=supply
    )

@app.route('/add_supplier', methods=['GET', 'POST'])
def add_supplier():
    error = None

    if request.method == 'POST':
        supplier_id = request.form['supplier_id']
        name = request.form['name']
        email = request.form['email']
        city = request.form['city']

        try:
            cursor.execute(
                "INSERT INTO suppliers VALUES (%s, %s, %s, %s)",
                (supplier_id, name, email, city)
            )
            db.commit()
            return redirect('/')
        except:
            error = "Supplier ID already exists"

    return render_template('add_supplier.html', error=error)

@app.route('/add_product', methods=['GET', 'POST'])
def add_product():
    error = None

    if request.method == 'POST':
        product_id = request.form['product_id']
        name = request.form['name']
        category = request.form['category']
        price = request.form['price']

        try:
            cursor.execute(
                "INSERT INTO products VALUES (%s, %s, %s, %s)",
                (product_id, name, category, price)
            )
            db.commit()
            return redirect('/')
        except:
            error = "Product ID already exists"

    return render_template('add_product.html', error=error)

@app.route('/link_supply', methods=['GET', 'POST'])
def link_supply():
    if request.method == 'POST':
        supplier_id = request.form['supplier_id']
        product_id = request.form['product_id']
        quantity = request.form['quantity']
        date = request.form['date']

        cursor.execute(
            "INSERT INTO supplier_products VALUES (%s, %s, %s, %s)",
            (supplier_id, product_id, quantity, date)
        )
        db.commit()
        return redirect('/')

    cursor.execute("SELECT supplier_id, name FROM suppliers")
    suppliers = cursor.fetchall()

    cursor.execute("SELECT product_id, product_name FROM products")
    products = cursor.fetchall()

    return render_template(
        'link_supply.html',
        suppliers=suppliers,
        products=products
    )

@app.route('/delete_supplier/<int:id>')
def delete_supplier(id):
    cursor.execute("DELETE FROM suppliers WHERE supplier_id = %s", (id,))
    db.commit()
    return redirect('/')


@app.route('/delete_product/<int:id>')
def delete_product(id):
    cursor.execute("DELETE FROM products WHERE product_id = %s", (id,))
    db.commit()
    return redirect('/')


@app.route('/delete_supply/<int:sid>/<int:pid>/<date>')
def delete_supply(sid, pid, date):
    cursor.execute(
        "DELETE FROM supplier_products WHERE supplier_id=%s AND product_id=%s AND supply_date=%s",
        (sid, pid, date)
    )
    db.commit()
    return redirect('/')


@app.route('/update_supplier/<int:id>', methods=['GET', 'POST'])
def update_supplier(id):
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        city = request.form['city']

        cursor.execute(
            "UPDATE suppliers SET name=%s, contact_email=%s, city=%s WHERE supplier_id=%s",
            (name, email, city, id)
        )
        db.commit()
        return redirect('/')

    cursor.execute("SELECT * FROM suppliers WHERE supplier_id=%s", (id,))
    supplier = cursor.fetchone()
    return render_template('update_supplier.html', supplier=supplier)


@app.route('/update_product/<int:id>', methods=['GET', 'POST'])
def update_product(id):
    if request.method == 'POST':
        name = request.form['name']
        category = request.form['category']
        price = request.form['price']

        cursor.execute(
            "UPDATE products SET product_name=%s, category=%s, price=%s WHERE product_id=%s",
            (name, category, price, id)
        )
        db.commit()
        return redirect('/')

    cursor.execute("SELECT * FROM products WHERE product_id=%s", (id,))
    product = cursor.fetchone()
    return render_template('update_product.html', product=product)

@app.route('/analytics')
def analytics():

    cursor.execute("""
        SELECT s.supplier_id, s.name, SUM(sp.quantity_supplied) AS total_supply
        FROM supplier_products sp
        JOIN suppliers s ON sp.supplier_id = s.supplier_id
        GROUP BY s.supplier_id, s.name
    """)
    supplier_performance = cursor.fetchall()

    cursor.execute("""
        SELECT s.name, SUM(sp.quantity_supplied) AS total_supply
        FROM supplier_products sp
        JOIN suppliers s ON sp.supplier_id = s.supplier_id
        GROUP BY s.name
        ORDER BY total_supply DESC
        LIMIT 5
    """)
    top_suppliers = cursor.fetchall()

    cursor.execute("""
        SELECT p.product_name, SUM(sp.quantity_supplied) AS total_supply
        FROM supplier_products sp
        JOIN products p ON sp.product_id = p.product_id
        GROUP BY p.product_name
        HAVING total_supply < 50
    """)
    low_products = cursor.fetchall()

    cursor.execute("""
        SELECT DATE_FORMAT(supply_date, '%Y-%m') AS month,
               SUM(quantity_supplied) AS total
        FROM supplier_products
        GROUP BY month
        ORDER BY month
    """)
    monthly_trend = cursor.fetchall()

    cursor.execute("""
        SELECT p.category, SUM(sp.quantity_supplied) AS total
        FROM supplier_products sp
        JOIN products p ON sp.product_id = p.product_id
        GROUP BY p.category
    """)
    category_data = cursor.fetchall()

    cursor.execute("""
        SELECT DISTINCT s.name
        FROM supplier_products sp
        JOIN suppliers s ON sp.supplier_id = s.supplier_id
        WHERE sp.supply_date >= DATE_SUB(CURDATE(), INTERVAL 30 DAY)
    """)
    active_suppliers = cursor.fetchall()

    cursor.execute("SELECT COUNT(*) FROM suppliers")
    total_suppliers = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM products")
    total_products = cursor.fetchone()[0]

    cursor.execute("SELECT IFNULL(SUM(quantity_supplied), 0) FROM supplier_products")
    total_quantity = cursor.fetchone()[0]

    cursor.execute("""
        SELECT COUNT(DISTINCT supplier_id)
        FROM supplier_products
        WHERE supply_date >= DATE_SUB(CURDATE(), INTERVAL 30 DAY)
    """)
    active_supplier_count = cursor.fetchone()[0]

    return render_template(
        'analytics.html',
        supplier_performance=supplier_performance,
        top_suppliers=top_suppliers,
        low_products=low_products,
        monthly_trend=monthly_trend,
        category_data=category_data,
        active_suppliers=active_suppliers,
        total_suppliers=total_suppliers,
        total_products=total_products,
        total_quantity=total_quantity,
        active_supplier_count=active_supplier_count
    )

if __name__ == '__main__':
    app.run(debug=True)
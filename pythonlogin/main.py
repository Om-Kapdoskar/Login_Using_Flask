from flask import Flask, render_template, request, redirect, url_for, session
from flask_mysqldb import MySQL
import MySQLdb.cursors
import re
import hashlib
app = Flask(__name__)
app.secret_key = 'your_secret_key'
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'root'
app.config['MYSQL_DB'] = 'pythonlogin'
mysql = MySQL(app)
@app.route('/', methods=['GET', 'POST'])
def login():
    msg = ''
    if request.method == 'POST' and 'username' in request.form and 'password' in request.form:
        username = request.form['username']
        password = request.form['password']
        hash = hashlib.sha1((password + app.secret_key).encode()).hexdigest()
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM accounts WHERE username = %s AND password = %s', (username, hash,))
        account = cursor.fetchone()
        if account:
            session['loggedin'] = True
            session['id'] = account['id']
            session['username'] = account['username']
            return redirect(url_for('home'))
        else:
            msg = 'Incorrect username/password!'
    return render_template('index.html', msg=msg)

@app.route('/pythonlogin/register', methods=['GET', 'POST'])
def register():
    msg = ''
    if request.method == 'POST' and 'username' in request.form and 'password' in request.form and 'email' in request.form:
        username = request.form['username']
        password = request.form['password']
        email = request.form['email']
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM accounts WHERE username = %s', (username,))
        account = cursor.fetchone()
        if account:
            msg = 'Account already exists!'
        elif not re.match(r'[^@]+@[^@]+\.[^@]+', email):
            msg = 'Invalid email address!'
        elif not re.match(r'[A-Za-z0-9]+', username):
            msg = 'Username must contain only characters and numbers!'
        elif not username or not password or not email:
            msg = 'Please fill out the form!'
        else:
            hash = hashlib.sha1((password + app.secret_key).encode()).hexdigest()
            cursor.execute('INSERT INTO accounts VALUES (NULL, %s, %s, %s)', (username, hash, email,))
            mysql.connection.commit()
            msg = 'You have successfully registered!'
    elif request.method == 'POST':
        msg = 'Please fill out the form!'
    return render_template('register.html', msg=msg)
@app.route('/pythonlogin/home', methods = ['GET','POST'])
def home():
    if 'loggedin' in session:
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        if request.method == 'POST':
            search_term = request.form.get('search_term')
            if search_term:
                cursor.execute("""SELECT p.prodid,p.name AS product_name,p.price,p.desc AS description,p.img AS image_url,s.sname AS supplier_name FROM products p
                    INNER JOIN supplier s ON p.sid = s.sid WHERE name LIKE %s""",(search_term,))
                products = cursor.fetchall()
            else:
                cursor.execute("""SELECT p.prodid,p.name AS product_name,p.price,p.desc AS description,p.img AS image_url,s.sname AS supplier_name FROM products p
                    INNER JOIN supplier s ON p.sid = s.sid;""")
                products = cursor.fetchall()
        else:
            cursor.execute("""SELECT p.prodid,p.name AS product_name,p.price,p.desc AS description,p.img AS image_url,s.sname AS supplier_name FROM products p
                    INNER JOIN supplier s ON p.sid = s.sid;""")
            products = cursor.fetchall()
        return render_template('home.html', p=products)
    return redirect(url_for('login'))
@app.route('/pythonlogin/profile')
def profile():
    if 'loggedin' in session:
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM accounts WHERE id = %s', (session['id'],))
        account = cursor.fetchone()
        return render_template('profile.html', account=account)
    return redirect(url_for('login'))
@app.route('/pythonlogin/cart')
def cart():
    if 'loggedin' in session:
        user_id = session['id']
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT p.name AS product_name, c.quantity,c.cart_id FROM cart c JOIN products p ON c.product_id = p.prodid WHERE c.user_id = %s', (user_id,))
        cart_items = cursor.fetchall()
        cursor.close()
        return render_template('cart.html', cart_items=cart_items)
    return redirect(url_for('login'))
@app.route('/add_to_cart/<int:product_id>', methods=['POST'])
def add_to_cart(product_id):
    if 'loggedin' in session:
        user_id = session['id']
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM cart WHERE user_id = %s AND product_id = %s', (user_id, product_id))
        cart_item = cursor.fetchone()
        if cart_item:
            cursor.execute('UPDATE cart SET quantity = quantity + 1 WHERE cart_id = %s', (cart_item['cart_id'],))
        else:
            cursor.execute('INSERT INTO cart (user_id, product_id, quantity) VALUES (%s, %s, 1)', (user_id, product_id))
        mysql.connection.commit()
        cursor.close()
        return redirect(url_for('home'))
    return redirect(url_for('login'))
@app.route('/remove_from_cart/<int:cart_id>', methods=['POST'])
def remove_from_cart(cart_id):
    if 'loggedin' in session:
        user_id = session['id']
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM cart WHERE user_id = %s AND cart_id = %s', (user_id, cart_id))
        cart_item = cursor.fetchone()
        if cart_item:
            cursor.execute('DELETE FROM cart WHERE cart_id = %s', (cart_id,))
            mysql.connection.commit()
        cursor.close()
        return redirect(url_for('cart'))
    return redirect(url_for('login'))
if __name__ == '__main__':
    app.run(debug=True)
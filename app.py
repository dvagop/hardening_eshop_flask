from flask import Flask, render_template, request, redirect, url_for, flash, session, make_response
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import InputRequired, Email, Length
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import or_
import os
from datetime import datetime
from flask_mail import Mail, Message

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ['DB_CONNECTION_STRING']
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = os.environ.get('SECRET_KEY', 'your_secret_key')

app.config['MAIL_SERVER'] = 'smtp.googlemail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD')
app.config['MAIL_DEFAULT_SENDER'] = os.environ.get('MAIL_USERNAME')

mail = Mail(app)
db = SQLAlchemy(app)

def send_order_confirmation_email(order, user, cart_items):
    admin_email = os.environ.get('MAIL_USERNAME')

    subject = 'New Order Confirmation'
    body = f"""
    Order ID: {order.order_id}
    User: {user.username} ({user.email})
    Total Price: ${order.total_price}
    Shipping Address: {order.shipping_address}
    Shipped Status: {order.shipped_status}
    Order Date: {order.order_date}

    Products:
    """
    for item in cart_items:
        body += f"- {item.product.name}: ${item.price}\n"

    msg = Message(subject, recipients=[admin_email])
    msg.body = body

    mail.send(msg)

# Define the User model
class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(150), nullable=False)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(250), nullable=False)
    address = db.Column(db.String(150), nullable=False)

    carts = db.relationship('Carts', backref='user', lazy=True)
    orders = db.relationship('Orders', backref='user', lazy=True)

# Define the Product model
class Product(db.Model):
    __tablename__ = 'products'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    description = db.Column(db.String(50), nullable=False)
    price = db.Column(db.Numeric(10, 2), nullable=False) 

    carts = db.relationship('Carts', backref='product', lazy=True)

# Define the Carts model
class Carts(db.Model):
    __tablename__ = 'carts'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    price = db.Column(db.Numeric(10, 2), nullable=False) 
    date = db.Column(db.DateTime, nullable=False, server_default=db.func.current_timestamp())
    purchased = db.Column(db.Boolean, nullable=False, default=False)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.order_id'))

# Define the Orders model
class Orders(db.Model):
    __tablename__ = 'orders'
    order_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    shipped_status = db.Column(db.String(50))
    order_date = db.Column(db.DateTime, nullable=False, server_default=db.func.current_timestamp())
    total_price = db.Column(db.Numeric(10, 2), nullable=False)
    shipping_address = db.Column(db.String(150), nullable=False)

# Define the RegistrationForm using Flask-WTF
class RegistrationForm(FlaskForm):
    first_name = StringField('First Name', validators=[InputRequired()])
    last_name = StringField('Last Name', validators=[InputRequired()])
    email = StringField('Email', validators=[InputRequired(), Email()])
    username = StringField('Username', validators=[InputRequired(), Length(min=4, max=50)])
    password = PasswordField('Password', validators=[InputRequired(), Length(min=6, max=250)])
    address = StringField('Address', validators=[InputRequired()])
    submit = SubmitField('Register')

# Route for user registration
@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        new_user = User(
            first_name=form.first_name.data,
            last_name=form.last_name.data,
            email=form.email.data,
            username=form.username.data,
            password=generate_password_hash(form.password.data),
            address=form.address.data
        )
        db.session.add(new_user)
        db.session.commit()
        flash('Registration successful! You can now login.', 'success')
        return redirect(url_for('login'))
    return render_template('register.html', form=form)

# Define the LoginForm using Flask-WTF
class LoginForm(FlaskForm):
    username = StringField('Username', validators=[InputRequired()])
    password = PasswordField('Password', validators=[InputRequired()])
    submit = SubmitField('Login')

# Route for the login page
@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            flash('Login successful!', 'success')
            session['username'] = username
            return redirect(url_for('products'))
        else:
            flash('Invalid username or password', 'error')
    return render_template('login.html', form=form)

@app.route('/logout')
def logout():
    if 'username' in session:
        username = session.get('username')
        user = User.query.filter_by(username=username).first()
        if user:
            # Delete all cart items for the user, regardless of purchase status
            try:
                num_deleted = Carts.query.filter_by(user_id=user.id).delete()
                db.session.commit()
                flash(f'All cart items cleared. {num_deleted} items were removed.', 'success')
            except Exception as e:
                db.session.rollback()
                app.logger.error("Failed to delete cart items: %s", str(e))
                flash('Failed to clear cart items due to an error.', 'error')
        else:
            flash('User not found.', 'error')

        session.pop('username', None)
        session.clear()
        flash('You have been logged out.', 'success')
    else:
        flash('No user session found.', 'error')

    return redirect(url_for('login'))




# Route for products page
@app.route('/products', methods=['GET'])
def products():
    if 'username' not in session:
        return redirect(url_for('login'))

    search_query = request.args.get('search_query', '')
    if search_query:
        search_results = Product.query.filter(or_(Product.name.ilike(f'%{search_query}%'),
                                                  Product.description.ilike(f'%{search_query}%'))).all()
        num_results = len(search_results)
        total_products = Product.query.count()
    else:
        search_results = []
        num_results = 0
        total_products = Product.query.count()

    current_user = User.query.filter_by(username=session['username']).first()
    cart_items = current_user.carts

    return render_template('products.html', search_results=search_results, 
                           num_results=num_results, total_products=total_products, 
                           search_query=search_query, cart_items=cart_items)

# Route to add a product to the cart
@app.route('/add_to_cart/<int:product_id>', methods=['POST'])
def add_to_cart(product_id):
    if 'username' not in session:
        return redirect(url_for('login'))

    user = User.query.filter_by(username=session['username']).first()
    product = Product.query.get_or_404(product_id)

    new_cart_entry = Carts(user_id=user.id, product_id=product_id, price=product.price)
    db.session.add(new_cart_entry)
    db.session.commit()

    flash('Product added to cart successfully!', 'success')
    return redirect(url_for('products'))

@app.route('/cart', methods=['GET'])
def cart():
    if 'username' not in session:
        return redirect(url_for('login'))

    current_user = User.query.filter_by(username=session['username']).first()
    cart_items = Carts.query.filter_by(user_id=current_user.id, purchased=False).all()
    total_price = sum(item.price for item in cart_items)

    return render_template('carts.html', cart_items=cart_items, total_price=total_price)


@app.route('/checkout', methods=['POST'])
def checkout():
    if 'username' not in session:
        return redirect(url_for('login'))

    user = User.query.filter_by(username=session['username']).first()
    cart_items = Carts.query.filter_by(user_id=user.id, purchased=False).all()
    total_price = sum(item.price for item in cart_items)
    shipping_address = request.form.get('shipping_address')

    new_order = Orders(
        user_id=user.id,
        shipped_status='Completed',
        order_date=datetime.utcnow(),
        total_price=total_price,
        shipping_address=shipping_address
    )
    db.session.add(new_order)
    db.session.commit()

    for item in cart_items:
        item.purchased = True
        item.order_id = new_order.order_id
    db.session.commit()

    send_order_confirmation_email(new_order, user, cart_items)

    flash('Order placed successfully!', 'success')
    return redirect(url_for('products'))



# Route for the home page
@app.route('/')
def home():
    return 'Welcome to the Home Page!'

if __name__ == '__main__':
    app.run(debug=True)





# from flask import Flask, render_template, jsonify, request

# from database import load_jobs_from_db, load_job_from_db, add_application_to_db 

# app = Flask(__name__)

# @app.route("/")
# def index():
#     jobs=load_jobs_from_db()
#     return render_template('home.html', jobs=jobs, owner='Fallout')

# @app.route("/api/jobs")
# def list_jobs():
#     jobs=load_jobs_from_db()
#     return jsonify(jobs)

# @app.route("/job/<id>")
# def show_job(id):
#     job=load_job_from_db(id)
#     if not job:
#         return "Not Found", 404
#     return render_template('jobpage.html', job=job)

# @app.route("/job/<id>/apply", methods= ['post'])
# def apply_to_job(id):
#     data=request.form

#     job=load_job_from_db(id)
#     add_application_to_db(id, data)
#     return render_template('application_submitted.html', application=data, job=job)
    
    
#if __name__=="__main__":
#    app.run(host='0.0.0.0', debug=True)

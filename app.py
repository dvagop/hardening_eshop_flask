from flask import Flask, render_template, request, redirect, url_for, flash, session, send_file
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm, CSRFProtect
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import InputRequired, Email, Length, ValidationError
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.middleware.proxy_fix import ProxyFix
from sqlalchemy import or_
from flask_mail import Mail, Message
from flask_login import LoginManager, login_user, logout_user, login_required, UserMixin, current_user
import os
from datetime import datetime
from dotenv import load_dotenv
from captcha.image import ImageCaptcha
import io
import random
import string

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__, static_url_path='/static')
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'default_secret')
csrf = CSRFProtect(app)
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ['DB_CONNECTION_STRING']
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['MAIL_SERVER'] = 'smtp.googlemail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD')
app.config['MAIL_DEFAULT_SENDER'] = os.environ.get('MAIL_USERNAME')

app.config.update(
    SESSION_COOKIE_SECURE=True,
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE='Lax',
)

app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

mail = Mail(app)
db = SQLAlchemy(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.context_processor
def inject_user():
    return dict(current_user=current_user)

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(150), nullable=False)
    username = db.Column(db.String(50), unique=True, nullable=False)
    _password_hash = db.Column('password', db.String(250), nullable=False)
    address = db.Column(db.String(150), nullable=False)
    confirmed = db.Column(db.Boolean, default=False)

    carts = db.relationship('Carts', backref='user', lazy='dynamic')
    orders = db.relationship('Orders', backref='user', lazy=True)

    @property
    def password(self):
        raise AttributeError('password is not a readable attribute')

    @password.setter
    def password(self, password):
        self._password_hash = generate_password_hash(password)

    def verify_password(self, password):
        return check_password_hash(self._password_hash, password)

class Product(db.Model):
    __tablename__ = 'products'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    description = db.Column(db.String(50), nullable=False)
    price = db.Column(db.Numeric(10, 2), nullable=False)

    carts = db.relationship('Carts', backref='product', lazy=True)

class Carts(db.Model):
    __tablename__ = 'carts'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    price = db.Column(db.Numeric(10, 2), nullable=False)
    date = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    purchased = db.Column(db.Boolean, default=False)
    quantity = db.Column(db.Integer, nullable=False, default=1)
    order_id=db.Column(db.Integer, db.ForeignKey('orders.order_id'))

class Orders(db.Model):
    __tablename__ = 'orders'
    order_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    shipped_status = db.Column(db.String(50))
    order_date = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    total_price = db.Column(db.Numeric(10, 2), nullable=False)
    shipping_address = db.Column(db.String(150), nullable=False)

class RegistrationForm(FlaskForm):
    first_name = StringField('First Name', validators=[InputRequired()])
    last_name = StringField('Last Name', validators=[InputRequired()])
    email = StringField('Email', validators=[InputRequired(), Email()])
    username = StringField('Username', validators=[InputRequired(), Length(min=4, max=50)])
    password = PasswordField('Password', validators=[InputRequired(), Length(min=6, max=250)])
    address = StringField('Address', validators=[InputRequired()])
    submit = SubmitField('Register')

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[InputRequired()])
    password = PasswordField('Password', validators=[InputRequired()])
    captcha = StringField('Captcha', validators=[InputRequired()])
    submit = SubmitField('Login')

def valid_address(form, field):
    if not field.data.strip():
        raise ValidationError('Shipping address cannot be empty or whitespace.')

class ShippingForm(FlaskForm):
    shipping_address = StringField('Shipping Address', validators=[InputRequired(), valid_address])
    submit = SubmitField('Checkout')

def generate_captcha():
    image = ImageCaptcha()
    captcha_text = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
    data = image.generate(captcha_text)
    return io.BytesIO(data.getvalue()), captcha_text

@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        new_user = User(
            first_name=form.first_name.data,
            last_name=form.last_name.data,
            email=form.email.data,
            username=form.username.data,
            password=form.password.data,
            address=form.address.data
        )
        db.session.add(new_user)
        db.session.commit()
        flash('Registration successful! You can now login.', 'success')
        return redirect(url_for('login'))
    return render_template('register.html', form=form)

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        if form.captcha.data != session.get('captcha'):
            flash('Invalid captcha', 'error')
            return redirect(url_for('login'))
        user = User.query.filter_by(username=form.username.data).first()
        if user and user.verify_password(form.password.data):
            login_user(user)
            flash('Login successful!', 'success')
            return redirect(url_for('products'))
        else:
            flash('Invalid username or password', 'error')
    return render_template('login.html', form=form)

@app.route('/captcha')
def captcha():
    image, captcha_text = generate_captcha()
    session['captcha'] = captcha_text
    return send_file(image, mimetype='image/png')

@app.route('/logout')
@login_required
def logout():
    if current_user.is_authenticated:
        try:
            num_deleted = Carts.query.filter_by(user_id=current_user.id).delete()
            db.session.commit()
            flash(f'All cart items cleared. {num_deleted} items were removed.', 'success')
        except Exception as e:
            db.session.rollback()
            app.logger.error("Failed to delete cart items: %s", str(e))
            flash('Failed to clear cart items due to an error.', 'error')
    logout_user()
    flash('You have been logged out.', 'success')
    return redirect(url_for('login'))

@app.route('/products', methods=['GET'])
@login_required
def products():
    search_query = request.args.get('search_query', '')
    if search_query:
        search_results = Product.query.filter(or_(Product.name.ilike(f'%{search_query}%'), Product.description.ilike(f'%{search_query}%'))).all()
        num_results = len(search_results)
    else:
        search_results = []
        num_results = 0

    total_products = Product.query.count()
    cart_items = list(current_user.carts.filter_by(purchased=False).all())

    return render_template('products.html', search_results=search_results, 
                           num_results=num_results, total_products=total_products, 
                           search_query=search_query, cart_items=cart_items)

@app.route('/add_to_cart/<int:product_id>', methods=['POST'])
@login_required
def add_to_cart(product_id):
    product = Product.query.get_or_404(product_id)
    cart_item = Carts.query.filter_by(user_id=current_user.id, product_id=product_id, purchased=False).first()

    if cart_item:
        cart_item.quantity += 1
    else:
        cart_item = Carts(user_id=current_user.id, product_id=product_id, price=product.price, quantity=1)
        db.session.add(cart_item)

    db.session.commit()
    flash('Product added to cart successfully!', 'success')
    return redirect(url_for('products'))

@app.route('/cart', methods=['GET', 'POST'])
@login_required
def cart():
    form = ShippingForm()
    if request.method == 'POST' and form.validate_on_submit():
        cart_items = Carts.query.filter_by(user_id=current_user.id, purchased=False).all()
        total_price = sum(item.price * item.quantity for item in cart_items)
        shipping_address = form.shipping_address.data

        new_order = Orders(
            user_id=current_user.id,
            shipped_status='Completed',
            total_price=total_price,
            shipping_address=shipping_address
        )
        db.session.add(new_order)
        db.session.commit()

        for item in cart_items:
            item.purchased = True
            item.order_id = new_order.order_id
        db.session.commit()

        send_order_confirmation_email(new_order, current_user, cart_items)

        flash('Order placed successfully!', 'success')
        return redirect(url_for('home'))

    cart_items = Carts.query.filter_by(user_id=current_user.id, purchased=False).all()
    total_price = sum(item.price * item.quantity for item in cart_items)
    return render_template('carts.html', cart_items=cart_items, total_price=total_price, form=form)

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
        body += f"- {item.product.name}: ${item.price} x {item.quantity} = ${item.price * item.quantity}\n"

    msg = Message(subject, recipients=[admin_email])
    msg.body = body
    mail.send(msg)

@app.route('/')
def home():
    cart_items = list(current_user.carts.filter_by(purchased=False).all()) if current_user.is_authenticated else []
    return render_template('index.html', cart_items=cart_items)

if __name__ == '__main__':
    app.run(debug=True)



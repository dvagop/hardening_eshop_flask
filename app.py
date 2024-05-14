from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import InputRequired, Email, Length
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import or_
import os

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ['DB_CONNECTION_STRING']
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = os.environ.get('SECRET_KEY', 'your_secret_key')
db = SQLAlchemy(app)

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

# Define the Product model
class Product(db.Model):
    __tablename__ = 'products'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    description = db.Column(db.String(50), nullable=False)
    price = db.Column(db.String(50), nullable=False)

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
        # Create a new User object and add it to the database
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
        if user:
            if check_password_hash(user.password, password):
                flash('Login successful!', 'success')
                session['username'] = username  # Store username in session
                return redirect(url_for('products'))  # Redirect to products page
            else:
                flash('Invalid username or password', 'error')
        else:
            flash('Invalid username or password', 'error')
    return render_template('login.html', form=form)

# Route for logging out
@app.route('/logout')
def logout():
    session.pop('username', None)  # Clear the session (logout the user)
    flash('You have been logged out.', 'success')
    return redirect(url_for('home'))

# Route for products page
@app.route('/products', methods=['GET'])
def products():
    # Check if the user is authenticated
    if 'username' not in session:
        # User is not logged in, redirect to the login page
        return redirect(url_for('login'))

    search_query = request.args.get('search_query', '')  # Get search query from request
    if search_query:
        # Perform a case-insensitive search for products matching the search query
        search_results = Product.query.filter(or_(Product.name.ilike(f'%{search_query}%'),
                                                  Product.description.ilike(f'%{search_query}%'))).all()
        num_results = len(search_results)
        total_products = Product.query.count()
    else:
        search_results = []
        num_results = 0
        total_products = Product.query.count()

    return render_template('products.html', search_results=search_results, 
                           num_results=num_results, total_products=total_products, 
                           search_query=search_query)


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

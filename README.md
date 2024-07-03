# Flask eShop Hardening

A hardened version of a Flask-based eShop application, with various security measures to protect against common web vulnerabilities.

## Features

- **User Registration and Login** with CAPTCHA validation
- **Admin Email Confirmation** for new user registrations
- **Product Search and Shopping Cart**
- **Rate Limiting** on login attempts
- **Session Management** enhancements
- **Content Security Policy (CSP)** implementation
- **SQLAlchemy** for ORM

## Installation

1. **Clone the repository:**

   ```sh
   git clone https://github.com/radaplanakos/your-repo-name.git
   cd your-repo-name
   ```

2. **Create a virtual environment and activate it:**

   ```sh
   python3 -m venv venv
   source venv/bin/activate  # On Windows use `venv\Scripts\activate`
   ```

3. **Install the dependencies:**

   ```sh
   pip install -r requirements.txt
   ```

4. **Set up environment variables:**
   Create a `.env` file in the root directory and add the following:

   ```env
   SECRET_KEY=your_secret_key
   DB_CONNECTION_STRING=your_database_uri
   MAIL_USERNAME=your_email@gmail.com
   MAIL_PASSWORD=your_email_password
   ```

5. **Run the application:**
   ```sh
   flask run
   ```

## Usage

### Registration

1. Go to `/register` to create a new user account.
2. Admin confirms the user by visiting `/confirm/<user_id>`.

### Login

1. Go to `/login` to access your account.
2. CAPTCHA validation required.

### Shopping

1. Browse products at `/products`.
2. Add products to your cart and proceed to checkout.

## Security Features

- **Rate Limiting** using `Flask-Limiter`
- **Session Management** with session ID regeneration
- **Content Security Policy (CSP)** headers

## Contributing

Contributions are welcome! Fork this repository and submit pull requests.

## License

This project is licensed under the MIT License.

## Contact

For inquiries, contact [radaplanos13@gmail.com](mailto:radaplanos13@gmail.com).

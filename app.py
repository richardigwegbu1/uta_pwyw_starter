from flask import Flask, request, redirect, render_template, session as flask_session, render_template_string
import stripe
import os
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from flask_cors import CORS
from flask_mail import Mail, Message
from dotenv import load_dotenv
from flask_session import Session
import uuid
import random

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", str(uuid.uuid4()))
CORS(app)

# Session configuration
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SESSION_FILE_DIR'] = './.flask_session/'
app.config['SESSION_COOKIE_DOMAIN'] = None
app.config['SESSION_COOKIE_SAMESITE'] = "Lax"
app.config['SESSION_COOKIE_SECURE'] = False
Session(app)

# Stripe Setup
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
YOUR_DOMAIN = os.getenv("YOUR_DOMAIN")

# Google Sheets Setup
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
client = gspread.authorize(creds)
sheet = client.open("UTA_Training_Signups").sheet1

# Flask-Mail config
app.config['MAIL_SERVER'] = os.getenv('MAIL_SERVER')
app.config['MAIL_PORT'] = int(os.getenv('MAIL_PORT'))
app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD')
app.config['MAIL_USE_TLS'] = os.getenv('MAIL_USE_TLS') == 'True'
app.config['MAIL_USE_SSL'] = os.getenv('MAIL_USE_SSL') == 'True'

mail = Mail(app)

def send_enrollment_email(student_name, email, amount, receipt_url):
    html_template = """<!DOCTYPE html>
    <html lang="en">
    <body>
      <h2>✅ Welcome {{ student_name }}</h2>
      <p>We’ve received your payment of <strong>${{ amount }}</strong>.</p>
      {% if receipt_url %}
        <p><a href="{{ receipt_url }}" target="_blank">View Stripe Receipt</a></p>
      {% endif %}
    </body>
    </html>"""
    msg = Message("🎉 You're Enrolled!", sender=app.config['MAIL_USERNAME'], recipients=[email])
    msg.html = render_template_string(html_template, student_name=student_name, amount=amount, receipt_url=receipt_url)
    mail.send(msg)

@app.route("/", methods=["GET"])
def home():
    return render_template("index.html")

@app.route("/form", methods=["POST"])
def handle_form():
    name = request.form.get("name")
    email = request.form.get("email")
    experience = request.form.get("experience")
    payment_option = request.form.get("payment_option")
    price = 3500.00 if payment_option == "full" else float(request.form.get("price", 0))

    seat_number = random.randint(1, 20)
    flask_session["student"] = {
        "name": name, "email": email, "experience": experience,
        "price": price, "payment_option": payment_option
    }
    flask_session["seat_number"] = seat_number

    # Append to Google Sheet
    sheet.append_row([name, email, experience, price, payment_option, "Pending"])

    return redirect("/congratulations")

@app.route("/congratulations", methods=["GET", "POST"])
def congratulations():
    return render_template("congratulations.html", seat_number=flask_session.get("seat_number"))

@app.route("/continue-checkout", methods=["POST"])
def continue_checkout():
    data = flask_session.get('student')
    if not data:
        return "Session expired. Please refill the form.", 400

    price = float(data["price"])
    email = data["email"]
    payment_option = data["payment_option"]

    if payment_option == "installments":
        product = stripe.Product.create(name="UTA May Installments")
        stripe_price = stripe.Price.create(
            unit_amount=int((price / 2) * 100),
            currency="usd",
            recurring={"interval": "month"},
            product=product.id,
        )
        session = stripe.checkout.Session.create(
            mode="subscription",
            line_items=[{"price": stripe_price.id, "quantity": 1}],
            customer_email=email,
            success_url=f"{YOUR_DOMAIN}/success",
            cancel_url=f"{YOUR_DOMAIN}/cancel.html"
        )
    else:
        session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            line_items=[{
                "price_data": {
                    "currency": "usd",
                    "product_data": {"name": "UTA May Full Payment"},
                    "unit_amount": int(price * 100),
                },
                "quantity": 1,
            }],
            mode="payment",
            customer_email=email,
            success_url=f"{YOUR_DOMAIN}/success",
            cancel_url=f"{YOUR_DOMAIN}/cancel.html"
        )
    return redirect(session.url, code=303)

@app.route("/success")
def success():
    student = flask_session.get("student", {})
    amount_paid = float(student.get("price", 0))

    if student.get("payment_option") == "installments":
        amount_paid = amount_paid / 2

    return render_template("success.html", student_name=student.get("name", "Student"), amount_paid=amount_paid)

@app.route("/webhook", methods=["POST"])
def stripe_webhook():
    payload = request.data
    sig_header = request.headers.get("stripe-signature")
    endpoint_secret = os.getenv("STRIPE_WEBHOOK_SECRET")
    try:
        event = stripe.Webhook.construct_event(payload, sig_header, endpoint_secret)
    except stripe.error.SignatureVerificationError:
        return "Invalid signature", 400

    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        email = session.get("customer_email")
        receipt_url = session.get("receipt_url", "")
        payment_option = session.get("metadata", {}).get("payment_option")
        full_price = float(session.get("metadata", {}).get("full_price", 0))

        cell = sheet.find(email)
        if cell:
            sheet.update_cell(cell.row, 6, "Paid")
            student = sheet.row_values(cell.row)
            send_enrollment_email(student[0], email, full_price, receipt_url)

    return '', 200

if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0", port=8000)

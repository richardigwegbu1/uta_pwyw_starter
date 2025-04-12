# app.py
from flask import Flask, request, redirect, render_template, session as flask_session, render_template_string
import stripe
import os
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from flask_cors import CORS
from flask_mail import Mail, Message
from dotenv import load_dotenv
from datetime import datetime, timedelta
import uuid
import random

load_dotenv()
app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", str(uuid.uuid4()))
CORS(app)

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
    html_template = """
    <!DOCTYPE html>
    <html lang="en">
    <head><meta charset="UTF-8"><title>You're Enrolled!</title></head>
    <body style="font-family: Arial, sans-serif; background: #f9f9f9; padding: 40px; text-align: center;">
      <div style="background: #fff; padding: 30px; max-width: 700px; margin: auto; border-radius: 10px; box-shadow: 0 0 10px rgba(0,0,0,0.1);">
        <h1>✅ Payment Received – You’re Officially Enrolled!</h1>
        <p>Hi <strong>{{ student_name }}</strong>,</p>
        <p>We’ve received your payment of <strong>${{ amount }}</strong>.</p>
        {% if receipt_url %}
        <p>You can download your Stripe receipt here: <a href="{{ receipt_url }}" target="_blank">View Receipt</a></p>
        {% endif %}
        <h2>📅 Training Schedule</h2>
        <p><strong>Start Date:</strong> Saturday, May 31st</p>
        <p><strong>Class Times (US Central Time):</strong><br>Saturdays: 10:30 AM – 2:30 PM<br>Sundays: 2:30 PM – 6:30 PM</p>
        <h2>🎬 Watch the Welcome Video</h2>
        <iframe width="100%" height="360" src="https://www.youtube.com/embed/s9DtOoM1u_Q" frameborder="0" allowfullscreen></iframe>
        <p>Questions? Email us at <a href="mailto:support@unixtrainingacademy.com">support@unixtrainingacademy.com</a></p>
        <p>Warm regards,<br><strong>Richard Igwegbu</strong><br>Founder & Lead Instructor<br><a href="https://www.unixtrainingacademy.com">unixtrainingacademy.com</a></p>
      </div>
    </body>
    </html>
    """

    msg = Message("🎉 Welcome to Unix Training Academy", sender=app.config['MAIL_USERNAME'], recipients=[email])
    msg.html = render_template_string(html_template, student_name=student_name, amount=amount, receipt_url=receipt_url)
    mail.send(msg)

@app.route("/", methods=["GET"])
def home():
    if flask_session.get("submitted"):
        return redirect("/congratulations")
    return render_template("index.html")

@app.route("/form", methods=["POST"])
def handle_form():
    if flask_session.get("submitted"):
        return redirect("/congratulations")

    name = request.form.get("name")
    email = request.form.get("email")
    experience = request.form.get("experience")
    payment_option = request.form.get("payment_option")

    if payment_option == "full":
        price = 3500.00
    else:
        price = float(request.form.get("price"))

    seat_number = random.randint(1, 20)
    row = [name, email, experience, price, payment_option, "Pending"]
    sheet.append_row(row)

    flask_session['student'] = {
        "name": name,
        "email": email,
        "experience": experience,
        "price": price,
        "payment_option": payment_option,
    }
    flask_session['seat_number'] = seat_number
    flask_session['submitted'] = True

    return redirect("/congratulations")

@app.route("/congratulations")
def congratulations():
    seat_number = flask_session.get('seat_number', '...')
    return render_template("congratulations.html", seat_number=seat_number)

@app.route("/continue-checkout", methods=["GET"])
def continue_checkout():
    data = flask_session.get('student', {})
    name = data.get("name")
    email = data.get("email")
    experience = data.get("experience")
    price = float(data.get("price"))
    payment_option = data.get("payment_option")

    if payment_option == "installments":
        product = stripe.Product.create(name="Unix Training Academy May Training - Installments")
        installment_price = stripe.Price.create(
            unit_amount=int((price / 2) * 100),
            currency="usd",
            recurring={"interval": "month", "interval_count": 1},
            product=product.id,
        )
        subscription_session = stripe.checkout.Session.create(
            mode="subscription",
            line_items=[{"price": installment_price.id, "quantity": 1}],
            subscription_data={
                "metadata": {
                    "payment_option": "installments",
                    "full_price": str(price),
                    "expected_cycles": "2"
                }
            },
            customer_email=email,
            success_url=f"{YOUR_DOMAIN}/success",
            cancel_url=f"{YOUR_DOMAIN}/cancel.html"
        )
        return redirect(subscription_session.url, code=303)

    else:
        session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            line_items=[{
                'price_data': {
                    'currency': 'usd',
                    'product_data': {
                        'name': 'Unix Training Academy May Training - Full Payment',
                    },
                    'unit_amount': int(price * 100),
                },
                'quantity': 1,
            }],
            mode='payment',
            success_url=f"{YOUR_DOMAIN}/success",
            cancel_url=f"{YOUR_DOMAIN}/cancel.html",
            customer_email=email,
            metadata={
                'full_price': str(price),
                'payment_option': payment_option,
            }
        )
        return redirect(session.url, code=303)

@app.route("/success")
def success():
    student = flask_session.get("student", {})
    student_name = student.get("name", "Student")
    return render_template("success.html", student_name=student_name)

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
            if payment_option == "installments":
                sheet.update_cell(cell.row, 6, "Paid (1st of 2)")
            else:
                sheet.update_cell(cell.row, 6, "Paid")
            student = sheet.row_values(cell.row)
            student_name = student[0]  # First column is name
            send_enrollment_email(student_name, email, full_price, receipt_url)

    elif event['type'] == 'invoice.paid':
        invoice = event['data']['object']
        subscription_id = invoice.get("subscription")
        customer_email = invoice.get("customer_email") or invoice.get("customer")

        subscription = stripe.Subscription.retrieve(subscription_id)
        payment_option = subscription.get("metadata", {}).get("payment_option")
        full_price = subscription.get("metadata", {}).get("full_price")

        if payment_option == "installments":
            cell = sheet.find(customer_email)
            if cell:
                sheet.update_cell(cell.row, 6, "Paid (2 of 2) - Completed")
            stripe.Subscription.modify(subscription_id, cancel_at_period_end=True)

    return '', 200

if __name__ == '__main__':
    app.run(debug=True)
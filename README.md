📖 UTA PWYW App

Welcome to the official repository for the Unix Training Academy (UTA) Pay-What-You-Want (PWYW) Training Enrollment App! 🚀

This application allows students to submit a form, choose their payment option, complete Stripe checkout, and automatically log their enrollment into Google Sheets — all securely managed with a simple and modern Python Flask backend.
🌟 Features

    Full Form Submission and Session Handling

    Stripe Integration: Full Payment and 2-Part Installment Options

    Google Sheets Logging for Registrations

    Secure Email Notifications (via HostGator SMTP)

    Stripe Webhook for Payment Confirmation

    Production-Ready Deployment with Gunicorn + Apache

    Fully Configurable via .env Environment Variables

🛠️ Tech Stack

    Python 3.9+

    Flask

    Stripe Python SDK

    Flask-Mail

    Flask-Session

    Google Sheets API (gspread)

    Gunicorn

    Apache (Reverse Proxy)

    HostGator SMTP (Email Server)

    Systemd (Service Management)

⚙️ Setup Instructions

    Clone the Repository

git clone https://github.com/your-username/uta_pwyw_starter.git
cd uta_pwyw_starter

Create and Activate Virtual Environment

python3 -m venv venv
source venv/bin/activate

Install Dependencies

pip install -r requirements.txt

Setup Environment Variables

    Copy .env.example to .env

    Fill in your keys: Stripe, Google Credentials, SMTP details, etc.

Run Locally for Testing

    python app.py

    Deploy to Production

        Use Gunicorn behind Apache as a reverse proxy.

        Follow the pwyw.service systemd script.

        Ensure HTTPS is enabled.

📦 Production Launch Checklist

✅ A full detailed checklist for production launch has been provided inside the /docs folder.

📄 Download UTA PWYW App Production Launch Checklist PDF

Make sure you complete all Pre-Launch, Launch, and Post-Launch tasks before going live!
🎯 App Architecture Diagram

User Form → Flask Backend → Stripe Checkout → Webhook → Google Sheets
                     ↓                  ↓
               SMTP Email → Stripe Dashboard

🛡️ Security Best Practices

    Never hardcode sensitive keys.

    Always use .env files.

    Limit Google Sheets and Stripe API scopes.

    Enforce HTTPS and TLS for all communications.

📈 Post-Launch Monitoring

    Monitor Stripe Payments Daily

    Monitor Apache and Gunicorn Logs

    Regularly Backup Google Sheets

    Periodically Test Full Form-Checkout Flow

    Renew SSL certificates before expiration.

👨‍💻 Author

    Richard Igwegbu
    Founder, Unix Training Academy
    UnixTrainingAcademy.com

🚀 Ready to Launch?

    "Build it stable, secure it strongly, monitor it daily."
    — UTA PWYW App Motto

📜 License

This project is licensed for educational and internal production use at Unix Training Academy.

import os
from flask import Flask, render_template, request, jsonify
import razorpay
import smtplib
from email.mime.text import MIMEText
#from dotenv import load_dotenv

#load_dotenv()

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "a_super_secret_fallback_key_DO_NOT_USE_IN_PROD")

RAZORPAY_KEY_ID = os.environ.get("RAZORPAY_KEY_ID")
RAZORPAY_KEY_SECRET = os.environ.get("RAZORPAY_KEY_SECRET")

SMTP_EMAIL = os.environ.get("SMTP_EMAIL")
SMTP_PASSWORD = os.environ.get("SMTP_PASSWORD")
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587

if RAZORPAY_KEY_ID and RAZORPAY_KEY_SECRET:
    client = razorpay.Client(auth=(RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET))
else:
    print("WARNING: Razorpay API keys are not set. Payment functionality may not work.")
    client = None

@app.route('/')
def index1():
    return render_template('index1.html', key_id=RAZORPAY_KEY_ID)

@app.route('/payment')
def payment():
    return render_template('payment.html', key_id=RAZORPAY_KEY_ID)

@app.route('/verify', methods=['POST'])
def verify():
    data = request.get_json()
    payment_id = data.get('razorpay_payment_id')
    email = data.get('email', '')

    print(f"Received verification request for payment_id: {payment_id}, email: {email}")

    if not client:
        print("ERROR: Razorpay client not initialized. API keys missing.")
        return jsonify({'status': 'failed', 'message': 'Razorpay client not initialized. API keys missing.'})

    try:
        payment = client.payment.fetch(payment_id)
        print(f"Razorpay payment fetch response: {payment}")

        # Check if the payment is 'authorized' and then attempt to capture it
        if payment['status'] == 'authorized':
            print(f"Payment {payment_id} is authorized. Attempting to CAPTURE...")
            # Capture the payment. Amount is required and should match the authorized amount.
            captured_payment = client.payment.capture(payment_id, payment['amount'])
            print(f"Razorpay payment capture response: {captured_payment}")

            if captured_payment['status'] == 'captured':
                print(f"Payment {payment_id} successfully CAPTURED after authorization.")
                with open("paid_emails.txt", "a") as f:
                    f.write(email + "\n")
                send_success_email(email)
                return jsonify({'status': 'success'})
            else:
                print(f"Payment {payment_id} capture failed. New status: {captured_payment['status']}")
                return jsonify({'status': 'failed', 'message': f"Payment capture failed. Current status: {captured_payment['status']}"})
        elif payment['status'] == 'captured':
            print(f"Payment {payment_id} was already CAPTURED.")
            with open("paid_emails.txt", "a") as f:
                f.write(email + "\n")
            send_success_email(email)
            return jsonify({'status': 'success'})
        else:
            print(f"Payment {payment_id} status is NOT captured or authorized. Current status: {payment['status']}")
            return jsonify({'status': 'failed', 'message': f"Payment not captured. Current status: {payment['status']}"})
    except Exception as e:
        print(f"Payment verification/capture failed with exception: {e}")
        return jsonify({'status': 'failed', 'message': str(e)})

@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')

def send_success_email(to_email):
    subject = "✅ EnglishPr0 Course Access - Payment Successful"
    body = '''
Dear Student,

✅ Your payment was successful!

Here are your course access links:
📘 PDF Books: https://drive.google.com/drive/folders/1HNWohGqjIiy_TVEk_y710OrbDb0g-ae3
🎥 Video Lessons: https://drive.google.com/drive/folders/1EBzBgWNDUwv-gPvHZFO9pMP0Cs-e6hYU
📚 IELTS Pack: https://drive.google.com/drive/folders/1iqee_2QBbODOu8xis9BqPTOT0FHogzCi

Thanks for joining EnglishPr0!
'''
    msg = MIMEText(body)
    msg['Subject'] = subject
    msg['From'] = SMTP_EMAIL
    msg['To'] = to_email

    if not SMTP_EMAIL or not SMTP_PASSWORD:
        print("WARNING: SMTP credentials not set. Email cannot be sent.")
        return

    try:
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_EMAIL, SMTP_PASSWORD)
            server.sendmail(SMTP_EMAIL, to_email, msg.as_string())
            print(f"Email sent to {to_email}")
    except Exception as e:
        print(f"Failed to send email: {e}")

if __name__ == '__main__':
    app.run(debug=True)

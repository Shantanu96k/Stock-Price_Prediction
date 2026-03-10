from flask import Flask, render_template, request, session, redirect, flash, url_for
from flask_mysqldb import MySQL
from werkzeug.security import generate_password_hash, check_password_hash
import os
import pandas as pd

from models.lstm_model import predict_lstm
from utils.preprocess import preprocess_data

app = Flask(__name__)
app.secret_key = 'your_secure_secret_key_here'
app.permanent_session_lifetime = 1800

app.config.update(
    MYSQL_HOST='localhost',
    MYSQL_USER='root',
    MYSQL_PASSWORD='Why do you want to know my password?',
    MYSQL_DB='stockpredict',
    MYSQL_CURSORCLASS='DictCursor'
)

mysql = MySQL(app)

UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


@app.route('/')
def index():
    if 'username' not in session:
        return redirect(url_for('login'))
    return render_template('index.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM users WHERE username = %s", (username,))
        user = cur.fetchone()
        cur.close()

        if user and check_password_hash(user['password'], password):
            session.permanent = True
            session['username'] = user['username']
            return redirect(url_for('dashboard'))
        else:
            flash("Invalid username or password")
            return redirect(url_for('login'))

    return render_template('login.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        hashed_password = generate_password_hash(password)

        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM users WHERE username = %s", (username,))
        existing_user = cur.fetchone()

        if existing_user:
            flash("Username already exists")
            return redirect(url_for('register'))

        try:
            cur.execute("INSERT INTO users (username, password) VALUES (%s, %s)", (username, hashed_password))
            mysql.connection.commit()
            flash("Registration successful. Please log in.")
            return redirect(url_for('login'))
        except Exception as e:
            flash(f"Error during registration: {str(e)}")
            return redirect(url_for('register'))
        finally:
            cur.close()

    return render_template('register.html')


@app.route('/upload')
def upload():
    if 'username' not in session:
        return redirect(url_for('login'))
    return render_template('upload.html')


@app.route('/dashboard')
def dashboard():
    if 'username' not in session:
        return redirect(url_for('login'))
    return render_template('dashboard.html', username=session['username'])


@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('login'))


@app.route('/predict', methods=['POST'])
def predict():
    if 'username' not in session:
        return redirect(url_for('login'))

    if 'file' not in request.files or request.files['file'].filename == '':
        flash('No file selected')
        return redirect(url_for('dashboard'))

    file = request.files['file']

    # Secure the filename and save
    filename = file.filename
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(filepath)

    try:
        df = pd.read_csv(filepath)
    except Exception as e:
        flash(f"Failed to read CSV: {str(e)}")
        return redirect(url_for('dashboard'))

    try:
        data = preprocess_data(df)
    except Exception as e:
        flash(f"Preprocessing error: {str(e)}")
        return redirect(url_for('dashboard'))

    try:
        lstm_plot_html, lstm_predictions = predict_lstm(data)
    except Exception as e:
        flash(f"LSTM prediction error: {str(e)}")
        return redirect(url_for('dashboard'))

    return render_template(
        'prediction_results.html',
        lstm_plot_html=lstm_plot_html,
        lstm_predictions=lstm_predictions
    )


@app.route('/export', methods=['POST'])
def export_predictions():
    preds = request.form.getlist('predictions[]')
    if not preds:
        flash("No predictions to export")
        return redirect(url_for('dashboard'))

    dates = pd.date_range(end=pd.Timestamp.today(), periods=len(preds))
    df = pd.DataFrame({'Date': dates, 'Predicted Close': preds})
    csv_path = os.path.join(app.config['UPLOAD_FOLDER'], 'predictions.csv')
    df.to_csv(csv_path, index=False)
    flash(f"Predictions exported successfully to {csv_path}")
    return redirect(url_for('dashboard'))


if __name__ == '__main__':
    app.run(debug=True)
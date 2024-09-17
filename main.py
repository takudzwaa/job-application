import sqlite3
import requests
from bs4 import BeautifulSoup
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
import schedule
import time
import dotenv
import os
import re

# Load environment variables from .env file
dotenv.load_dotenv()

# Define your IT-related keywords
keywords = [
    "Software Engineer", "Cloud Engineer", "DevOps", "Python Developer", 
    "Java Developer", "Data Scientist", "AI", "Machine Learning", "AWS", 
    "Azure", "Google Cloud", "Full Stack Developer", "Cybersecurity", "Computer Technician",
    "IT Support", "Network Engineer", "IT Technician", "System Administrator"
]

# Initialize SQLite database connection
def init_db():
    conn = sqlite3.connect('jobs.db')
    cursor = conn.cursor()
    # Create table if it doesn't exist
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS applied_jobs (
            id INTEGER PRIMARY KEY,
            job_id TEXT UNIQUE
        )
    ''')
    conn.commit()
    return conn

def job_already_applied(conn, job_id):
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM applied_jobs WHERE job_id=?", (job_id,))
    return cursor.fetchone() is not None

def save_applied_job(conn, job_id):
    cursor = conn.cursor()
    cursor.execute("INSERT INTO applied_jobs (job_id) VALUES (?)", (job_id,))
    conn.commit()

# Function to apply to a job by sending an email
def apply_to_job(job_title, job_description, to_email):
    from_email = os.getenv('EMAIL')
    password = os.getenv('PASSWORD')
    cv_file = os.getenv('CV_PATH')  

    subject = f"Application for {job_title}"
    body = f"Dear Sir/Madam,\n\nI do hereby apply for the {job_title} at your organisation. Please find attached my resume for your review.\n\nBest regards,\n{os.getenv('MY_NAME')}"

    msg = MIMEMultipart()
    msg['From'] = from_email
    msg['To'] = to_email
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain'))

    # Attach CV
    with open(cv_file, "rb") as attachment:
        part = MIMEBase('application', 'octet-stream')
        part.set_payload(attachment.read())
        encoders.encode_base64(part)
        part.add_header('Content-Disposition', f'attachment; filename= {os.path.basename(cv_file)}')
        msg.attach(part)

    # Send email
    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(from_email, password)
        server.sendmail(from_email, to_email, msg.as_string())
        server.quit()
        print(f"Applied to {job_title}")
    except Exception as e:
        print(f"Failed to send email for {job_title}: {e}")

# extract email from job description
def extract_email(description):
    match = re.search(r'[\w\.-]+@[\w\.-]+', description)
    return match.group(0) if match else None

# Function to scrape jobs from multiple websites
def scrape_jobs(conn):
    urls = [
        'https://vacancymail.co.zw/jobs/?search=&location=&category=10',
        'https://jobszimbabwe.co.zw/'
    ]
    
    for url in urls:
        response = requests.get(url)
        soup = BeautifulSoup(response.content, 'html.parser')

        for job in soup.find_all('div', class_='job-listing'):
            title = job.find('h2').text.strip()
            description = job.find('p').text.strip()
            job_id = title

            # Check if the job has already been applied to
            if not job_already_applied(conn, job_id):
                # Check if keywords match
                if any(keyword in title for keyword in keywords) or any(keyword in description for keyword in keywords):
                    email_address = extract_email(description)
                    if email_address:
                        apply_to_job(title, description, email_address)
                        save_applied_job(conn, job_id)
                    else:
                        print(f"No email found for job: {title}")

# Function to run scheduled tasks
def run_scheduled_tasks(conn):
    print("Running scheduled tasks...")
    scrape_jobs(conn)


def main():
    conn = init_db()

    schedule.every().day.at("08:00").do(run_scheduled_tasks, conn)
    schedule.every().day.at("12:00").do(run_scheduled_tasks, conn)
    schedule.every().day.at("16:00").do(run_scheduled_tasks, conn)

    # Keep the script running
    while True:
        schedule.run_pending()
        time.sleep(60)

if __name__ == "__main__":
    main()

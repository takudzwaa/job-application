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

# Check if a job has already been applied to
def job_already_applied(conn, job_id):
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM applied_jobs WHERE job_id=?", (job_id,))
    return cursor.fetchone() is not None

# Save the job after applying
def save_applied_job(conn, job_id):
    cursor = conn.cursor()
    cursor.execute("INSERT INTO applied_jobs (job_id) VALUES (?)", (job_id,))
    conn.commit()

# Function to apply to a job by sending an email
def apply_to_job(job_title, job_description, to_email):
    from_email = dotenv.get('EMAIL')
    password = dotenv.get('PASSWORD')
    cv_file = "path_to_your_cv.pdf"

    subject = f"Application for {job_title}"
    body = f"Dear Sir/Madam,\n\nI am applying for the position of {job_title}. Please find attached my CV.\n\nBest regards,\nYour Name"

    msg = MIMEMultipart()
    msg['From'] = from_email
    msg['To'] = to_email
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain'))

    attachment = open(cv_file, "rb")
    part = MIMEBase('application', 'octet-stream')
    part.set_payload(attachment.read())
    encoders.encode_base64(part)
    part.add_header('Content-Disposition', f'attachment; filename= {cv_file}')
    msg.attach(part)

    server = smtplib.SMTP('smtp.gmail.com', 587)
    server.starttls()
    server.login(from_email, password)
    server.sendmail(from_email, to_email, msg.as_string())
    server.quit()

    print(f"Applied to {job_title}")

# Function to scrape jobs from a website
def scrape_jobs(conn):
    # Example job board URL
    url = 'https://www.example-jobsite.com/jobs?q=IT'
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')

    for job in soup.find_all('div', class_='job-listing'):
        title = job.find('h2').text
        description = job.find('p').text
        job_id = title.strip()  # Use the title as the job ID (you can adjust this)

        # Check if the job was already applied to
        if not job_already_applied(conn, job_id):
            # Check for keywords in the job title or description
            if any(keyword in title for keyword in keywords) or any(keyword in description for keyword in keywords):
                email_address = 'hr@example.com'  # Replace with actual HR email if available
                apply_to_job(title, description, email_address)

                # Save job ID to avoid applying again
                save_applied_job(conn, job_id)

# Function to run scheduled tasks (scraping and email checking)
def run_scheduled_tasks(conn):
    print("Running scheduled tasks...")
    scrape_jobs(conn)

# Main function to schedule tasks
def main():
    conn = init_db()

    # Scheduling the job search at 8:00 AM, 12:00 PM, and 4:00 PM
    schedule.every().day.at("08:00").do(run_scheduled_tasks, conn)
    schedule.every().day.at("12:00").do(run_scheduled_tasks, conn)
    schedule.every().day.at("16:00").do(run_scheduled_tasks, conn)

    # Keep the script running
    while True:
        schedule.run_pending()
        time.sleep(60)

if __name__ == "__main__":
    main()

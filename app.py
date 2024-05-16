import os
from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from bs4 import BeautifulSoup
import requests
import re
from twilio.rest import Client


# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = '8BYkEfBA6O6donzWlSihBXox7C0sKR6b'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///latestnews.db'


# TWILIO_ACCOUNT_SID = os.getenv('TWILIO_ACCOUNT_SID')
# TWILIO_AUTH_TOKEN = os.getenv('TWILIO_AUTH_TOKEN')
# TWILIO_WHATSAPP_NUMBER = os.getenv('TWILIO_WHATSAPP_NUMBER')
# MY_WHATSAPP_NUMBER = os.getenv('MY_WHATSAPP_NUMBER')
# FRIEND_WHATSAPP_NUMBER = os.getenv('FRIEND_WHATSAPP_NUMBER')
#Twillio code

#
db = SQLAlchemy(app)

class Techupdate(db.Model):
    __tablename__ = "tech_update"
    id = db.Column(db.Integer, primary_key=True)
    headline = db.Column(db.String(500), nullable=False)
    link = db.Column(db.String(500), nullable=False)

with app.app_context():
    db.create_all()

URL = "https://www.cnet.com/ai-atlas/"

def load_tracked_urls():
    tracked_urls = {item.link for item in Techupdate.query.all()}
    return tracked_urls

def scrape_and_store():
    response = requests.get(URL)
    if response.status_code == 200:
        content = response.text
        soup = BeautifulSoup(content, "html.parser")

        blog_text = []
        blog_link = []

        tracked_urls = load_tracked_urls()

        blogs = soup.find_all("a", class_="c-storiesNeonHighlightsCard_link")

        if blogs:
            new_articles_found = False
            for blog in blogs:
                text = blog.get_text(strip=True)
                link = blog.get('href')
                full_link = f"https://www.cnet.com{link}"
                if text and link and full_link not in tracked_urls:
                    text = re.split(r'\d{1,2} (?:hour|hours|day|days) ago', text)[0].strip()
                    text = re.split(r'\d{1,2}:\d{2} • \s*\d{1,2} (?:hour|hours|day|days) ago', text)[0].strip()
                    blog_text.append(text)
                    blog_link.append(full_link)
                    new_articles_found = True

            if new_articles_found:
                for text, link in zip(blog_text, blog_link):
                    new_update = Techupdate(headline=text, link=link)
                    db.session.add(new_update)
                db.session.commit()
                send_whatsapp_message(blog_text, blog_link)
                return {"message": "New articles have been stored and sent via WhatsApp.", "status": "success"}
            else:
                return {"message": "Stay tuned, new news will come.", "status": "no_update"}
    return {"message": "Failed to retrieve the webpage.", "status": "error"}

def send_whatsapp_message(headlines, links):
    print("Sending WhatsApp message...")
    print(f"TWILIO_ACCOUNT_SID: {TWILIO_ACCOUNT_SID}")
    print(f"TWILIO_AUTH_TOKEN: {TWILIO_AUTH_TOKEN}")
    client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
    message_body = "\n\n".join([f"{headline}: {link}" for headline, link in zip(headlines, links)])
    print("Message body:", message_body)

    try:
        # Send message to your number
        message1 = client.messages.create(
            body=message_body,
            from_=TWILIO_WHATSAPP_NUMBER,
            to=MY_WHATSAPP_NUMBER
        )
        print("Message sent to your number:", message1.sid)

        # Send message to your friend's number
        message2 = client.messages.create(
            body=message_body,
            from_=TWILIO_WHATSAPP_NUMBER,
            to=FRIEND_WHATSAPP_NUMBER
        )
        print("Message sent to friend's number:", message2.sid)

        return message1.sid, message2.sid
    except Exception as e:
        print("Error sending message:", e)
        return None

@app.route('/', methods=['GET'])
def home():
    return render_template('home.html')

@app.route('/login', methods=['GET'])
def login():
    return render_template('loginpage.html')

@app.route('/contact', methods=['GET'])
def contact():
    return render_template('contactUs.html')

@app.route('/ad', methods=['GET'])
def ad():
    return render_template('ad.html')

@app.route('/about', methods=['GET'])
def about():
    return render_template('about.html')

@app.route('/scrape', methods=['GET'])
def scrape():
    result = scrape_and_store()
    flash(result['message'])
    return redirect(url_for('home'))

@app.route('/delete_all', methods=['GET'])
def delete_all():
    try:
        num_rows_deleted = db.session.query(Techupdate).delete()
        db.session.commit()
        flash(f"All news entries deleted ({num_rows_deleted} rows).")
    except Exception as e:
        db.session.rollback()
        flash("Error occurred while trying to delete news entries.")
    return redirect(url_for('home'))

@app.route('/connect_whatsapp', methods=['GET'])
def connect_whatsapp():
    updates = Techupdate.query.limit(4).all()
    headlines = [update.headline for update in updates]
    links = [update.link for update in updates]
    if headlines and links:
        send_whatsapp_message(headlines, links)
        flash("Latest news sent to WhatsApp!")
    else:
        flash("No news to send.")
    return redirect(url_for('home'))

if __name__ == '__main__':
    app.run(debug=True)

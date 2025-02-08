# app.py
from flask import Flask, render_template, request, redirect, url_for, flash
from pymongo import MongoClient
from bson.objectid import ObjectId
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv("APP_KEY")  # Change this to a secure secret key

# Replace this with your MongoDB Atlas connection string
MONGO_URI = os.getenv("MONGO_URI")
client = MongoClient(MONGO_URI)
db = client.experience_tracker  # database name
experiences = db.experiences    # collection name

@app.route('/')
def index():
    # Sort by date descending
    all_experiences = experiences.find().sort('date', -1)
    return render_template('index.html', experiences=all_experiences)

@app.route('/add', methods=['POST'])
def add_experience():
    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        
        if not title or not description:
            flash('Title and description are required!', 'error')
            return redirect(url_for('index'))
        
        experience = {
            'title': title,
            'description': description,
            'date': datetime.utcnow()
        }
        
        experiences.insert_one(experience)
        flash('Experience added successfully!', 'success')
        return redirect(url_for('index'))

@app.template_filter('format_date')
def format_date(date):
    return date.strftime('%B %d, %Y at %I:%M %p')

if __name__ == '__main__':
    app.run(debug=True)
# app.py
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask import send_file, Response

from pymongo import MongoClient
from bson.objectid import ObjectId
from datetime import datetime
import os
import gridfs
from dotenv import load_dotenv
from better_profanity import profanity

def has_profanity(text):
    # Check if the text contains any profane words
    return profanity.contains_profanity(text)

load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv("APP_KEY")  # Change this to a secure secret key

# Replace this with your MongoDB Atlas connection string
MONGO_URI = os.getenv("MONGO_URI")
client = MongoClient(MONGO_URI)

db = client.experience_tracker  # database name
fs = gridfs.GridFS(client.db)

experiences = db.experiences    # collection name

@app.route('/')
def index():
    # Sort by date descending
    all_experiences = experiences.find().sort('date', -1)
    return render_template('index.html', experiences=all_experiences)

@app.route("/toggle_like/<id>", methods=['POST'])
def toggle_like(id):
    experiences = db["experiences"]
    experiences.update_one(
        {'_id': ObjectId(id)},
        {'$inc': {'likes': 1}}
    )
    document = experiences.find_one({'_id': ObjectId(id)}, {'likes': 1})
    print({"likes": document.get('likes', 0)})
    return jsonify({"likes": document.get('likes', 0)})


@app.route('/add', methods=['POST'])
def add_experience():
    """ Handle adding a new experience with an optional image upload """
    title = request.form.get('title')
    description = request.form.get('description')
    rating = request.form.get('rating','0')
    likes = 0
    
    print("Files received:", request.files)  # Log received files

    file = request.files.get("images")  # Ensure correct name


    # Ensure title and description exist
    if not title or not description:
        flash('Title and description are required!', 'error')
        return redirect(url_for('index'))
    
    if has_profanity(title) or  has_profanity(description):
        flash('You cannot type that!', 'error')
        return redirect(url_for('index'))

    # Get the file safely (avoid KeyError)
    if file:  # Check if file is uploaded
        print(f"File received: {file.filename}")  # Debugging
        file_id = fs.put(file, filename=file.filename, content_type=file.content_type)
    else:
        print("No file received!")  # Debugging

    experience = {
        'title': title,
        'description': description,
        'date': datetime.utcnow(),
        'rating': rating,
        "image_id": file_id if file else None, 
        "likes": likes
    }

   
    # Insert experience into MongoDB
    experiences.insert_one(experience)
    flash('Experience added successfully!', 'success')
    return redirect(url_for('index'))

@app.route('/image/<image_id>')
def get_image(image_id):
    try:
        # Retrieve the image file from GridFS
        file = fs.get(ObjectId(image_id))
        return Response(file.read(), mimetype=file.content_type)
    except gridfs.errors.NoFile:
        return "Image Not Found", 404
    
@app.template_filter('format_date')
def format_date(date):
    return date.strftime('%B %d, %Y at %I:%M %p')

if __name__ == '__main__':
    app.run(debug=True)
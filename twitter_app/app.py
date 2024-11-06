from flask import Flask, render_template, request, redirect, url_for, flash
from pymongo import MongoClient
from datetime import datetime

app = Flask(__name__)
app.secret_key = "secret_key"  # Diperlukan untuk flash messages

# Koneksi ke MongoDB
client = MongoClient("mongodb://localhost:27017/")
db = client['twitter_app']
users_col = db['users']
tweets_col = db['tweets']
comments_col = db['comments']

# Route Halaman Utama
@app.route('/')
def index():
    tweets = list(tweets_col.find().sort("created_at", -1))
    return render_template('index.html', tweets=tweets)

# Route untuk Post Tweet
@app.route('/post_tweet', methods=['POST'])
def post_tweet():
    username = request.form['username']
    content = request.form['content']
    tweet = {
        "tweet_id": tweets_col.count_documents({}) + 1,
        "username": username,
        "content": content,
        "likes": 0,
        "comment_count": 0,
        "created_at": datetime.now()
    }
    tweets_col.insert_one(tweet)
    flash("Tweet berhasil diposting!")
    return redirect(url_for('index'))

# Route untuk Like Tweet
@app.route('/like_tweet/<int:tweet_id>')
def like_tweet(tweet_id):
    tweets_col.update_one({"tweet_id": tweet_id}, {"$inc": {"likes": 1}})
    flash("Berhasil menambahkan like!")
    return redirect(url_for('index'))

# Route untuk Hapus Tweet
@app.route('/delete_tweet/<int:tweet_id>')
def delete_tweet(tweet_id):
    result_tweet = tweets_col.delete_one({"tweet_id": tweet_id})
    if result_tweet.deleted_count > 0:
        comments_col.delete_many({"tweet_id": tweet_id})
        flash("Tweet berhasil dihapus!")
    else:
        flash("Tweet tidak ditemukan!")
    return redirect(url_for('index'))

# Route untuk Melihat dan Menambah Komentar
@app.route('/tweet/<int:tweet_id>', methods=['GET', 'POST'])
def tweet(tweet_id):
    tweet = tweets_col.find_one({"tweet_id": tweet_id})
    comments = list(comments_col.find({"tweet_id": tweet_id}).sort("created_at", 1))
    
    if request.method == 'POST':
        username = request.form['username']
        text = request.form['text']
        comment = {
            "comment_id": comments_col.count_documents({}) + 1,
            "tweet_id": tweet_id,
            "username": username,
            "text": text,
            "created_at": datetime.now()
        }
        comments_col.insert_one(comment)
        tweets_col.update_one({"tweet_id": tweet_id}, {"$inc": {"comment_count": 1}})
        flash("Komentar berhasil ditambahkan!")
        return redirect(url_for('tweet', tweet_id=tweet_id))

    return render_template('tweet.html', tweet=tweet, comments=comments)

# Route untuk Mengelola Pengguna
@app.route('/users')
def users():
    users = list(users_col.find().sort("username", 1))
    return render_template('user.html', users=users)

# Tambah Pengguna
@app.route('/add_user', methods=['POST'])
def add_user():
    username = request.form['username']
    if users_col.find_one({"username": username}):
        flash("Username sudah ada!")
    else:
        user = {
            "username": username,
            "display_name": request.form['display_name'],
            "bio": request.form['bio'],
            "tanggal_lahir": request.form['tanggal_lahir']
        }
        users_col.insert_one(user)
        flash("Pengguna berhasil ditambahkan!")
    return redirect(url_for('users'))

# Edit Pengguna
@app.route('/edit_user/<username>', methods=['GET', 'POST'])
def edit_user(username):
    user = users_col.find_one({"username": username})
    if request.method == 'POST':
        new_display_name = request.form['display_name']
        new_bio = request.form['bio']
        new_tanggal_lahir = request.form['tanggal_lahir']

        # Update informasi pengguna
        users_col.update_one({"username": username}, {"$set": {
            "display_name": new_display_name,
            "bio": new_bio,
            "tanggal_lahir": new_tanggal_lahir
        }})
        flash("Pengguna berhasil diedit.")
        return redirect(url_for('users'))
    return render_template('edit_user.html', user=user)

# Hapus Pengguna
@app.route('/delete_user/<username>')
def delete_user(username):
    result = users_col.delete_one({"username": username})
    flash("Pengguna berhasil dihapus!" if result.deleted_count > 0 else "Pengguna tidak ditemukan!")
    return redirect(url_for('users'))

if __name__ == "__main__":
    app.run(debug=True)

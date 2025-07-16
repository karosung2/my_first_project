from flask import Flask, render_template, request, redirect, url_for
from werkzeug.utils import secure_filename
import os

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = os.path.join('static', 'uploads')

# simple in-memory storage for posts
posts = {}

# list of KBO teams
TEAMS = [
    'Doosan Bears',
    'Lotte Giants',
    'Hanwha Eagles',
    'LG Twins',
    'SSG Landers',
    'Samsung Lions',
    'KIA Tigers',
    'KT Wiz',
    'NC Dinos',
    'Kiwoom Heroes'
]

@app.route('/')
def index():
    return render_template('index.html', teams=TEAMS)

@app.route('/team/<team>', methods=['GET', 'POST'])
def team_board(team):
    if team not in TEAMS:
        return "Unknown team", 404

    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        username = request.form.get('username', 'Anonymous').strip() or 'Anonymous'
        content = request.form.get('content', '')
        file = request.files.get('file')
        filename = None
        if file and file.filename:
            filename = secure_filename(file.filename)
            team_folder = os.path.join(app.config['UPLOAD_FOLDER'], team)
            os.makedirs(team_folder, exist_ok=True)
            file.save(os.path.join(team_folder, filename))

        posts.setdefault(team, []).append({
            'title': title or 'No Title',
            'username': username,
            'content': content,
            'filename': filename
        })
        return redirect(url_for('team_board', team=team))

    team_posts = posts.get(team, [])
    return render_template('team.html', team=team, posts=team_posts)


@app.route('/team/<team>/post/<int:post_id>')
def view_post(team, post_id):
    if team not in TEAMS:
        return "Unknown team", 404
    team_posts = posts.get(team, [])
    if post_id < 0 or post_id >= len(team_posts):
        return "Post not found", 404
    post = team_posts[post_id]
    return render_template('post.html', team=team, post=post)

if __name__ == '__main__':
    app.run(debug=True)

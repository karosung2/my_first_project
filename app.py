from flask import Flask, render_template, request, redirect, url_for, session
from werkzeug.utils import secure_filename
from bs4 import BeautifulSoup
import requests
import os

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = os.path.join('static', 'uploads')
app.secret_key = 'dev_key'  # simple dev secret

# simple in-memory user store {username: {'password': pwd, 'nickname': nick}}
users = {}

# simple in-memory storage for posts
posts = {}

# list of KBO teams (fallback order)
DEFAULT_TEAMS = [
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

# mapping from Korean team names on the ranking page to our board names
TEAM_NAME_MAP = {
    '두산': 'Doosan Bears',
    '롯데': 'Lotte Giants',
    '한화': 'Hanwha Eagles',
    'LG': 'LG Twins',
    'SSG': 'SSG Landers',
    '삼성': 'Samsung Lions',
    'KIA': 'KIA Tigers',
    'KT': 'KT Wiz',
    'NC': 'NC Dinos',
    '키움': 'Kiwoom Heroes'
}

# simple logo mapping (public URLs)
TEAM_LOGOS = {
    'Doosan Bears': 'https://sports-phinf.pstatic.net/team/kbo/default/OB.png',
    'Lotte Giants': 'https://sports-phinf.pstatic.net/team/kbo/default/LT.png',
    'Hanwha Eagles': 'https://sports-phinf.pstatic.net/team/kbo/default/HH.png',
    'LG Twins': 'https://sports-phinf.pstatic.net/team/kbo/default/LG.png',
    'SSG Landers': 'https://sports-phinf.pstatic.net/team/kbo/default/SK.png',
    'Samsung Lions': 'https://sports-phinf.pstatic.net/team/kbo/default/SS.png',
    'KIA Tigers': 'https://sports-phinf.pstatic.net/team/kbo/default/HT.png',
    'KT Wiz': 'https://sports-phinf.pstatic.net/team/kbo/default/KT.png',
    'NC Dinos': 'https://sports-phinf.pstatic.net/team/kbo/default/NC.png',
    'Kiwoom Heroes': 'https://sports-phinf.pstatic.net/team/kbo/default/WO.png'
}

def fetch_ranked_teams():
    """Attempt to fetch team rankings from the KBO website."""
    url = 'https://www.koreabaseball.com/Record/TeamRank/TeamRank.aspx'
    try:
        resp = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=5)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, 'html.parser')
        teams = []
        table = soup.find('table', {'class': 'tData'})
        if table:
            for row in table.select('tbody tr'):
                cols = row.find_all('td')
                if cols:
                    name_ko = cols[1].get_text(strip=True)
                    teams.append(TEAM_NAME_MAP.get(name_ko, name_ko))
        if teams:
            return teams
    except Exception as exc:
        print('Failed to fetch rankings:', exc)
    return DEFAULT_TEAMS


def get_ranked_teams():
    if not hasattr(get_ranked_teams, 'cache'):
        get_ranked_teams.cache = fetch_ranked_teams()
    return get_ranked_teams.cache

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        user = users.get(username)
        if user and user['password'] == password:
            session['username'] = username
            return redirect(url_for('index'))
        return render_template('login.html', error='Invalid credentials')
    return render_template('login.html')


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        nickname = request.form.get('nickname', '').strip()
        if not username or not password:
            return render_template('signup.html', error='Username and password required')
        if username in users:
            return render_template('signup.html', error='User already exists')
        users[username] = {'password': password, 'nickname': nickname or username}
        return redirect(url_for('login'))
    return render_template('signup.html')


@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('index'))

@app.route('/')
def index():
    teams = get_ranked_teams()
    username = session.get('username')
    nickname = users.get(username, {}).get('nickname') if username else None
    return render_template('index.html', teams=teams, username=username, nickname=nickname)

@app.route('/team/<team>', methods=['GET', 'POST'])
def team_board(team):
    teams = get_ranked_teams()
    if team not in teams:
        return "Unknown team", 404

    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        username = session.get('username', request.form.get('username', 'Anonymous')).strip() or 'Anonymous'
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
    username = session.get('username')
    nickname = users.get(username, {}).get('nickname') if username else None
    return render_template('team.html', team=team, posts=team_posts, username=username, nickname=nickname)


@app.route('/team/<team>/post/<int:post_id>')
def view_post(team, post_id):
    teams = get_ranked_teams()
    if team not in teams:
        return "Unknown team", 404
    team_posts = posts.get(team, [])
    if post_id < 0 or post_id >= len(team_posts):
        return "Post not found", 404
    post = team_posts[post_id]
    username = session.get('username')
    nickname = users.get(username, {}).get('nickname') if username else None
    return render_template('post.html', team=team, post=post, username=username, nickname=nickname)

if __name__ == '__main__':
    app.run(debug=True)

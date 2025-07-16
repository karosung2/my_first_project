# my_first_project

Simple KBO team fan board built with Flask.

Each team has a message board where fans can post a title, content and an optional
file attachment. Posts are listed with their titles and authors; clicking a title
shows the full post.

On the home page, the list of teams is ordered by the current KBO team ranking.
The app attempts to fetch the ranking from `koreabaseball.com` and falls back to
a default order if the site cannot be reached.

## Setup
```
pip install -r requirements.txt
python app.py
```

Visit `http://localhost:5000` in your browser.

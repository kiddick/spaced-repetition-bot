import random
from datetime import datetime

from flask import Flask, render_template

from src.bot.models import Task

app = Flask(__name__)


@app.route("/stats/<int:chat_id>/")
def get_statistics(chat_id):
    tasks = Task.get_users_tasks(chat_id)

    if not tasks:
        return render_template('404.html')

    return render_template(
        'stats.html',
        tasks=list(tasks),
        q=str(random.random())
    )


@app.template_filter('strftime')
def format_timestamp(value):
    return datetime.fromtimestamp(int(value)).strftime('%H:%M - %d.%m.%y')

if __name__ == "__main__":
    app.jinja_env.auto_reload = True
    app.run(host='0.0.0.0', port=7890)

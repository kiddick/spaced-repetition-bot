import random
from datetime import datetime

from flask import Flask, render_template, jsonify

from src.bot.models import Task


class FlaskCustomTemplates(Flask):
    jinja_options = Flask.jinja_options.copy()
    jinja_options.update(dict(
        block_start_string='$$',
        block_end_string='$$',
        variable_start_string='$',
        variable_end_string='$',
        comment_start_string='$#',
        comment_end_string='#$',
    ))

app = FlaskCustomTemplates(__name__)


@app.route("/stats/<int:chat_id>/")
def get_statistics(chat_id):
    tasks = Task.get_users_tasks(chat_id)

    if not tasks:
        return render_template('404.html')
    tasks = sorted(tasks, key=lambda task: task.start_date, reverse=True)

    return render_template(
        'stats.html',
        chat_id=chat_id,
        q=str(random.random())
    )


@app.route("/api/get_tasks/<int:chat_id>")
def get_user_tasks(chat_id):
    tasks = Task.get_public_list(chat_id)
    return jsonify(tasks=tasks)


@app.template_filter('strftime')
def format_timestamp(value):
    return datetime.fromtimestamp(int(value)).strftime('%H:%M - %d.%m.%y')


if __name__ == "__main__":
    app.jinja_env.auto_reload = True
    app.run(host='0.0.0.0', port=7890)

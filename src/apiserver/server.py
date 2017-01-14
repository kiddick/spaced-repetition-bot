from functools import wraps

from flask import Flask, request, jsonify

from src.bot.models import User, Task, Activity
from src.bot.utils import format_task_content


app = Flask(__name__)


def authenticate(func):

    @wraps(func)
    def decorated(*args, **kwargs):
        api_key = request.args.get('apiKey')
        if api_key:
            user = User.find_by_api_key(api_key)
            if user:
                kwargs['api_key'] = api_key
                kwargs['user'] = user
                return func(*args, **kwargs)
        return jsonify(status=False)
    return decorated


@app.route("/api/authorize/")
@authenticate
def authorize(api_key, user):
    response = {'status': True}
    response.update(user.to_public_dict())
    return jsonify(**response)


@app.route("/api/add_term/")
@authenticate
def add_term(api_key, user):
    term = request.args.get('term')

    if term and Task.create(
            chat_id=user.chat_id,
            content=format_task_content(term),
            origin=Activity.ADD_EXT):
        return jsonify(status=True)
    else:
        return jsonify(status=False)


if __name__ == "__main__":
    app.run(port=8080)

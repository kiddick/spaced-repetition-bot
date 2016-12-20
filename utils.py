import re
import yaml
import datetime


def encode_callback_data(answer_option, data):
    return '{}@{}'.format(answer_option, data)


def decode_callback_data(callback_data):
    return re.sub(r'^\d+@', '', callback_data)


def decode_answer_option(callback_data):
    return callback_data.split('@')[0]


def render_template(template, *args, bold=False):
    if len(args) != template.count('{}'):
        raise IndexError('Number of arguments did not match with template')

    if bold:
        template = template.replace('{}', '*{}*')

    return template.format(*args)


def format_task_content(content):
    content = content.strip()
    if content:
        first_letter = content[0]
        content = first_letter.upper() + content[1:]
    return content


def timestamp_to_date(timestamp):
    return datetime.datetime.fromtimestamp(
        int(timestamp)).strftime('%H:%M %d/%m/%Y')


def load_config():
    with open('config.yaml') as stream:
        config = yaml.load(stream)

    time_multiplier = config['intervals_multiplier']
    config['time_intervals'] = [
        interval * time_multiplier for interval in config['time_intervals']
    ]

    return config

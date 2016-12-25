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


def _convert_handwrite_to_seconds(conf_value):
    multiplier = {
        's': 1,
        'm': 60,
        'h': 3600,
        'd': 86400,
        'w': 604800
    }
    result = 0
    for time_value in re.findall(r'.+?[smhdw]', conf_value):
        time_prefix = time_value[-1]
        value = float(time_value[:-1])
        result += value * multiplier[time_prefix]
    return result


def load_config():
    with open('config.yaml') as stream:
        config = yaml.load(stream)

    config['time_intervals'] = [
        _convert_handwrite_to_seconds(i) for i in config['time_intervals']
    ]

    return config

import re


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

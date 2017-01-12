import time
import random
from datetime import datetime, timezone

from peewee import *
from src.bot.utils import load_config


config = load_config()
DATABASE_NAME = config['database_name']
API_KEY_SIZE = 15
time_intervals = config['time_intervals']


db = SqliteDatabase(DATABASE_NAME)


def get_time_delta(delta_index):
    return time_intervals[delta_index]


class TaskStatus(object):
    WAITING_ANSWER = 'waiting'
    ACTIVE = 'active'
    DONE = 'done'


def get_current_timestamp():
    timestamp = time.time()
    # timestamp = datetime.utcnow().replace(tzinfo=timezone.utc).timestamp()
    return int(timestamp)


def generate_notification_date(delta_index=0):
    return get_current_timestamp() + get_time_delta(delta_index)


class BaseModel(Model):

    class Meta:
        database = db


class Task(BaseModel):
    content = CharField(default='')
    iteration = IntegerField(default=0)
    notification_date = IntegerField(
        index=True, default=generate_notification_date)
    start_date = IntegerField(default=get_current_timestamp)
    finish_date = IntegerField(default=0)
    chat_id = IntegerField(index=True, default=0)
    status = CharField(default=TaskStatus.ACTIVE)
    forgot_counter = IntegerField(default=0)

    def update_notification_date(self, remember):
        '''Return False if maximum iterations reached
        '''

        if remember and (self.iteration == len(time_intervals) - 1):
            # Learning process has finished
            with db.transaction():
                self.status = TaskStatus.DONE
                self.finish_date = get_current_timestamp()
                self.save()
            return False

        if remember:
            self.iteration += 1

        elif not remember:
            self.iteration = 0
            self.forgot_counter += 1

        self.status = TaskStatus.ACTIVE
        self.notification_date = generate_notification_date(self.iteration)

        with db.transaction():
            self.save()

        return get_time_delta(self.iteration)

    def set_status(self, status):
        with db.transaction():
            self.status = status
            self.save()

    @classmethod
    def find_task(cls, chat_id, content):
        try:
            return Task.get(
                (Task.chat_id == chat_id) &
                (Task.content == content))
        except DoesNotExist:
            return None

    @classmethod
    def get_active_tasks(cls):
        tasks = Task.select().where(
            (Task.notification_date <= get_current_timestamp()) &
            (Task.status == TaskStatus.ACTIVE))
        return tasks

    @classmethod
    def get_users_tasks(cls, chat_id):
        return Task.select().where(Task.chat_id == chat_id)

    def increase_forgot_counter(self, value=1):
        self.forgot_counter += value
        with db.transaction():
            self.save()

    def __repr__(self):
        return '<Task: chat_id={}, content={}>'.format(
            self.chat_id, self.content)

    @classmethod
    def create(cls, chat_id, content, **kwargs):
        task = Task.find_task(chat_id, content)
        if not task:
            with db.transaction():
                new_task = Task(chat_id=chat_id, content=content, **kwargs)
                new_task.save()
            return new_task
        else:
            task.update_notification_date(remember=False)
            return task

    def mark_done(self):
        with db.transaction():
            self.status = TaskStatus.DONE
            self.finish_date = get_current_timestamp()
            self.save()


class User(BaseModel):
    chat_id = IntegerField(index=True, default=0)
    public_api_key = CharField(index=True, default='')

    def generate_api_key(self):
        alph = [str(x) for x in range(10)] + [chr(97 + x) for x in range(26)]
        mess = ''.join([random.choice(alph) for x in range(API_KEY_SIZE)])
        key = '{}:{}'.format(self.chat_id, mess)
        with db.transaction():
            self.public_api_key = key
            self.save()

        return key

    @property
    def api_key(self):
        if not self.public_api_key:
            self.generate_api_key()

        return self.public_api_key

    @classmethod
    def find(cls, chat_id):
        try:
            return User.get(User.chat_id == int(chat_id))
        except DoesNotExist:
            return User.create(chat_id=chat_id)

    @classmethod
    def find_by_api_key(cls, api_key):
        try:
            return User.get(User.public_api_key == api_key)
        except DoesNotExist:
            return None

    def to_public_dict(self):
        return {
            'chat_id': self.chat_id,
            'api_key': self.public_api_key
        }


def create_tables():
    with db.transaction():
        for model in [Task, User]:
            if not model.table_exists():
                db.create_table(model)

create_tables()

import time
from datetime import datetime, timezone

from peewee import *

from utils import load_config


config = load_config()
DATABASE_NAME = config['database_name']
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
    def find_task(self, chat_id, content):
        try:
            return Task.get(
                (Task.chat_id == chat_id) &
                (Task.content == content))
        except DoesNotExist:
            return None

    @classmethod
    def get_active_tasks(self):
        tasks = Task.select().where(
            (Task.notification_date <= get_current_timestamp()) &
            (Task.status == TaskStatus.ACTIVE))
        return tasks

    @classmethod
    def get_users_tasks(self, chat_id):
        return Task.select().where(Task.chat_id == chat_id)

    def increase_forgot_counter(self, value=1):
        self.forgot_counter += value
        with db.transaction():
            self.save()

    def __repr__(self):
        return '<Task: chat_id={}, content={}>'.format(
            self.chat_id, self.content)

    @classmethod
    def create(self, chat_id, content, **kwargs):
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


def create_tables():
    with db.transaction():
        for model in [Task]:
            if not model.table_exists():
                db.create_table(model)

create_tables()

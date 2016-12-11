import time
from datetime import datetime, timezone

from peewee import *

DATABASE_NAME = 'tasks.db'
time_intervals = [1, 60, 120, 240]

db = SqliteDatabase(DATABASE_NAME)


def get_time_delta(delta_index):
    return time_intervals[delta_index]


class TaskStatus(object):
    WAITING_ANSWER = 0
    ACTIVE = 1
    DONE = 2


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
    chat_id = IntegerField(index=True, default=0)
    status = IntegerField(default=TaskStatus.ACTIVE)
    forgot_counter = IntegerField(default=0)

    def update_notification_date(self, remember):
        '''Return False if maximum iterations reached
        '''

        if remember and (self.iteration == len(time_intervals) - 1):
            # Learning process has finished
            self.status = TaskStatus.DONE
            with db.transaction():
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

    def __repr__(self):
        return 'Task<{}: {}>'.format(self.chat_id, self.content)


def create_tables():
    with db.transaction():
        for model in [Task]:
            if not model.table_exists():
                db.create_table(model)

create_tables()

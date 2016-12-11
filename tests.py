from unittest import TestCase, main
from unittest.mock import patch
from playhouse.test_utils import test_database
from peewee import *

import models
from models import Task, TaskStatus

test_db = SqliteDatabase(':memory:')


def create_task(**kwargs):
    with test_database(test_db, (Task,)):
        return Task.create(**kwargs)


class TestModelCreation(TestCase):

    @patch.object(models, 'time_intervals', [5, 10])
    @patch('models.get_current_timestamp')
    def test_task_default_creation(self, current_date):
        current_date.return_value = 100
        task = create_task()
        self.assertEqual(task.notification_date, current_date() + 5)
        self.assertEqual(task.status, TaskStatus.ACTIVE)

    def test_regular_task_creation(self):
        task = create_task(content='Hi', chat_id=52)
        self.assertEqual(task.content, 'Hi')
        self.assertEqual(task.chat_id, 52)


class TestUpdateNotificationDate(TestCase):

    def setUp(self):
        patcher = patch('models.get_current_timestamp')
        self.addCleanup(patcher.stop)
        self.mock_timestamp = patcher.start()
        self.current_date = 100
        self.mock_timestamp.return_value = self.current_date

    @patch.object(models, 'time_intervals', [1, 2, 3])
    def test_user_forgot_a_term(self):
        intervals = models.time_intervals

        task = create_task()
        delta = intervals[0]
        self.assertEqual(task.notification_date, self.current_date + delta)

        time_gap = task.update_notification_date(remember=False)
        new_date = task.notification_date

        self.assertEqual(new_date, self.current_date + intervals[0])
        self.assertEqual(time_gap, intervals[0])
        self.assertEqual(task.status, TaskStatus.ACTIVE)

        time_gap = task.update_notification_date(remember=False)
        self.assertEqual(time_gap, intervals[0])
        self.assertEqual(task.status, TaskStatus.ACTIVE)

    @patch.object(models, 'time_intervals', [1, 2, 3])
    def test_user_remember_a_term(self):
        intervals = models.time_intervals

        task = create_task()

        task.update_notification_date(remember=True)
        new_date = task.notification_date
        self.assertEqual(new_date, self.current_date + intervals[1])
        self.assertEqual(task.status, TaskStatus.ACTIVE)

        task.update_notification_date(remember=True)
        new_date = task.notification_date
        self.assertEqual(new_date, self.current_date + intervals[2])
        self.assertEqual(task.status, TaskStatus.ACTIVE)

    @patch.object(models, 'time_intervals', [2, 3])
    def test_maximum_intervals_reached(self):
        task = create_task()
        task.update_notification_date(remember=True)
        time_gap = task.update_notification_date(remember=True)
        self.assertFalse(time_gap)
        self.assertEqual(task.status, TaskStatus.DONE)


class TestCommonOperations(TestCase):

    def test_change_status(self):
        task = create_task()
        task.set_status(TaskStatus.DONE)
        self.assertEqual(task.status, TaskStatus.DONE)
        task.set_status(TaskStatus.ACTIVE)
        self.assertEqual(task.status, TaskStatus.ACTIVE)

    def test_forgot_counter(self):
        task = create_task()
        self.assertEqual(task.forgot_counter, 0)
        task.update_notification_date(remember=True)
        self.assertEqual(task.forgot_counter, 0)
        task.update_notification_date(remember=False)
        task.update_notification_date(remember=False)
        self.assertEqual(task.forgot_counter, 2)
        task.update_notification_date(remember=True)
        self.assertEqual(task.forgot_counter, 2)

    def test_find_task(self):
        with test_database(test_db, (Task,)):
            Task.create(content='abc', chat_id=1)
            Task.create(content='abc', chat_id=2)
            Task.create(content='def', chat_id=1)
            Task.create(content='def', chat_id=2)

            task = Task.find_task(2, 'qqq')
            self.assertEqual(task, None)
            task = Task.find_task(2, 'def')
            self.assertEqual(task.chat_id, 2)
            self.assertEqual(task.content, 'def')

    @patch('models.get_current_timestamp')
    def test_get_active_tasks(self, current_date):
        current_date.return_value = 0

        with test_database(test_db, (Task,)):
            self.assertEqual(Task.get_active_tasks(), [])

            Task.create(status=TaskStatus.ACTIVE)
            Task.create(status=TaskStatus.ACTIVE)
            Task.create(status=TaskStatus.DONE)
            Task.create(status=TaskStatus.WAITING_ANSWER)
            current_date.return_value = 999999
            tasks = Task.get_active_tasks()

            self.assertEqual(len(tasks), 2)
            self.assertEqual(tasks[0].status, TaskStatus.ACTIVE)
            self.assertEqual(tasks[1].status, TaskStatus.ACTIVE)

if __name__ == '__main__':
    main()
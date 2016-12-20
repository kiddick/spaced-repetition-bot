from unittest import TestCase, main
from unittest.mock import patch, MagicMock
from playhouse.test_utils import test_database
from peewee import *

import models
import bot
from models import Task, TaskStatus
from utils import encode_callback_data, decode_callback_data, \
    render_template, format_task_content, decode_answer_option, \
    timestamp_to_date, load_config
from bot import callback_handler, remind_task_to_user, \
    AnswerOption, MessageTemplate


test_db = SqliteDatabase(':memory:')


class TestUtils(TestCase):

    @patch('utils.yaml.load')
    def test_load_config_intervals_multiplier(self, yaml_load):
        yaml_load.return_value = {
            'time_intervals': [1, 2, 3],
            'intervals_multiplier': 60
        }
        config = load_config()
        self.assertEqual(config['time_intervals'], [60, 120, 180])


class TestModelCreation(TestCase):

    @patch.object(models, 'time_intervals', [5, 10])
    @patch('models.get_current_timestamp')
    def test_task_default_creation(self, current_date):
        with test_database(test_db, (Task,)):
            current_date.return_value = 100
            task = Task.create(chat_id=1, content='stuff')
            self.assertEqual(task.notification_date, current_date() + 5)
            self.assertEqual(task.status, TaskStatus.ACTIVE)

    def test_regular_task_creation(self):
        with test_database(test_db, (Task,)):
            task = Task.create(content='Hi', chat_id=52)
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
        with test_database(test_db, (Task,)):
            intervals = models.time_intervals

            task = Task.create(chat_id=1, content='stuff')
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
        with test_database(test_db, (Task,)):
            intervals = models.time_intervals

            task = Task.create(chat_id=1, content='stuff')

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
        with test_database(test_db, (Task,)):
            task = Task.create(chat_id=1, content='stuff')
            task.update_notification_date(remember=True)
            time_gap = task.update_notification_date(remember=True)
            self.assertFalse(time_gap)
            self.assertEqual(task.status, TaskStatus.DONE)


class TestModelsCommonOperations(TestCase):

    def test_change_status(self):
        with test_database(test_db, (Task,)):
            task = Task.create(chat_id=1, content='stuff')
            task.set_status(TaskStatus.DONE)
            self.assertEqual(task.status, TaskStatus.DONE)
            task.set_status(TaskStatus.ACTIVE)
            self.assertEqual(task.status, TaskStatus.ACTIVE)

    @patch('models.get_current_timestamp')
    def test_mark_done(self, current_date):
        with test_database(test_db, (Task,)):
            task = Task.create(chat_id=1, content='stuff')
            task.mark_done()
            self.assertEqual(task.status, TaskStatus.DONE)
            self.assertEqual(task.finish_date, current_date())

    def test_forgot_counter(self):
        with test_database(test_db, (Task,)):
            task = Task.create(chat_id=1, content='stuff')
            self.assertEqual(task.forgot_counter, 0)
            task.update_notification_date(remember=True)
            self.assertEqual(task.forgot_counter, 0)
            task.update_notification_date(remember=False)
            task.update_notification_date(remember=False)
            self.assertEqual(task.forgot_counter, 2)
            task.update_notification_date(remember=True)
            self.assertEqual(task.forgot_counter, 2)

    def test_inc_forgot_counter(self):
        with test_database(test_db, (Task,)):
            task = Task.create(chat_id=1, content='stuff')
            task.increase_forgot_counter()
            self.assertEqual(task.forgot_counter, 1)
            task.increase_forgot_counter(20)
            self.assertEqual(task.forgot_counter, 21)

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

            Task.create(status=TaskStatus.ACTIVE, chat_id=1, content='1')
            Task.create(status=TaskStatus.ACTIVE, chat_id=1, content='2')
            Task.create(status=TaskStatus.DONE, chat_id=1, content='3')
            Task.create(
                status=TaskStatus.WAITING_ANSWER, chat_id=1, content='4')
            current_date.return_value = 999999
            tasks = Task.get_active_tasks()

            self.assertEqual(len(tasks), 2)
            self.assertEqual(tasks[0].status, TaskStatus.ACTIVE)
            self.assertEqual(tasks[1].status, TaskStatus.ACTIVE)

    def test_get_users_tasks(self):
        with test_database(test_db, (Task,)):
            Task.create(chat_id=1, content='first')
            Task.create(chat_id=7, content='second')
            Task.create(chat_id=7, content='third')

            self.assertEqual(len(Task.get_users_tasks(1)), 1)
            self.assertEqual(Task.get_users_tasks(1)[0].content, 'first')
            self.assertEqual(len(Task.get_users_tasks(7)), 2)


class TestBotCommon(TestCase):

    def test_encode_callback(self):
        data = encode_callback_data(1, 'text')
        self.assertEqual(data, '1@text')

        data = encode_callback_data(2, '@ text')
        self.assertEqual(data, '2@@ text')

        data = encode_callback_data(13, '1')
        self.assertEqual(data, '13@1')

    def test_decode_callback(self):
        data = encode_callback_data(1, 'message')
        self.assertEqual(decode_callback_data(data), 'message')

        data = encode_callback_data(12, '@text@')
        self.assertEqual(decode_callback_data(data), '@text@')

        data = encode_callback_data(0, ' one two ')
        self.assertEqual(decode_callback_data(data), ' one two ')

    def test_decode_answer_option(self):
        data = encode_callback_data(1, 'message')
        self.assertEqual(decode_answer_option(data), '1')

        data = encode_callback_data(12, '@12@')
        self.assertEqual(decode_answer_option(data), '12')

    def test_render_template(self):
        text = render_template('The {} who knocks', 'one')
        self.assertEqual(text, 'The one who knocks')

        text = render_template('{} {}', 2, 'args')
        self.assertEqual(text, '2 args')

        text = render_template('{} text', 'bold', bold=True)
        self.assertEqual(text, '*bold* text')

        self.assertEqual(render_template('Pure text'), 'Pure text')

        with self.assertRaises(IndexError):
            render_template('{} {} {}', 1)

        with self.assertRaises(IndexError):
            render_template('{}', 1, 2, 3)

    def test_format_content(self):
        content = ' Strip '
        self.assertEqual(format_task_content(content), 'Strip')

        content = 'upper'
        self.assertEqual(format_task_content(content), 'Upper')

        self.assertEqual(format_task_content(' a '), format_task_content('A'))

    def test_from_timestamp(self):
        pretty_date = timestamp_to_date(0)
        self.assertIn('01/01/1970', pretty_date)


class TestBotCallbacks(TestCase):

    def setUp(self):
        message = MagicMock(chat_id=777, message_id=111)
        callback_query = MagicMock(message=message, data='')
        self.update = MagicMock(callback_query=callback_query)
        self.bot = MagicMock()

        patcher = patch('bot.render_template')
        self.addCleanup(patcher.stop)
        self.mock_render = patcher.start()

    def answer(self, answer_option, text):
        ''' Emulate user click on a callback button'''
        data = encode_callback_data(answer_option, text)
        self.update.callback_query.data = data
        callback_handler(self.bot, self.update)

    def assertRendered(self, message_template):
        self.assertIn(message_template, self.mock_render.call_args[0])

    def test_add_task(self):
        with test_database(test_db, (Task,)):
            self.answer(AnswerOption.ADD_TASK, 'python')

            self.assertEqual(Task.select(), 1)
            task = Task.find_task(777, 'python')
            self.assertIsNotNone(task)
            self.assertEqual(task.status, TaskStatus.ACTIVE)
            self.assertRendered(MessageTemplate.ADD_CONFIRMATION)

    def test_remove_task(self):
        with test_database(test_db, (Task,)):
            Task.create(chat_id=777, content='python')
            self.answer(AnswerOption.REMOVE, 'python')

            task = Task.get()
            self.assertEqual(task.status, TaskStatus.DONE)
            self.assertGreater(task.finish_date, 0)
            self.assertRendered(MessageTemplate.REMOVAL_CONFIRM)

    @patch.object(models.Task, 'update_notification_date')
    def test_user_remember_task(self, update_date):
        with test_database(test_db, (Task,)):
            self.answer(AnswerOption.ADD_TASK, 'stuff')

            self.answer(AnswerOption.REMEMBER, 'stuff')

            update_date.assert_called_with(remember=True)
            self.assertRendered(MessageTemplate.REMEMBER)

    @patch.object(models.Task, 'update_notification_date')
    def test_user_forgot_task(self, update_date):
        with test_database(test_db, (Task,)):
            self.answer(AnswerOption.ADD_TASK, 'thing')

            self.answer(AnswerOption.FORGOT, 'thing')

            update_date.assert_called_with(remember=False)
            self.assertRendered(MessageTemplate.FORGOT)

    def test_cancel_task_creation(self):
        with test_database(test_db, (Task,)):
            self.answer(AnswerOption.CANCEL, 'text')

            self.assertEqual(len(Task.select()), 0)
            self.assertRendered(MessageTemplate.REGULAR_REPLY)

    def test_task_reminder(self):
        with test_database(test_db, (Task,)):
            task = Task.create(chat_id=777, content='Content')
            remind_task_to_user(self.bot, task)

            self.assertEqual(task.status, TaskStatus.WAITING_ANSWER)
            self.assertRendered(MessageTemplate.NOTIFICATION_QUESTION)

    @patch.object(models, 'time_intervals', [5])
    def test_user_has_learned_term(self):
        with test_database(test_db, (Task,)):
            self.answer(AnswerOption.ADD_TASK, 'Quick')
            self.answer(AnswerOption.REMEMBER, 'Quick')

            self.assertRendered(MessageTemplate.TERM_HAS_LEARNED)
            self.assertEqual(Task.get().status, TaskStatus.DONE)
            self.assertGreater(Task.get().finish_date, 0)

    def test_add_existing_active_task(self):
        with test_database(test_db, (Task,)):
            self.answer(AnswerOption.ADD_TASK, 'JS')
            self.answer(AnswerOption.ADD_TASK, 'JS')

            self.assertRendered(MessageTemplate.DUPLICATE_ACTIVE_TASK)
            self.assertEqual(len(Task.select()), 1)
            self.assertEqual(Task.get().forgot_counter, 1)

    def test_add_finished_task(self):
        with test_database(test_db, (Task,)):
            self.answer(AnswerOption.ADD_TASK, 'JS')
            self.answer(AnswerOption.REMOVE, 'JS')
            self.answer(AnswerOption.ADD_TASK, 'JS')

            self.assertRendered(MessageTemplate.DUPLICATE_DONE_TASK)
            self.assertEqual(len(Task.select()), 1)
            self.assertEqual(Task.get().forgot_counter, 1)


if __name__ == '__main__':
    main()

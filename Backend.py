import enum
import time
import requests
import traceback
from abc import ABC, abstractmethod
from hashlib import md5
from random import choice


def random_str(length):
    chars = [chr(a) for a in range(ord('a'), ord('z') + 1)]
    return ''.join(choice(chars) for _ in range(length))


class TempMail:
    def __init__(self):
        self.email = ''
        self.cookies = None
        self.inbox = {}

    def new_email(self):
        response = requests.get('https://api4.temp-mail.org/request/domains/format/json')
        self.cookies = response.cookies
        self.email = random_str(12) + choice(response.json())
        return self.email

    def check_inbox(self):
        response = requests.get(
            f'https://api4.temp-mail.org/request/mail/id/{md5(self.email.encode()).hexdigest()}/format/json',
            cookies=self.cookies
        )
        new_letters = []
        if 'error' in response.json():
            return []
        for letter in response.json():
            if not letter['_id']['$oid'] in self.inbox:
                new_letters.append(letter)
                self.inbox.update({letter['_id']['$oid']: letter})
        return new_letters


class SessionStatus(enum.Enum):
    SUCCESS = 0
    NON_CRITICAL_FAILURE = 1
    CRITICAL_FAILURE = -1


class AbstractWebsiteBackend(ABC):
    DISPLAY_NAME = 'AbstractWebsite'

    @abstractmethod
    def __init__(self, email=None):
        self.FREE_TRIALS = 1
        self.credentials = {
            'email': email,
            'password': random_str(10) + 'A$0'
        } if email is not None else None
        pass

    @abstractmethod
    def confirm_email(self, confirmation_email_text):
        pass

    @abstractmethod
    def session(self, **kwargs):
        return SessionStatus.CRITICAL_FAILURE

    @abstractmethod
    def login(self, credentials=None):
        pass

    @abstractmethod
    def logout(self):
        pass

    @abstractmethod
    def delete_account(self):
        pass


class ComplexSession:
    def __init__(self, backend: AbstractWebsiteBackend):
        self.backend = backend

    def _perform(self, session_arg_list=None, print_callback=print,
                 progress_callback=lambda progress_value: None,
                 finalize_callback=lambda: None):
        if session_arg_list is None:
            session_arg_list = []
        temp_mail = TempMail()
        counter = 0
        total_sessions = len(session_arg_list)

        while session_arg_list:
            counter += 1

            # Get session arguments ready
            session_args = session_arg_list[0]
            session_args['print_callback'] = print_callback
            session_args['progress_callback'] = lambda x: progress_callback((counter + x - 1) / total_sessions)

            # Check if account needs refresh
            if self.backend.FREE_TRIALS == 0 or self.backend.credentials is None:
                if self.backend.FREE_TRIALS == 0:
                    print_callback(f'{self.backend.DISPLAY_NAME} account expired, deleting...')
                    self.backend.delete_account()
                print_callback('Generating temporary email...')
                email = temp_mail.new_email()
                print_callback(f'Creating new {self.backend.DISPLAY_NAME} account...')
                self.backend.__init__(email)
                print_callback('Waiting for confirmation email...')
                inbox = temp_mail.check_inbox()
                while not inbox:
                    time.sleep(1)
                    inbox = temp_mail.check_inbox()
                print_callback('Confirming email...')
                self.backend.confirm_email(inbox[0]['mail_html'])
                print_callback('Logging in...')
                self.backend.login()

            # Start session
            print_callback('Performing session...\n')
            try:
                session_status = self.backend.session(**session_args)

                if session_status == SessionStatus.SUCCESS:
                    # Session completed successfully
                    print_callback(f'Session {counter} of {total_sessions} complete.\n')
                    self.backend.FREE_TRIALS -= 1
                    session_arg_list.pop(0)

                elif session_status == SessionStatus.NON_CRITICAL_FAILURE:
                    # Session completed with errors because of invalid data
                    print_callback(
                        f'Session {counter} of {total_sessions} failed '
                        f'with a non-critical error, session counter reverted.\n'
                    )
                    session_arg_list.pop(0)

                elif session_status == SessionStatus.CRITICAL_FAILURE:
                    # Some shit happened, delete account
                    print_callback(f'Session {counter} of {total_sessions} failed '
                                   'with a critical error. Discarding account...\n')
                    session_arg_list.pop(0)
                    self.backend.delete_account()

            except requests.exceptions.ChunkedEncodingError or requests.exceptions.ConnectionError:
                # Network error occured, retry session
                print_callback('Network connection lost, retrying...')
                counter -= 1

            except BaseException:
                # Some other exception was raised, print and abort complex session
                print_callback('Unhandled exception occurred:')
                print_callback(str(traceback.format_exc()))
                print_callback('Deleting account...')
                self.backend.delete_account()
                print_callback('Done.')
                finalize_callback()
                return

            # refresh progress
            progress_callback(counter / total_sessions)
        print_callback('All sessions complete, deleting account...')
        self.backend.delete_account()
        print_callback('Done.')
        finalize_callback()

    def perform(self, *args, **kw):
        pass

    def abort(self):
        try:
            self.backend.delete_account()
        except AttributeError:
            pass

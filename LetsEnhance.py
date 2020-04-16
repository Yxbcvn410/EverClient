import os
import time
import requests
from bs4 import BeautifulSoup
from hashlib import md5

from Backend import AbstractWebsiteBackend, SessionStatus, random_str, ComplexSession


class LetsEnhanceBackend(AbstractWebsiteBackend):
    DISPLAY_NAME = "Let's Enhance"

    def __init__(self, email=None):
        super().__init__(email)
        self.FREE_TRIALS = 5
        self.cookie = {
            f'amplitude_id_{random_str(29)}accletsenhance.io': random_str(244)
        }
        self.auth_token = None
        if email:
            requests.post(
                'https://letsenhance.io/api/v1/auth/signup',
                json={**self.credentials,
                      'email_subscriber': False,
                      'terms_agreed': True
                      },
                cookies=self.cookie
            )

    def confirm_email(self, confirmation_email):
        bs = BeautifulSoup(confirmation_email, features='html.parser')
        confirmation_link = bs.a['href'].replace('token/confirm-email', 'api/v1/auth/confirm_and_login/')
        self.auth_token = requests.post(confirmation_link, cookies=self.cookie).json()

    def session(self, **kwargs):
        if 'print_callback' in kwargs:
            echo = kwargs['print_callback']
        else:
            echo = print
        if 'progress_callback' in kwargs:
            progress = kwargs['progress_callback']
        else:
            def progress(progress_value):
                pass
        echo('Uploading image...')
        path = kwargs['image_path']
        image_info = requests.post(
            'https://letsenhance.io/api/v1/uploader/companion/s3/multipart',
            cookies=self.cookie,
            headers={'authorization': 'Bearer ' + self.auth_token['access_token']},
            json={'filename': path, 'type': 'image/jpeg'}
        ).json()
        requests.options(
            'https://letsenhance.io/api/v1/uploader/companion/s3/multipart/{uploadId}/1?key={key}'.format(**image_info)
        )
        upload_url = requests.get(
            'https://letsenhance.io/api/v1/uploader/companion/s3/multipart/{uploadId}/1?key={key}'.format(
                **image_info)
        ).json()['url']
        content = open(path, 'rb').read()
        requests.put(upload_url, content)
        requests.post(
            'https://letsenhance.io/api/v1/uploader/companion/s3/multipart/{uploadId}/complete?key={key}'.format(
                **image_info), cookies=self.cookie,
            json={'parts': [{'PartNumber': 1, 'ETag': f'"{md5(content).hexdigest()}"'}]})
        upload_props = requests.post(
            'https://letsenhance.io/api/v1/images/upload/from_s3',
            cookies=self.cookie,
            headers={'authorization': 'Bearer ' + self.auth_token['access_token']},
            json={'s3_file_key': image_info['key']}
        ).json()
        if 'image' in upload_props:
            image_props = upload_props['image']
        elif 'code' in upload_props and upload_props['code'] == 'wrong_data':
            return SessionStatus.NON_CRITICAL_FAILURE
        else:
            return SessionStatus.CRITICAL_FAILURE

        progress(0.25)
        echo('Requesting processing...')
        requests.post(
            'https://letsenhance.io/api/v1/images/process',
            cookies=self.cookie,
            headers={'authorization': 'Bearer ' + self.auth_token['access_token']},
            json=[{
                'original_id': image_info['key'],
                'mod': kwargs['mod'] if 'mod' in kwargs else "magic AUTO JPEG",
                'width': image_props['width'] * 4,
                'height': image_props['height'] * 4
            }]
        )

        progress(0.5)
        echo('Waiting for image to be processed...')
        processed_instances = {}
        while not processed_instances:
            time.sleep(1)
            processed_instances = requests.post(
                'https://letsenhance.io/api/v1/images/in-process',
                cookies=self.cookie,
                headers={'authorization': 'Bearer ' + self.auth_token['access_token']},
                json={'ids': [image_info['key']]}
            ).json()[0]['versions']

        progress(0.75)
        echo('Downloading image...')
        download_url = processed_instances.popitem()[1]['download_url']
        target_dir = kwargs.get('target_path', 'image_directory')
        image_writer = open(target_dir + os.sep + kwargs['image_path'].split(os.sep)[-1], 'wb')
        image_writer.write(requests.get(download_url).content)
        image_writer.close()
        return SessionStatus.SUCCESS

    def login(self, credentials=None):
        pass

    def logout(self):
        pass

    def delete_account(self):
        try:
            requests.post(
                'https://letsenhance.io/api/v1/auth/delete-account',
                cookies=self.cookie,
                headers={'authorization': 'Bearer ' + self.auth_token['access_token']}
            )
        except TypeError:
            raise ValueError('Account not created or not validated yet')
        self.credentials = None


class LetsEnhanceComplexSession(ComplexSession):
    def __init__(self):
        super().__init__(LetsEnhanceBackend())

    def perform(self, images: str or list, target_dir: str, print_callback, progress_callback):
        if images is None:
            return
        if type(images) == str:
            images = [images]
        super()._perform(
            session_arg_list=[{'image_path': image_path, 'target_path': target_dir} for image_path in images],
            print_callback=print_callback, progress_callback=progress_callback)

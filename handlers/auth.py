from base import BaseHandler

import re
import json

from webapp2_extras import auth
from google.appengine.api import images
from google.appengine.api import urlfetch

class LoginHandler(BaseHandler):
    def get(self):
        self.render_template('login.html')

    def post(self):
        email = self.request.get('email')
        password = self.request.get('password')

        if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
            self.render_template('login.html', {'error': 'Invalid Email'})
            return

        try:
            user = self.auth.get_user_by_password(email, password, remember=True, save_session=True)
            user = self.user_model.get_by_auth_id(user['email'])

            if user.auth_mode != 'email':
                self.render_template('login.html', {'error': 'Email already registered'})
                return

            self.redirect('/')
        except (auth.InvalidAuthIdError, auth.InvalidPasswordError) as e:
            self.render_template('login.html', {'error': 'Invalid Username or Password'})

    def logout(self):
        self.auth.unset_session()
        self.redirect('/')

class RegisterHandler(BaseHandler):
    def get(self):
        self.render_template('register.html')

    def post(self):
        name = self.request.get('name')
        surname = self.request.get('surname')
        email = self.request.get('email')

        if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
            self.render_template('register.html', {'error': 'Invalid Email'})
            return

        if len(self.request.get('password')) < 6:
            self.render_template('register.html', {'error': 'Password must be at least 6 char'})
            return

        if self.request.get('password') != self.request.get('password_verification'):
            self.render_template('register.html', {'error': 'Password doesn\'t match'})
            return

        if not self.request.get('name'):
            self.render_template('register.html', {'error': 'Name is required'})
            return

        password = self.request.get('password')

        user, error = self.create_user(name, surname, email, password, 'email')

        if not user:
            self.render_template('register.html', error)
            return

        self.render_template('login.html')

    def post_facebook(self):
        result = urlfetch.fetch(url='https://graph.facebook.com/v2.5/me?fields=id,first_name,last_name,picture.width(400),email&access_token=%s' % self.request.get('access_token'),
                                method=urlfetch.GET)

        if result.status_code != 200:
            self.response.set_status(501)
            return

        result = json.loads(result.content)

        if not result['email']:
            self.response.status = 501
            self.response.write('Unable to retrieve email address')
            return

        user = self.user_model.get_by_auth_id(result['email'])

        if not user:
            user, error = self.create_user(result['first_name'], result['last_name'], result['email'], '', 'facebook')
            if not user:
                self.response.status = 501
                self.response.write(error)
                return

        if user.auth_mode != 'facebook':
            self.response.status = 501
            self.response.write('Auth mode doen\'t match, previuosly: %s' % user.auth_mode.capitalize())
            return

        self.get_image(user, result['picture']['data']['url'])

        self.auth.set_session(self.auth.store.user_to_dict(user), remember=True)

    def post_google(self):
        result = urlfetch.fetch(url="https://www.googleapis.com/oauth2/v1/userinfo?access_token=%s" % self.request.get('access_token'),
                                method=urlfetch.GET)

        if result.status_code != 200:
            self.response.set_status(501)
            return

        result = json.loads(result.content)

        if not result['email']:
            self.response.status = 501
            self.response.write('Unable to retrieve email address')
            return

        user = self.user_model.get_by_auth_id(result['email'])

        if not user:
            user, error = self.create_user(result['given_name'], result['family_name'], result['email'], '', 'google')
            if not user:
                self.response.status = 501
                self.response.write(error)
                return

        if user.auth_mode != 'google':
            self.response.status = 501
            self.response.write('Auth mode doen\'t match, previuosly: %s' % user.auth_mode.capitalize())
            return

        self.get_image(user, result['picture'])

        self.auth.set_session(self.auth.store.user_to_dict(user), remember=True)

    def post_github(self):
        result = urlfetch.fetch(url="https://api.github.com/user?access_token=%s" % self.request.get('access_token'),
                                method=urlfetch.GET)

        if result.status_code != 200:
            self.response.set_status(501)
            return

        result = json.loads(result.content)

        if not result['email']:
            self.response.status = 501
            self.response.write('Unable to retrieve email address')
            return

        user = self.user_model.get_by_auth_id(result['email'])

        if not user:
            user, error = self.create_user(result['name'], '', result['email'], '', 'github')
            if not user:
                self.response.status = 501
                self.response.write(error)
                return

        if user.auth_mode != 'github':
            self.response.status = 501
            self.response.write('Auth mode doen\'t match, previuosly: %s' % user.auth_mode.capitalize())
            return

        self.get_image(user, result['avatar_url'])

        self.auth.set_session(self.auth.store.user_to_dict(user), remember=True)

    def create_user(self, name, surname, email, password, auth_mode):
        user_data = self.user_model.create_user(email,
                                    ['email'],
                                    email=email,
                                    password_raw=password,
                                    name=name,
                                    surname=surname,
                                    auth_mode=auth_mode,
                                    total_tasks=0,
                                    completed_tasks=0,
                                    wunder_token='',
                                    verified=False)

        if user_data[0]:
            return user_data[1], None
        else:
            return None, {
                'error': 'Email %s already exists' % (email)
            }

    def get_image(self, user, url):
        result = urlfetch.fetch(url)

        if result.status_code == 200:
            img = images.resize(result.content, 200, 200)
            user.image = img
            user.put()
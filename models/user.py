import webapp2_extras.appengine.auth.models
from google.appengine.ext import ndb
from webapp2_extras import security


class User(webapp2_extras.appengine.auth.models.User):
    email = ndb.StringProperty(indexed=False, required=False)
    password = ndb.StringProperty(indexed=False, required=False)
    name = ndb.StringProperty(indexed=False, required=False)
    surname = ndb.StringProperty(indexed=False, required=False)

    def set_password(self, raw_password):
        """Sets the password for the current user

        :param raw_password:
            The raw password which will be hashed and stored
        """
        self.password = security.generate_password_hash(raw_password, length=12)
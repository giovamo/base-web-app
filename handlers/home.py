from base import BaseHandler


class HomeHandler(BaseHandler):
    def get(self):
        self.render_template('home.html')
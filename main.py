#!/usr/bin/env python

import logging
from webapp2 import WSGIApplication, Route
from google.appengine.ext.webapp import template


def handle_404(request, response, exception):
    logging.exception(exception)
    #if 'api' in request.url:
    #   return

    response.write(template.render('templates/errors/404.html', {}))
    response.set_status(404)

def handle_500(request, response, exception):
    logging.exception(exception)
    #if 'api' in request.url:
    #    return

    response.write(template.render('templates/errors/500.html', {}))
    response.set_status(500)

config = {
    'webapp2_extras.auth': {
        'user_model': 'models.User',
        'user_attributes': ['email']
    },
    'webapp2_extras.sessions': {
        'secret_key': 'uye569YTu4hTDdud7dghid6e7EDy'
    }
}

routes = [
    Route('/', handler='handlers.HomeHandler'),
    Route('/login', handler='handlers.LoginHandler'),
    Route('/register', handler='handlers.RegisterHandler'),
    Route('/logout', handler='handlers.LoginHandler:logout', name='logout')
]

app = WSGIApplication(routes, config=config, debug=True)

app.error_handlers[404] = handle_404
app.error_handlers[500] = handle_500

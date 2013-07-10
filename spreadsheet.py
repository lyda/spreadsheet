#!/usr/bin/python

__author__ = 'Kevin Lyda <kevin@ie.suberic.net>'

import sys
import readline
import os.path
import gdata.auth
import gdata.spreadsheets.client
import gdata.client
import yaml
import gflags
import BaseHTTPServer
import socket

FLAGS = gflags.FLAGS
gflags.DEFINE_string('conf', '.spreadsheet.yaml', 'Config file.')

class OAuthHTTPServer(BaseHTTPServer.HTTPServer):
  def __init__(self, server_address, RequestHandlerClass):
    # Note: Not using super() here because BaseHTTPServer.HTTPServer is
    # an "old-style" object. Sigh.
    BaseHTTPServer.HTTPServer.__init__(self,
        server_address, RequestHandlerClass)
    self.oauth_url = None

  def get_oauth_url(self):
    while self.oauth_url == None:
      self.handle_request()
    self.server_close()

class OAuthHTTPHandler(BaseHTTPServer.BaseHTTPRequestHandler):
  def _simple_response(self, code, title='', body=''):
    self.send_response(code)
    self.send_header('Content-type', 'text/html')
    self.end_headers()
    self.wfile.write(
        '<html><head><title>%s</title></head><body>%s</body></html>' %
        (title, body))

  def do_GET(self):
    if 'oauth_verifier' in self.path:
      # TODO: window.close only works with pages that javascript opened.
      self._simple_response(200, body='<script>window.close();</script>')
      self.server.oauth_url = self.path
    else:
      self._simple_response(200, title='Error', body='No OAuth received.')

class Config(object):
  def __init__(self, config_file):
    self._config_file = config_file
    try:
      self._conf = yaml.load(open(self._config_file, 'r'))
    except IOError:
      self._conf = dict()

  def __len__(self):
    return len(self._conf)

  def __getitem__(self, key):
    return self._conf[key]

  def __setitem__(self, key, value):
    self._conf[key] = value
    with open(self._config_file, 'w') as conf:
      conf.write(yaml.dump(self._conf))

  def __delitem__(self, key):
    del(self._conf[key])
    with open(self._config_file, 'w') as conf:
      conf.write(yaml.dump(self._conf))

  def __iter__(self):
    return self._conf.__iter__()

  def next(self):
    return self._conf.next()


class Spreadsheet(object):

  def __init__(self, conf):
    self._conf = conf
    self._gd = gdata.spreadsheets.client.SpreadsheetsClient()

    self._port = 49301
    self._httpd = None
    while self._httpd == None:
      # TODO: This could loop past port==65k or ignore other errors.
      #       Make the loop smarter.
      try:
        self._httpd = OAuthHTTPServer(('127.1', self._port), OAuthHTTPHandler)
      except socket.error:
        self._port += 1
        self._httpd = None

    try:
      self._reuseAuth()
    except KeyError:
      self._initialAuth()
    if 'id' not in self._conf:
      self._pickSpreadsheet()
    if 'wsid' not in self._conf:
      self._pickWorksheet()
    self._getHeaders()

  def _initialAuth(self):
    request_token = self._gd.get_oauth_token(
        scopes=['https://spreadsheets.google.com/feeds/'],
        next='http://localhost:%s/' % self._port,
        consumer_key='322152070718.apps.googleusercontent.com',
        consumer_secret='4gF964cqCqImms0mH13HAbWf')
    print 'Authorization URL: %s ' % request_token.generate_authorization_url(
        google_apps_domain='ie.suberic.net')
    self._httpd.get_oauth_url()
    gdata.gauth.authorize_request_token(request_token,
        self._httpd.oauth_url)
    self._gd.auth_token = self._gd.get_access_token(request_token)
    self._conf['access_token'] = gdata.gauth.token_to_blob(self._gd.auth_token)

  def _reuseAuth(self):
    self._gd.auth_token = gdata.gauth.token_from_blob(
        self._conf['access_token'])

  def _ask_user(self, question):
    response = raw_input(question)
    try:
      choice = int(response) - 1
      return choice
    except ValueError:
      if response == 'q':
        sys.exit(1)
    return None

  def _pickSpreadsheet(self):
    feed = self._gd.get_spreadsheets()
    sheets = list(
        enumerate(feed.entry, start=1))

    choice = None
    for i, sheet in sheets:
      print '%d. %s' % (i, sheet.title.text)
      if i % 10 == 0:
        choice = self._ask_user(
            'Return to continue list, q to quit, # to choose: ')
        if choice != None:
          break
    if choice == None:
      choice = self._ask_user('Press q to quit or # to choose: ')
      if choice == None:
        sys.exit(1)

    if choice >= 0:
      id_parts = sheets[choice][1].id.text.split('/')
      self._conf['id'] = id_parts[len(id_parts) - 1]

  def _pickWorksheet(self):
    feed = self._gd.get_worksheets(self._conf['id'])
    sheets = list(enumerate(feed.entry, start=1))

    choice = None
    for i, sheet in sheets:
      print '%d. %s' % (i, sheet.title.text)
      if i % 10 == 0:
        choice = self._ask_user(
            'Return to continue list, q to quit, # to choose: ')
        if choice != None:
          break
    if choice == None:
      choice = self._ask_user('Press q to quit or # to choose: ')
      if choice == None:
        sys.exit(1)

    if choice >= 0:
      id_parts = sheets[choice][1].id.text.split('/')
      self._conf['wsid'] = id_parts[len(id_parts) - 1]

  def _getHeaders(self):
    col = 1
    self._headers = []
    while True:
      cell = self._gd.GetCell(self._conf['id'], self._conf['wsid'], 1, col)
      if cell.content.text != None:
        self._headers.append(cell.content.text)
      else:
        break
      col += 1

  def update(self, keyname, key, valuename, value):
    """Update a cell in a spreadsheet.

    Find 'key' in the column labeled 'keyname' and then set 'value'
    in the same row but in the column named 'valuename.'

    Example: Say column 1 is called 'Host' and column 2 is called
    'OS'. If this was called with ('Host', 'foo', 'OS', 'Multics')
    then the cell in the 'OS' column in the same row as 'foo' in
    the 'Host' column would be set to 'Multics.'
    """
    search_col = self._headers.index(keyname) + 1
    update_col = self._headers.index(valuename) + 1
    row = 2
    found = False
    while not found:
      cell = self._gd.GetCell(self._conf['id'], self._conf['wsid'],
          row, search_col)
      if cell.content.text == None:
        break
      if cell.content.text == key:
        found = True
      else:
        row += 1
    if found:
      cell = self._gd.GetCell(self._conf['id'], self._conf['wsid'],
          row, update_col)
      cell.cell.input_value = value
      self._gd.update(cell)

  def print_list(self, keyname):
    """List a named column in a spreadsheet.

    List the column labeled 'keyname.'
    """
    col = self._headers.index(keyname) + 1
    row = 2
    while True:
      cell = self._gd.GetCell(self._conf['id'], self._conf['wsid'], row, col)
      if cell.content.text == None:
        break
      print cell.content.text
      row += 1

if __name__ == '__main__':
  try:
    sys.argv = FLAGS(sys.argv)  # parse flags
  except gflags.FlagsError, err:
    print '%s\\nUsage: %s ARGS\\n%s' % (err, sys.argv[0], FLAGS)
    sys.exit(1)
  conf = Config(FLAGS.conf)
  ss = Spreadsheet(conf)
  if sys.argv[1] == 'update':
    ss.update(*sys.argv[2:])
  elif sys.argv[1] == 'list':
    ss.print_list(*sys.argv[2:])

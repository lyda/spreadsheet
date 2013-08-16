===========
spreadsheet
===========

Command Line Tool To Manipulate Google Spreadsheets
===================================================
The ``spreadsheet`` tool is a command line tool to manipulate Google
spreadsheets. It specifically works on spreadsheets where row 1 is
a series of column titles and there is one or more columns that can
act as a unique key.

When running it it will create three config files in the current
directory:

* ``.app.json``: Configuration file with the app configuration.  By
  default these are anonymous, but if you have Google Apps for your
  domain, you might want to set these. TODO: Explain how and provide
  urls to Google help docs and the app admin panel for this.
  (console: https://code.google.com/apis/console ; docs: ?)
* ``.auth.json``: These store your auth credentials. The ``spreadsheet``
  tool will manipulate these.
* ``.ss.json``: This records the spreadsheet and worksheet you chose
  as well as any infor the ``spreadsheet`` tool has cached.

If these need info from you, you will be prompted.

Commands
~~~~~~~~

All references to "column" mean the title of the column.

spreadsheet app_conf "consumer_key" "consumer_secret" "google_apps_domain"
spreadsheet list "key column"
spreadsheet update "key column" key "value column" value
spreadsheet remember headers
spreadsheet remember "column"
spreadsheet forget headers
spreadsheet forget "column"

Dependencies
~~~~~~~~~~~~

Depends on the following modules: ``gdata``, ``json``, ``gflags``.

Contributions
=============
Contributions are welcome!

Unit tests are kind of difficult since I haven't found a good mock
spreadsheet.

The packaged version is available via ``pip`` or ``easy_install``
as ``spreadsheet``. The project page is on `pypi`_:

The source code is available in the following locations:

* Bitbucket: https://bitbucket.org/lyda/spreadsheet/
* code.google: https://code.google.com/p/spreadsheet-cl/
* Github: https://github.com/lyda/spreadsheet
* Gitorious: https://gitorious.org/uu/spreadsheet
* Sourceforge: https://sourceforge.net/p/spreadsheet-cl

Pull requests on any of those platforms or emailed patches are fine.
Opening issues on github is easiest, but I'll check any of them.

TODO
====

Authentication
~~~~~~~~~~~~~~

* Currently authentication redirects to a local url. Document that
  url and give the user the option to change it.
* Likewise, it currently listens on localhost and a dynamically
  chosen port. Provide a way to supply that.
* Might also print the url the browser will redirect to.
* Clean up how the auth token is found by the listener.
* Have the listener display a page saying auth success.

Testing and API
~~~~~~~~~~~~~~~
* Some unit tests of some sort.
* Ideas for mocking gdata?
* Is `issue580`_ fixed yet? If so remove the ``str()`` calls for
  GetCells parameters.
* Code layout - split things into modules so it's not one monlithic
  script now that there's an install process.

Features and hardening
~~~~~~~~~~~~~~~~~~~~~~
* A way to add rows.  And a way to delete them.
* Finish allowing users to specify the title row number.
* A command similar to update that allows users to specify the
  row/column directly.
* Have caching be more seemless. When using cache, do sanity checks
  to make sure it's correct (check the search column and the header)
  and then recache if it's a miss.  Keep the forget/remember commands
  in case the user knows the caches are wrong and can use these to
  tell us ahead of time.
* Handle a bunch of possible exceptions in the gdata API.
* Do command parsing better.

Credits
=======
- `Kevin Lyda`_: Spreadsheets are fine once I can script them...

.. _`Kevin Lyda`: https://github.com/lyda
.. _`pypi`: https://pypi.python.org/pypi/spreadsheet
.. _`issue580`: https://code.google.com/p/gdata-python-client/issues/detail?id=580

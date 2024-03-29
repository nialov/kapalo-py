Documentation
=============

|Documentation Status| |PyPI Status| |CI Test| |Coverage|

Introduction
------------

Create webmaps and export kapalo observations as cvs.

Running tests
-------------

To run pytest in currently installed environment:

.. code:: bash

   poetry run pytest

To run full extensive test suite:

.. code:: bash

   poetry run doit
   # Add -n <your-cpu-core-count> to execute tasks in parallel
   # E.g.
   poetry run doit -n 8 -v 0
   # -v 0 is added to limit verbosity to mininum (optional)
   # doit makes sure tasks are run in the correct order
   # E.g. if a task uses a requirements.txt file that other task produces
   # the producer is run first even with parallel execution

Formatting and linting
----------------------


Formatting & linting:

.. code:: bash

   poetry run doit pre_commit
   poetry run doit lint

Building docs
-------------

Docs can be built locally to test that ``ReadTheDocs`` can also build them:

.. code:: bash

   poetry run doit docs

doit usage
----------

To list all available commands from ``dodo.py``:

.. code:: bash

   poetry run doit list

Development
~~~~~~~~~~~

Development dependencies for ``kapalo_py`` include:

-  ``poetry``

   -  Used to handle Python package dependencies.

   .. code:: bash

      # Use poetry run to execute poetry installed cli tools such as invoke,
      # nox and pytest.
      poetry run <cmd>


-  ``doit``

   -  A general task executor that is a replacement for a ``Makefile``
   -  Understands task dependencies and can run tasks in parallel
      even while running them in the order determined from dependencies
      between tasks. E.g. requirements.txt is a requirement for running
      tests and therefore the task creating requirements.txt will always
      run before the test task.

   .. code:: bash

      # Tasks are defined in dodo.py
      # To list doit tasks from command line
      poetry run doit list
      # To run all tasks in parallel (recommended before pushing and/or
      # committing)
      # 8 is the number of cpu cores, change as wanted
      # -v 0 sets verbosity to very low. (Errors will always still be printed.)
      poetry run doit -n 8 -v 0

-  ``nox``

   -  ``nox`` is a replacement for ``tox``. Both are made to create
      reproducible Python environments for testing, making docs locally, etc.

   .. code:: bash

      # To list available nox sessions
      # Sessions are defined in noxfile.py
      poetry run nox --list

-  ``copier``

   -  ``copier`` is a project templater. Many Python projects follow a similar
      framework for testing, creating documentations and overall placement of
      files and configuration. ``copier`` allows creating a template project
      (e.g. https://github.com/nialov/nialov-py-template) which can be firstly
      cloned as the framework for your own package and secondly to pull updates
      from the template to your already started project.

   .. code:: bash

      # To pull copier update from github/nialov/nialov-py-template
      poetry run copier update


-  ``pytest``

   -  ``pytest`` is a Python test runner. It is used to run defined tests to
      check that the package executes as expected. The defined tests in
      ``./tests`` contain many regression tests (done with
      ``pytest-regressions``) that make it almost impossible
      to add features to ``kapalo_py`` that changes the results of functions
      and methods.

   .. code:: bash

      # To run tests implemented in ./tests directory and as doctests
      # within project itself:
      poetry run pytest


-  ``coverage``

   .. code:: bash

      # To check coverage of tests
      # (Implemented as nox session!)
      poetry run nox --session test_pip

-  ``sphinx``

   -  Creates documentation from files in ``./docs_src``.

   .. code:: bash

      # To create documentation
      # (Implemented as nox session!)
      poetry run nox --session docs

Big thanks to all maintainers of the above packages!

License
~~~~~~~

Copyright © 2021, Nikolas Ovaskainen.

-----


.. |Documentation Status| image:: https://readthedocs.org/projects/kapalo-py/badge/?version=latest
   :target: https://kapalo-py.readthedocs.io/en/latest/?badge=latest
.. |PyPI Status| image:: https://img.shields.io/pypi/v/kapalo-py.svg
   :target: https://pypi.python.org/pypi/kapalo-py
.. |CI Test| image:: https://github.com/nialov/kapalo-py/workflows/test-and-publish/badge.svg
   :target: https://github.com/nialov/kapalo-py/actions/workflows/test-and-publish.yaml?query=branch%3Amaster
.. |Coverage| image:: https://raw.githubusercontent.com/nialov/kapalo-py/master/docs_src/imgs/coverage.svg
   :target: https://github.com/nialov/kapalo-py/blob/master/docs_src/imgs/coverage.svg

Documentation
=============

|Documentation Status| |PyPI Status| |CI Test| |Coverage|

Uses Bedrock of Finland 1:200k from Geological Survey of Finland
https://hakku.gtk.fi/

Running tests
-------------

To run pytest in currently installed environment:

.. code:: bash

   poetry run pytest

To run full extensive test suite:

.. code:: bash

   poetry run invoke test

Formatting and linting
----------------------

Formatting and linting is done with a single command. First formats,
then lints.

.. code:: bash

   poetry run invoke format-and-lint

Building docs
-------------

Docs can be built locally to test that ``ReadTheDocs`` can also build them:

.. code:: bash

   poetry run invoke docs

Invoke usage
------------

To list all available commands from ``tasks.py``:

.. code:: bash

   poetry run invoke --list

Development
~~~~~~~~~~~

Development dependencies include:

   -  invoke
   -  nox
   -  copier
   -  pytest
   -  coverage
   -  sphinx

Big thanks to all maintainers of the above packages!

License
~~~~~~~

Copyright © 2021, Nikolas Ovaskainen.

.. |Documentation Status| image:: https://readthedocs.org/projects/kapalo_py/badge/?version=latest
   :target: https://kapalo_py.readthedocs.io/en/latest/?badge=latest
.. |PyPI Status| image:: https://img.shields.io/pypi/v/kapalo_py.svg
   :target: https://pypi.python.org/pypi/kapalo_py
.. |CI Test| image:: https://github.com/nialov/kapalo_py/workflows/test-and-publish/badge.svg
   :target: https://github.com/nialov/kapalo_py/actions/workflows/test-and-publish.yaml?query=branch%3Amaster
.. |Coverage| image:: https://raw.githubusercontent.com/nialov/kapalo_py/master/docs_src/imgs/coverage.svg
   :target: https://github.com/nialov/kapalo_py/blob/master/docs_src/imgs/coverage.svg

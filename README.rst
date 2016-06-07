============
Odoo Updates
============

.. image:: https://img.shields.io/pypi/v/odoo_updates.svg
        :target: https://pypi.python.org/pypi/odoo_updates

.. image:: https://img.shields.io/travis/Vauxoo/odoo_updates.svg
        :target: https://travis-ci.org/Vauxoo/odoo_updates

.. image:: https://readthedocs.org/projects/odoo_updates/badge/?version=latest
        :target: https://readthedocs.org/projects/odoo_updates/?badge=latest
        :alt: Documentation Status


A few scripts packaged that get all changes to be applied into an Odoo database.

The main goal is to have a library and command line utility that allow us to see what changes are about to be applied into a production databases, not the commit list (which ATM is done in other project) but the changes reflected at database level (see TODO list for the features that will be integrated). So far no instance is needed, only needs an *original* database and an *updated* one (the result of -u all / -u module ) and the script will display (or return if you import the package).

Most of the functionality are still to be defined. If you have any suggestion/issue please leave it in the issues section.

* Free software: ISC license
* Documentation: https://odoo_updates.readthedocs.org.


TODO
----
* [X] Changes in the views
* [X] Changes in the menus
* [X] Changes in translations
* [] Changes in models
* [X] Tests


Features
--------

* TODO

Credits
-------

This package was created with Cookiecutter_ and the `audreyr/cookiecutter-pypackage`_ project template.

.. _Cookiecutter: https://github.com/audreyr/cookiecutter
.. _`audreyr/cookiecutter-pypackage`: https://github.com/audreyr/cookiecutter-pypackage



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

.. image:: https://coveralls.io/repos/github/Vauxoo/odoo_updates/badge.svg?branch=master
        :target: https://coveralls.io/github/Vauxoo/odoo_updates?branch=master
        :alt: Coverage Status


A few scripts packaged that get all changes to be applied into an Odoo database.

The main goal is to have a library and command line utility that allow us to see what changes are about to be applied into a production databases, not the commit list (which ATM is done in other project) but the changes reflected at database level (see TODO list for the features that will be integrated). So far no instance is needed, only needs an *original* database and an *updated* one (the result of -u all / -u module ) and the script will display (or return if you import the package).

Most of the functionality are still to be defined. If you have any suggestion/issue please leave it in the issues section.

* Free software: ISC license
* Documentation: https://odoo_updates.readthedocs.org.

HOW TO USE IT
-------------

As this is and alpha release we recommend to use a virtualenv:

    $ virtualenv some_name
    $ . some_name/bin/activate

Clone the repo and install it:

    $ git clone -b master https://github.com/Vauxoo/odoo_updates.git
    $ cd odoo_updates
    $ python setup.py install

Then you will need two databases to be compared, one is the "original" database before applying the changes
and the second one is the database after applying the changes (-u all or -u some_module).
We do not need the attachments nor the instance since this script compares only at database level.

So there will be two databases pre_udpates and post_updates (you can use the names that fits you the best),
to compare the both we execute and get only the changes in the views:

    $ updatesv -o pre_update -u post_update -c XXX -s views

Where:
*-o pre_update* is the original database or the database before the changes
*-u post_update* is the updated database
*-c XXX* Still not implemented, so can be anything
*-s* Sends the results to the screen
*views* Check only the changes made in the views (may be: views, translations or menus)

The operations can take a while depending on the database size.

Any suggestions or bug report feel free to create a [new issue](https://github.com/Vauxoo/odoo_updates/issues/new)

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



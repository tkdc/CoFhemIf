CoFhemIf
--------
Command line tool to request your `FHEM`_ server via http to control your electronic components
like room heating thermostat, switched socket-outlets or temperature sensors etc.


Installation and Usage
----------------------
Add the tool folder to your python library search path and check that all dependent libraries are available.

The tool has a prototypical status, you must adapt the init procedure to your FHEM configuration.

Execute in python console:

    >>> from cofhemif import CoFhemIf
    >>> mf = CoFhemIf()


Licence
-------
CoFhemIf is released under the `GNU GPL v3`_ license.

.. _FHEM: https://fhem.de/
.. _GNU GPL v3: https://www.gnu.org/licenses/gpl.html

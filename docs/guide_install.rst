.. _installation:

Installation Guide
---------------------------

1) Get the correct Python

Before installing Ralph, make sure that you have Python 3.12
installed on your machine. Ralph should support any Python above 3.10,
but it was built and tested with Python 3.12.

* Make sure to install `python3.12`, `python3.12-venv`, and `python3.12-dev`.
Otherwise many packages won't be able to install properly.

2) Create a virtual environment
Now, let's create a virtual environment.
This will ensure that your python versions and packages don't collide
with whatever Ralph needs and vice-versa.

.. code-block:: console

   >> python3.12 -m venv path_to_your_venv

To activate your newly created virtual environment use the following command:

* in bash:

.. code-block:: console

   >> source path_to_your_venv/bin/activate

* in tcshell:

.. code-block:: console

   >> source path_to_your_venv/bin/activate.tcsh

3) Update your pip

To ensure smooth installation of Ralph, make sure to have your pip updated to
at least 24.0 version.

4) Clone the repository and install Ralph

Now you can clone the repository. Once you do run the following commands:
.. code-block:: console

   >> python -m pip install .

To check if the installation went through succesfully, run the test suite:

.. code-block:: console

   >> python -m pip install .

Hurray! Now you can deploy Ralph to do help you with your microlensing events!
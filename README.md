
# Ralph

Ralph is a package that will help you model batches of microlensing events.

[![Template](https://img.shields.io/badge/Template-LINCC%20Frameworks%20Python%20Project%20Template-brightgreen)](https://lincc-ppt.readthedocs.io/en/latest/)

[![PyPI](https://img.shields.io/pypi/v/ralph?color=blue&logo=pypi&logoColor=white)](https://pypi.org/project/ralph/)
[![GitHub Workflow Status](https://img.shields.io/github/actions/workflow/status/KKruszynska/ralph/smoke-test.yml)](https://github.com/KKruszynska/ralph/actions/workflows/smoke-test.yml)
[![Codecov](https://codecov.io/gh/KKruszynska/ralph/branch/main/graph/badge.svg)](https://codecov.io/gh/KKruszynska/ralph)
[![Read The Docs](https://img.shields.io/readthedocs/ralph)](https://ralph.readthedocs.io/)
[![Benchmarks](https://img.shields.io/github/actions/workflow/status/KKruszynska/ralph/asv-main.yml?label=benchmarks)](https://KKruszynska.github.io/ralph/)

This project was automatically generated using the LINCC-Frameworks 
[python-project-template](https://github.com/lincc-frameworks/python-project-template).

For more information about the project template see the 
[documentation](https://lincc-ppt.readthedocs.io/en/latest/).

## Installation guide

1. Ensure that you have `python3.12` installed on your machine.
   - Make sure to install both `python3.12` and `python3.12-dev`
2. Create a virtual environment with `python3.12` for Ralph:

    `python3.12 -m venv path_to_your_venv`

3. Activate your newly created virtual environment:
    - in bash
    `source path_to_your_venv\bin\activate`
    - in tcshell
   `other command`
4. Update `pip` to at least 24.0
5. Clone Ralph's repository.
6. Go to the folder where you cloned the repository, and run:
    `python -m pip install .`
7. To make sure that the installation process went well, check if unit test run correctly:
    `pytest test/.`

If all went well, you should see an information that all unit tests passed!

Enjoy!
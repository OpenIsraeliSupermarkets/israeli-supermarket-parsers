Israel Supermarket Parsers: Clients to parser the data published by the supermarkets.
=======================================
This is a parser for ALL the supermarket chains listed in the GOV.IL site.

שקיפות מחירים (השוואת מחירים) - https://www.gov.il/he/departments/legalInfo/cpfta_prices_regulations
הגדרת הקבצים שהיו צריכים להיות זמינים באתרים - https://www.nevo.co.il/law_html/law01/501_131.htm


[![Unit & Integration Tests](https://github.com/OpenIsraeliSupermarkets/israeli-supermarket-parsers/actions/workflows/test-suite.yml/badge.svg?event=push)](https://github.com/OpenIsraeliSupermarkets/israeli-supermarket-parsers/actions/workflows/test-suite.yml)
[![CodeQL](https://github.com/OpenIsraeliSupermarkets/israeli-supermarket-parsers/actions/workflows/codeql.yml/badge.svg)](https://github.com/OpenIsraeliSupermarkets/israeli-supermarket-parsers/actions/workflows/codeql.yml)
[![Pylint](https://github.com/OpenIsraeliSupermarkets/israeli-supermarket-parsers/actions/workflows/pylint.yml/badge.svg)](https://github.com/OpenIsraeliSupermarkets/israeli-supermarket-parsers/actions/workflows/pylint.yml)
[![Publish Docker image](https://github.com/OpenIsraeliSupermarkets/israeli-supermarket-parsers/actions/workflows/docker-publish.yml/badge.svg)](https://github.com/OpenIsraeliSupermarkets/israeli-supermarket-parsers/actions/workflows/docker-publish.yml)
[![Upload Python Package](https://github.com/OpenIsraeliSupermarkets/israeli-supermarket-parsers/actions/workflows/python-publish.yml/badge.svg)](https://github.com/OpenIsraeliSupermarkets/israeli-supermarket-parsers/actions/workflows/python-publish.yml)


## 🤗 Want to support my work?
<p align="center">
    <a href="https://buymeacoffee.com/erlichsefi" target="_blank"><img src="https://cdn.buymeacoffee.com/buttons/v2/default-yellow.png" alt="Buy Me A Coffee" style="height: 60px !important;width: 217px !important;">
    </a>
</p> 

Got a question?
---------------

You can email me at erlichsefi@gmail.com

If you think you've found a bug:

- Create issue in [issue tracker](https://github.com/OpenIsraeliSupermarkets/israeli-supermarket-parsers/issues) to see if
  it's already been reported
- Please consider solving the issue by yourself and creating a pull request.

What is il_supermarket_parsers?
-------------

A simple access layer to the data the supermarkets publish.
You can download the data using https://github.com/OpenIsraeliSupermarkets/israeli-supermarket-parsers.

You only need to run the following code to parse all the data currently shared by the supermarkets and was downloaded using the package above.

```python
from il_supermarket_parsers import ConvertingTask

scraper = ConvertingTask(data_folder="dumps")
scraper.run()
```


Quick start
-----------

il_supermarket_parsers can be installed using pip:

    python3 pip install il_supermarket_parsers

If you want to run the latest version of the code, you can install it from the
repo directly:

    python3 -m pip install -U git+https://github.com/OpenIsraeliSupermarkets/israeli-supermarket-parsers.git
    # or if you don't have 'git' installed
    python3 -m pip install -U https://github.com/OpenIsraeliSupermarkets/israeli-supermarket-parsers/main
    

Contributing
------------

Help in testing, development, documentation and other tasks is
highly appreciated and useful to the project. There are tasks for
contributors of all experience levels.

If you need help getting started, don't hesitate to contact me.


Development status
------------------

IL SuperMarket Parser is beta software, as far as i see devlopment stoped until new issues will be found.

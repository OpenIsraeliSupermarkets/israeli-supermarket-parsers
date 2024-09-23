Israel Supermarket Parsers: Clients to parser the data published by the supermarkets.
=======================================
This is a scraper for ALL the supermarket chains listed in the GOV.IL site.

שקיפות מחירים (השוואת מחירים) - https://www.gov.il/he/departments/legalInfo/cpfta_prices_regulations
הגדרת התוצאות - https://www.nevo.co.il/law_html/law01/501_131.htm

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
You can download the data using https://github.com/erlichsefi/israeli-supermarket-scarpers.

You only need to run the following code to get all the data currently shared by the supermarkets.

```python
from il_supermarket_parsers import ConvertingTask

scraper = ConvertingTask()
scraper.run()
```


Please notice!
Since new files are constantly uploaded by the supermarket to their site, you will only get the current snapshot. In order to keep getting data, you will need to run this code more than one time to get the newly uploaded files.

Quick start
-----------

il_supermarket_scarper can be installed using pip:

    python3 pip install israeli-supermarket-parsers

If you want to run the latest version of the code, you can install it from the
repo directly:

    python3 -m pip install -U git+https://github.com/OpenIsraeliSupermarkets/israeli-supermarket-parsers.git
    # or if you don't have 'git' installed
    python3 -m pip install -U https://github.com/OpenIsraeliSupermarkets/israeli-supermarket-parsers/master
    

Contributing
------------

Help in testing, development, documentation and other tasks is
highly appreciated and useful to the project. There are tasks for
contributors of all experience levels.

If you need help getting started, don't hesitate to contact me.


Development status
------------------

IL SuperMarket Parser is beta software, as far as i see devlopment stoped until new issues will be found.


#git config --global --unset user.name && git config --global --unset user.email && git config --global --unset user.signingkey
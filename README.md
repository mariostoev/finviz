### Unofficial API for [finviz.com](http://finviz.com)

This project is in *active* development as of 11/15/2017

> **What is finviz?**
>
> Finviz is a stock market protal that provides traders with superior and detailed financial analysis, research, and data visualization.

### Important information

Any quotes data displayed on finviz.com is delayed by 15 minutes for NASDAQ, and 20 minutes for NYSE and AMEX. This API should **NOT** be used for live trading, it's main purpuse is financial analysis, research and data scraping.

### Using the screener

    import public
    
    fv = public.Finviz()
    
    searchFilters = ['cap_microunder', 'earningsdate_tomorrow', 'exch_nasd']    
    fv.search(filters=searchFilters, sort_by='country')
    
This returns a .json file called data.json, which contains a brief overview of the filtered options. 

The search() function takes exactly 4 arguments:
* (list) **tickers**
* (list) **filters**

You can find each filter arguments by executing a search on the website itself, while I find an easier solution

- (string) **sort_by**
- (int) **quantity** *(50 by default, and currently not implemented)*

### To do's:

- Limit the quantity of results saved from screener()
- Add SQL support
- Scrape data from individual symbol page

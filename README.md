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
    
This returns a .json file called data.json, which contains a brief overview of the filtered options and looks like this:
      
     {
        "1": {
        "Price": "6.58", 
        "Company": "Diana Containerships Inc.", 
        "Volume": "377,492", 
        "Change": "-1.79%", 
        "P/E": "-", 
        "Ticker": "DCIX", 
        "Number": "1", 
        "Industry": "Shipping", 
        "Country": "Greece", 
        "Sector": "Services", 
        "Market Cap": "5.09M"
    }, 
        "2" ...

The search() function takes exactly 4 arguments:
* (list) **tickers**
* (list) **filters**

You can find each filter arguments by executing a search on the website itself, while I find an easier solution

- (string) **sort_by**
- (int) **quantity** *(50 by default, and currently not implemented)*

### Performance

As of the latest update, after trial and error, I'll stop attempting to improve the performance of the scraper. Each command takes around 4 seconds to execute, and I've come to the conclusion that CPU performance is not the bottleneck here, but the internet speed. That means the time to complete each request to screener() will vary on your download speed.

### To do's:

- Limit the quantity of results saved from screener()
- Add CSV and SQL support
- Obtain information from the homepage
- Scrape data from individual symbol page

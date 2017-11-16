import public

fv = public.Finviz()

print(fv.search(filters=['cap_microunder', 'earningsdate_tomorrow', 'exch_nasd'], sort_by='country'))

# //*[@id="screener-content"]/table/tbody/tr[4]/td/table/tbody/tr[2]/td[1]/a

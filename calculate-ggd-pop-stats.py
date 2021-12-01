from os import environ
import sys
import pandas as pd
import requests
import time
import os
from datetime import date, datetime
from datetime import timedelta

def progress(*args):
    print(datetime.now(), "\t", *args, file=sys.stderr, flush=True)

progress("*** waiting for new data drop")
yesterday = date.today() - timedelta(days=1)
while not ("ALWAYS_RUN" in os.environ):
    r=requests.head('https://data.rivm.nl/covid-19/COVID-19_casus_landelijk.csv')
    if r.status_code == 200:
        date = pd.to_datetime(r.headers['Last-Modified'])
        if date.date() > yesterday:
            progress("Got update today: ", date)
            time.sleep(5)
            break
    progress("Sleeping 10s to wait for change, currently: ", date)
    time.sleep(10)
        
progress("*** Reading RIVM data")
cases = pd.read_csv('https://data.rivm.nl/covid-19/COVID-19_casus_landelijk.csv', 
    sep=';', parse_dates=["Date_statistics"], 
    usecols=["Date_statistics", "Date_statistics_type", "Agegroup", "Sex", "Municipal_health_service"])
cases = cases.applymap(lambda x: x.strip() if isinstance(x, str) else x)
progress("\n", cases)


progress("*** Reading population master file")
population = pd.read_csv('https://raw.githubusercontent.com/mzelst/covid-19/master/misc/population_masterfile.csv')
population = population.applymap(lambda x: x.strip() if isinstance(x, str) else x)
progress(population)


progress("*** Counting positive casus per GGD & agegroup")
merge_cols = ["Municipal_health_service", 'Agegroup', 'Date_statistics']
positive_cases = cases[~(cases.Agegroup.isin({'<50', 'Unknown'}))].copy()\
    .value_counts(subset=merge_cols, sort=True).reset_index(name="Count")

# fill in blanks
zeroes = pd.DataFrame({'Date_statistics': cases.Date_statistics.unique()}) \
    .merge(pd.DataFrame({'Agegroup': positive_cases.Agegroup.unique()}), how='cross') \
    .merge(pd.DataFrame({'Municipal_health_service': cases.Municipal_health_service.unique()}), how='cross')
zeroes['Count'] = 0

positive_cases = positive_cases.merge(zeroes, on=merge_cols, how="right", validate="one_to_one")
positive_cases['Count'] = (positive_cases.Count_x.fillna(0) + positive_cases.Count_y).astype(int)
del positive_cases['Count_x']
del positive_cases['Count_y']
positive_cases = positive_cases.rename(columns={
    "Municipal_health_service": "GGD_name", 
    "Agegroup": "Age_group", 
    "Date_statistics": "Date", 
    "Count": "Positive_cases"
})
progress("\n", positive_cases)


progress("*** Joining with GGD level population stats")
population = population[['GGD_name', 'Age_group', 'Population_2021', 'Population_2020']].copy()\
    .set_index(['GGD_name', 'Age_group'])\
    .groupby(by=["GGD_name", "Age_group"])\
    .sum()

positive_cases = positive_cases.set_index(['GGD_name', 'Age_group'])\
    .join(population, how="left") \
    .reset_index()

positive_cases['Population'] = positive_cases.Population_2021
positive_cases.loc[positive_cases.Date < '2021-01-01', 'Population'] = positive_cases[positive_cases.Date < '2021-01-01']['Population_2020']

progress("\n", positive_cases)

positive_cases['Positive_cases_per100k'] = (positive_cases.Positive_cases / positive_cases.Population) * 100_000

del positive_cases['Population_2020']
del positive_cases['Population_2021']
del positive_cases['Population']

progress("\n", positive_cases)


progress("*** Sorting and writing to disk")
positive_cases.sort_values(by=['Date','GGD_name','Age_group'], inplace=True)
positive_cases[["Date", "GGD_name", "Age_group", "Positive_cases", 'Positive_cases_per100k']].to_csv("data/rivm-cases-per-ggd-per-age-group.csv", index=False, chunksize=1000, float_format='%.3f')
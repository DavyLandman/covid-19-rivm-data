import pandas as pd
import numpy as np


print("*** Reading RIVM data")
cases = pd.read_csv('https://data.rivm.nl/covid-19/COVID-19_casus_landelijk.csv', 
    sep=';', parse_dates=["Date_statistics"], 
    usecols=["Date_statistics", "Date_statistics_type", "Agegroup", "Sex", "Municipal_health_service"])
cases = cases.applymap(lambda x: x.strip() if isinstance(x, str) else x)
print(cases)


#print("*** Reading population master file")
#population = pd.read_csv('https://raw.githubusercontent.com/mzelst/covid-19/master/misc/population_masterfile.csv')
#population = population.applymap(lambda x: x.strip() if isinstance(x, str) else x)
#print(population)


print("*** Counting positive casus per GGD & agegroup")
merge_cols = ["Municipal_health_service", 'Agegroup', 'Date_statistics']
positive_cases = cases[(cases.Date_statistics_type == 'DPL') & ~(cases.Agegroup.isin({'<50', 'Unknown'}))].copy()\
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
print(positive_cases)


#print("*** Joining with GGD level population stats")
#population = population[['GGD_name', 'Age_group', 'Population_2021', 'Population_2020']].copy()\
#    .set_index(['GGD_name', 'Age_group'])\
#    .groupby(by=["GGD_name", "Age_group"])\
#    .sum()
#
#positive_cases = positive_cases.set_index(['GGD_name', 'Age_group'])\
#    .join(population, how="left") \
#    .reset_index()
#
#print(positive_cases)



print("*** Sorting and writing to disk")
positive_cases.sort_values(by=['Date','GGD_name','Age_group'], inplace=True)
positive_cases[["Date", "GGD_name", "Age_group", "Positive_cases"]].to_csv("data/rivm-cases-per-ggd-per-age-group.csv", index=False, chunksize=1000)
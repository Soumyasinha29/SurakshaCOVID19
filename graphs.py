#!/usr/bin/env python
# coding: utf-8

# In[1]:


import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from pandas.plotting import register_matplotlib_converters
register_matplotlib_converters()
#%matplotlib inline
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
plt.rcParams['figure.figsize'] = [15, 5]
from IPython import display
from ipywidgets import interact, widgets


# In[5]:


ConfirmedCases_raw=pd.read_csv('https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data/csse_covid_19_time_series/time_series_covid19_confirmed_global.csv')


# In[7]:


Deaths_raw=pd.read_csv('https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data/csse_covid_19_time_series/time_series_covid19_deaths_global.csv')


# In[8]:


Recoveries_raw=pd.read_csv('https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data/csse_covid_19_time_series/time_series_covid19_recovered_global.csv')


# In[11]:


### Melt the dateframe into the right shape and set index
def cleandata(df_raw):
    df_cleaned=df_raw.melt(id_vars=['Province/State','Country/Region','Lat','Long'],value_name='Cases',var_name='Date')
    df_cleaned=df_cleaned.set_index(['Country/Region','Province/State','Date'])
    return df_cleaned 

# Clean all datasets
ConfirmedCases=cleandata(ConfirmedCases_raw)
Deaths=cleandata(Deaths_raw)
Recoveries=cleandata(Recoveries_raw)


# In[13]:


### Get Countrywise Data
def countrydata(df_cleaned,oldname,newname):
    df_country=df_cleaned.groupby(['Country/Region','Date'])['Cases'].sum().reset_index()
    df_country=df_country.set_index(['Country/Region','Date'])
    df_country.index=df_country.index.set_levels([df_country.index.levels[0], pd.to_datetime(df_country.index.levels[1])])
    df_country=df_country.sort_values(['Country/Region','Date'],ascending=True)
    df_country=df_country.rename(columns={oldname:newname})
    return df_country
  
ConfirmedCasesCountry=countrydata(ConfirmedCases,'Cases','Total Confirmed Cases')
DeathsCountry=countrydata(Deaths,'Cases','Total Deaths')
RecoveriesCountry=countrydata(Recoveries,'Cases','Total Recoveries')

### Get DailyData from Cumulative sum
def dailydata(dfcountry,oldname,newname):
    dfcountrydaily=dfcountry.groupby(level=0).diff().fillna(0)
    dfcountrydaily=dfcountrydaily.rename(columns={oldname:newname})
    return dfcountrydaily

NewCasesCountry=dailydata(ConfirmedCasesCountry,'Total Confirmed Cases','Daily New Cases')
NewDeathsCountry=dailydata(DeathsCountry,'Total Deaths','Daily New Deaths')
NewRecoveriesCountry=dailydata(RecoveriesCountry,'Total Recoveries','Daily New Recoveries')


# In[26]:


CountryConsolidated=pd.merge(ConfirmedCasesCountry,NewCasesCountry,how='left',left_index=True,right_index=True)
CountryConsolidated=pd.merge(CountryConsolidated,NewDeathsCountry,how='left',left_index=True,right_index=True)
CountryConsolidated=pd.merge(CountryConsolidated,DeathsCountry,how='left',left_index=True,right_index=True)
CountryConsolidated=pd.merge(CountryConsolidated,RecoveriesCountry,how='left',left_index=True,right_index=True)
CountryConsolidated=pd.merge(CountryConsolidated,NewRecoveriesCountry,how='left',left_index=True,right_index=True)
CountryConsolidated['Active Cases']=CountryConsolidated['Total Confirmed Cases']-CountryConsolidated['Total Deaths']-CountryConsolidated['Total Recoveries']
CountryConsolidated['Share of Recoveries - Closed Cases']=np.round(CountryConsolidated['Total Recoveries']/(CountryConsolidated['Total Recoveries']+CountryConsolidated['Total Deaths']),2)
CountryConsolidated['Death to Cases Ratio']=np.round(CountryConsolidated['Total Deaths']/CountryConsolidated['Total Confirmed Cases'],3)


# In[16]:


## Get totals for all metrics
GlobalTotals=CountryConsolidated.reset_index().groupby('Date').sum()
GlobalTotals['Share of Recoveries - Closed Cases']=np.round(GlobalTotals['Total Recoveries']/(GlobalTotals['Total Recoveries']+GlobalTotals['Total Deaths']),2)
GlobalTotals['Death to Cases Ratio']=np.round(GlobalTotals['Total Deaths']/GlobalTotals['Total Confirmed Cases'],3)
GlobalTotals.tail(2)

# Create Plots that show Key Metrics For the Covid-19
chartcol='red'
fig = make_subplots(rows=3, cols=2,shared_xaxes=True,
                    specs=[[{}, {}],[{},{}],
                       [{"colspan": 2}, None]],
                    subplot_titles=('Total Confirmed Cases','Active Cases','Deaths','Recoveries','Death to Cases Ratio'))
fig.add_trace(go.Scatter(x=GlobalTotals.index,y=GlobalTotals['Total Confirmed Cases'],
                         mode='lines+markers',
                         name='Confirmed Cases',
                         line=dict(color=chartcol,width=2)),
                         row=1,col=1)
fig.add_trace(go.Scatter(x=GlobalTotals.index,y=GlobalTotals['Active Cases'],
                         mode='lines+markers',
                         name='Active Cases',
                         line=dict(color=chartcol,width=2)),
                         row=1,col=2)
fig.add_trace(go.Scatter(x=GlobalTotals.index,y=GlobalTotals['Total Deaths'],
                         mode='lines+markers',
                         name='Deaths',
                         line=dict(color=chartcol,width=2)),
                         row=2,col=1)
fig.add_trace(go.Scatter(x=GlobalTotals.index,y=GlobalTotals['Total Recoveries'],
                         mode='lines+markers',
                         name='Recoveries',
                         line=dict(color=chartcol,width=2)),
                         row=2,col=2)
fig.add_trace(go.Scatter(x=GlobalTotals.index,y=GlobalTotals['Death to Cases Ratio'],
                         mode='lines+markers',
                         line=dict(color=chartcol,width=2)),
                         row=3,col=1)
fig.update_layout(showlegend=False)


# In[17]:


TotalCasesCountry=CountryConsolidated.max(level=0)['Total Confirmed Cases'].reset_index().set_index('Country/Region')
TotalCasesCountry=TotalCasesCountry.sort_values(by='Total Confirmed Cases',ascending=False)
TotalCasesCountryexclChina=TotalCasesCountry[~TotalCasesCountry.index.isin(['Mainland China','Others'])]
Top10countriesbycasesexclChina=TotalCasesCountryexclChina.head(10)
TotalCasesCountrytop10=TotalCasesCountry.head(10)
fig = go.Figure(go.Bar(x=Top10countriesbycasesexclChina.index, y=Top10countriesbycasesexclChina['Total Confirmed Cases'],
                      text=Top10countriesbycasesexclChina['Total Confirmed Cases'],
            textposition='outside'))
fig.update_layout(title_text='Top 10 Countries by Total Confirmed Cases Excluding China')
fig.update_yaxes(showticklabels=False)

fig.show()


# In[19]:


ItalyFirstCase=CountryConsolidated.loc['Italy']['Total Confirmed Cases'].reset_index().set_index('Date')
IranFirstCase=CountryConsolidated.loc['Iran']['Total Confirmed Cases'].reset_index().set_index('Date')
GermanyFirstCase=CountryConsolidated.loc['Germany']['Total Confirmed Cases'].reset_index().set_index('Date')
SingaporeFirstCase=CountryConsolidated.loc['Singapore']['Total Confirmed Cases'].reset_index().set_index('Date')
IndiaFirstCase=CountryConsolidated.loc['India']['Total Confirmed Cases'].reset_index().set_index('Date')

ItalyGrowth=ItalyFirstCase[ItalyFirstCase.ne(0)].dropna().reset_index()
IranGrowth=IranFirstCase[IranFirstCase.ne(0)].dropna().reset_index()
GermanyGrowth=GermanyFirstCase[GermanyFirstCase.ne(0)].dropna().reset_index()
SingaporeGrowth=SingaporeFirstCase[SingaporeFirstCase.ne(0)].dropna().reset_index()
IndiaGrowth=IndiaFirstCase[IndiaFirstCase.ne(0)].dropna().reset_index()


# In[24]:


fig = make_subplots(rows=2, cols=2,shared_xaxes=True,
                   subplot_titles=('Italy','Iran','India','Germany'))

fig.update_xaxes(title_text="Number of Days since Outbreak", row=2, col=1)

fig.update_xaxes(title_text="Number of Days since Outbreak", row=2, col=2)

fig.add_trace(go.Scatter(x=ItalyGrowth.index,y=ItalyGrowth['Total Confirmed Cases'],
                         mode='lines+markers',
                         name='Active Cases',
                         line=dict(color=chartcol,width=2)),
                          row=1,col=1)
fig.add_trace(go.Scatter(x=IranGrowth.index,y=IranGrowth['Total Confirmed Cases'],
                         mode='lines+markers',
                         name='Active Cases',
                         line=dict(color=chartcol,width=2)),
                          row=1,col=2)
                           
fig.add_trace(go.Scatter(x=IndiaGrowth.index,y=IndiaGrowth['Total Confirmed Cases'],
                         mode='lines+markers',
                         name='Active Cases',
                         line=dict(color=chartcol,width=2)),
                          row=2,col=1)    
                           
fig.add_trace(go.Scatter(x=GermanyGrowth.index,y=GermanyGrowth['Total Confirmed Cases'],
                         mode='lines+markers',
                         name='Active Cases',
                         line=dict(color=chartcol,width=2)),
                          row=2,col=2)  

fig.update_layout(showlegend=False)


# In[25]:


def plotcountry(Country):
    fig = make_subplots(rows=3, cols=2,shared_xaxes=True,
                    specs=[[{}, {}],[{},{}],
                       [{"colspan": 2}, None]],
                    subplot_titles=('Total Confirmed Cases','Active Cases','Deaths','Recoveries','Death to Cases Ratio'))
    fig.add_trace(go.Scatter(x=CountryConsolidated.loc[Country].index,y=CountryConsolidated.loc[Country,'Total Confirmed Cases'],
                         mode='lines+markers',
                         name='Confirmed Cases',
                         line=dict(color=chartcol,width=2)),
                         row=1,col=1)
    fig.add_trace(go.Scatter(x=CountryConsolidated.loc[Country].index,y=CountryConsolidated.loc[Country,'Active Cases'],
                         mode='lines+markers',
                         name='Active Cases',
                         line=dict(color=chartcol,width=2)),
                         row=1,col=2)
    fig.add_trace(go.Scatter(x=CountryConsolidated.loc[Country].index,y=CountryConsolidated.loc[Country,'Total Deaths'],
                         mode='lines+markers',
                         name='Total Deaths',
                         line=dict(color=chartcol,width=2)),
                         row=2,col=1)
    fig.add_trace(go.Scatter(x=CountryConsolidated.loc[Country].index,y=CountryConsolidated.loc[Country,'Total Recoveries'],
                         mode='lines+markers',
                         name='Total Recoveries',
                         line=dict(color=chartcol,width=2)),
                         row=2,col=2)
    fig.add_trace(go.Scatter(x=CountryConsolidated.loc[Country].index,y=CountryConsolidated.loc[Country,'Death to Cases Ratio'],
                         mode='lines+markers',
                         name='Death to Cases Ratio',
                         line=dict(color=chartcol,width=2)),
                         row=3,col=1)
    fig.update_layout(showlegend=False)
    
    return fig
CountriesList=['Germany','Mainland China','US','Italy','France','Pakistan','India','Japan','Singapore']
interact(plotcountry, Country=widgets.Dropdown(options=CountriesList))


# In[ ]:





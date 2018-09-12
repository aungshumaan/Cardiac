
# coding: utf-8

# In[75]:


import pandas as pd
import numpy as np


# In[76]:


# cpa=pd.read_excel('Data/Cardiac Program_Archive.xlsx',sheet_name=['patients'])
cp=pd.read_excel('Data/Cardiac Program_M.xlsx',sheet_name=['patients'])
df=cp['patients']


# In[95]:


import datetime as DT
now = pd.Timestamp(DT.datetime.now())
df['Date_of_Birth'] = pd.to_datetime(df['Date_of_Birth'], format='%m%d%y')
df['Date_of_Birth'] = df['Date_of_Birth'].where(df['Date_of_Birth'] < now, df['Date_of_Birth'] -  np.timedelta64(100, 'Y'))
df['age'] = (now - df['Date_of_Birth']).astype('<m8[Y]')
df[['Date_of_Birth', 'age']]

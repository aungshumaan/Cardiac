
# coding: utf-8

# In[1]:


import pandas as pd
import numpy as np


# In[31]:


df_meds=pd.read_csv('Cardiac Program_Archive - Cardiac_Meds.csv')
df_enroll=pd.read_csv('Cardiac Program_Archive - patient_enrollment_records.csv')


# In[32]:


print('original shape', df_meds.shape)
df_meds=df_meds.loc[df_meds['create_user']!='multitechvisions@gmail.com']#delete rows with this user
print('shape after removing multitechvision rows', df_meds.shape)


# In[33]:


#2 misc rows to be deleted
df_meds=df_meds.loc[df_meds['ACE']!='asdf']#removed test created by multitechvision
df_meds=df_meds.loc[df_meds['ACE']!='5'] #removed test
print('shape after removing misc rows', df_meds.shape)


# In[34]:


def cleaning_func(df, var, impute):
    #lowercase all values
    df[var]=df[var].str.lower()
    
    #fill missing w/impute value
    df[var]=df[var].fillna(impute) 
    
    #set all values that indicate absence of value to zero
    none_values=list(set(df.loc[df[var].str.contains('none', na=False)][var].tolist()))
    allergy_values=list(set(df.loc[df[var].str.contains('allergic', na=False)][var].tolist()))
    zero_values=none_values+allergy_values
    df.loc[df[var].isin(zero_values),var]=0
    df.loc[df[var].isin(['0']), var]=0  
    
    #Variables AICD and Acute_or_chronic
    if var=='aicd':
        df=df.replace({'aicd':{'no':0, 'no aicd or pacemaker':0, '0' : 0,'0.25':0, '25%':0, 'o':0, '9/13/2017' : 0, 'lisinopril':0}})
    if var=='acute_or_chronic':
        df=df.replace({'acute_or_chronic':{'acute':0, 'chronic':1}})
            
    #set all other values to 1
    allowed_vals=[0, impute]
    print(df.loc[~df[var].isin(allowed_vals), var].tolist())
    df.loc[~df[var].isin(allowed_vals), var] = 1
    
    df[var]=df[var].astype(float)
    
    print(df[var].value_counts())
    
    return df 


# In[38]:


#cleaning_func(df_meds,'ACE', 9999)
#cleaning_func(df_meds,'BB', 9999)
#cleaning_func(df_meds,'Diuretics', 9999)
#cleaning_func(df_meds,'Anticoagulant', 9999)
#cleaning_func(df_meds,'Ionotropes', 9999)
#cleaning_func(df_enroll, 'Aicd', 9999)


# In[42]:


df_meds[['ACE','BB','Diuretics','Anticoagulant','Ionotropes']]


# In[ ]:


df_meds.to_csv('clean_cardiac_meds.csv')


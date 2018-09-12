import pandas as pd
import numpy as np
from data_merge import *
from Clean_Fun import *

# NOTE have to use remove_invalid_rows() inside ALex's function,
# before we remove patient name
impute_na=9999
# %% Load dataset

live_path='Data/Cardiac Program_M.xlsx'
archive_path='Data/Cardiac Program_Archive.xlsx'
live_sheet_pkl='pickle_jar/live_sheets.pkl'
archive_sheet_pkl='pickle_jar/archive_sheets.pkl'
datecol_pkl='pickle_jar/datecols.pkl'
df_dict=pairwise_sheet_merge(live_path, archive_path,
    live_sheet_pkl, archive_sheet_pkl, datecol_pkl)
df_dict.keys()
for key in df_dict.keys():
    print(key+":\n")
    print(df_dict[key].columns)


# %%

from enrollId import *
id_periods=generateEnrollId(df_dict['patient_enrollment_records'])

addEnrollId(df_dict['patient weights'], 'patient_weight_date', id_periods)
addEnrollId(df_dict['patient BNP'], 'bnp_date', id_periods)
addEnrollId(df_dict['Cardiac_Meds'], 'cardiac_meds_date', id_periods)
addEnrollId(df_dict['patient labs'], 'labs_date', id_periods)
addEnrollId(df_dict['patient BP'], 'bp_date', id_periods)

# %% test patients, determing Response Value

# NOTE have to remove invalid rows

train_df,test_df=train_test_split_sg(df)
df=train_df.copy() # for now
del test_df

# %% Clean effusion rate

df['ef']=df['ef'].apply(lambda x: clean_EF_rows(x))

# Clean Blood Pressure rows

df['diastolic']=df.apply(lambda row: clean_diastolic_columns(
    row['diastolic'],row['resting_bp'],col_type='di'),axis=1)
df['systolic']=df.apply(lambda row: clean_diastolic_columns(
    row['systolic'],row['resting_bp'],col_type='sys'),axis=1)

# Dummify the diagnoses
uniq_diag=find_unique_diag(df.diagnosis_1)
dummy_df_diag=dummify_diagnoses(df,uniq_diag,diagnosis_col='diagnosis_1')
df.drop('diagnosis_1',axis=1,inplace=True)
df=df.merge(dummy_df_diag,on='patient_link',how="inner")

# Clean Meds and aicd
# acute or chronic

med_aicd_clean(df,'ace', 0)
med_aicd_clean(df,'bb', 0)
med_aicd_clean(df,'diuretics', 0)
med_aicd_clean(df,'anticoagulant', 0)
med_aicd_clean(df,'ionotropes', 0)
med_aicd_clean(df,'aicd', 0)

weight_dur_age_clean(df,dur_na=impute_na,age_na=impute_na,weight_perc_cutoff=0.2)
# weight_dur_age_clean(df,dur_na=-999999,age_na=-99.,weight_perc_cutoff=0.2)
# Fill all other NA values so that we can find them in a missingness matrix
df.fillna(impute_na,inplace=True)

# %%
import matplotlib.pyplot as plt
import seaborn as sns
#%%
plt.subplots(figsize=(20,15))
heat=sns.heatmap(df[df==impute_na].notnull(), cbar=False)
# plt.xticks(rotation=75)
fig=heat.get_figure()
fig.savefig('Figures/missingness.png',transparent=True, dpi=400,bbox_inches='tight' ,format='png')

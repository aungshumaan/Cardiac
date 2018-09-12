from data_merge import *
from Clean_Fun import *
import re
from matplotlib import pyplot as plt
import seaborn as sns
from IPython.display import display
pd.options.display.max_columns = None #show all columns

# %%

file_path='Data/Cardiac Program_M.xlsx'
sheet_pkl='pickle_jar/live_sheets.pkl'
datecol_pkl='pickle_jar/live_datecols.pkl'
df=live_sheet_merge(file_path, sheet_pkl, datecol_pkl)

# %%
file_path='Data/Cardiac Program_Archive.xlsx'
sheet_pkl='pickle_jar/archive_sheets.pkl'
datecol_pkl='pickle_jar/archive_datecols.pkl'
df_archive=archive_sheet_merge(file_path, sheet_pkl, datecol_pkl)

# df.shape
# df.columns

def clean_numerical(df):
    """
    This function adds duration and age columns and naively
    cleans the weight_change_since_admit.
    duration (type int, expressed in days) is difference of discharge_date and
    admission_date if discharge is true, otherwise duration is time since admission_dateself.
    age (type int, expressed in years) is deduced from birth date

    If weight_change_since_admit/ weight < 0.2:
    weight_change_since_admit (float, expressed in pounds) is divided by 10
    otherwise it is unchanged.
    """
    ## duration
    today = pd.to_datetime('today')
    df.loc[df['discharge']==True,'duration'] = (pd.to_datetime(df.loc[df['discharge']==True, \
        'discharge_date']) - pd.to_datetime(df.loc[df['discharge']==True,'enrollment_date']))
    df.loc[df['discharge']==False,'duration'] = (today - \
        pd.to_datetime(df.loc[df['discharge']==False,'enrollment_date']))
    df.duration = df.duration.fillna(-9999999)
    df['duration'] = (df['duration'] / np.timedelta64(1, 'D')).astype(int)

    ##age
    df['age'] = (today - pd.to_datetime(df['date_of_birth'])).apply(lambda x: \
        float(x.days)/365).fillna(-99.).astype(int)
    df.loc[(df.age<1)&(df.age>-99), 'age'] = -99
    ## weight_change_since_admit
    df['weight_change_since_admit'] = np.where(abs(df['weight_change_since_admit']/ \
        df['weight']) < 0.2, df['weight_change_since_admit'], df['weight_change_since_admit']/10)
    df['weight_change_since_admit'] = df['weight_change_since_admit'].fillna(-999)
    return

clean_numerical(df)
list(zip(df.columns,df_archive.columns))

clean_numerical(df_archive)
df.shape
df.duration.sample(5)
df.age.sample(5)
df.weight_change_since_admit.head(10)

def weight_dur_age_clean(df,dur_na=-999999,age_na=-99.,weight_perc_cutoff=0.2):
    """
    This function adds duration and age columns and naively
    cleans the weight_change_since_admit.
    duration (type int, expressed in days) is difference of discharge_date and
    admission_date if discharge is true, otherwise duration is time since admission_dateself.
    age (type int, expressed in years) is deduced from birth date

    If weight_change_since_admit/ weight < 0.2:
    weight_change_since_admit (float, expressed in pounds) is divided by 10
    otherwise it is unchanged.
    Mutating function
    Author: Aungshuman
    """
    ## duration
    today = pd.to_datetime('today')
    df.loc[df['discharge']==True,'duration'] = (pd.to_datetime(df.loc[df['discharge']==True, \
        'discharge_date']) - pd.to_datetime(df.loc[df['discharge']==True,'enrollment_date']))
    df.loc[df['discharge']==False,'duration'] = (today - \
        pd.to_datetime(df.loc[df['discharge']==False,'enrollment_date']))
    df.duration = df.duration.fillna(dur_na)
    try:
        df['duration'] = (df['duration'] / np.timedelta64(1, 'D')).astype(int)
        df.loc[(df['duration']<1)&(df['duration']!=dur_na), 'duration']=dur_na
    except:
        print(df['duration'])
    ##age
    df['age'] = (today - pd.to_datetime(df['date_of_birth'])).apply(lambda x: \
        float(x.days)/365).fillna(age_na).astype(int)
    df.loc[(df.age<1)&(df.age!=age_na), 'age'] = age_na
    ## weight_change_since_admit
    df['weight_change_since_admit'] = np.where(abs(df['weight_change_since_admit']/ \
        df['weight']) < weight_perc_cutoff, df['weight_change_since_admit'], df['weight_change_since_admit']/10)

    #return

weight_dur_age_clean(df)
df.head()

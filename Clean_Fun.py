# Helper Cleaning Functions

import pandas as pd
import numpy as np
import re
import datetime
import xlrd

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

def med_aicd_clean(df, var, impute):
    """ Mutating Function
    Use as: med_aicd_clean(df,'ace', 0) for all medicines
    """
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
    print("Values set to 1.0: \n")
    print(df.loc[~df[var].isin(allowed_vals), var].tolist())
    df.loc[~df[var].isin(allowed_vals), var] = 1

    df[var]=df[var].astype(float)

    print(df[var].value_counts())

    # return df

def remove_cardiac_unrelated(df):
    """ Remove rows that are not cardiac related
    Mutating function
    """
    ind_cardiac=df.loc[df['cardiac_related']==False].index
    if len(ind_cardiac)!=0:
        # print and remove them
        for i in ind_cardiac:
            print("Removing Cardiac Unrelated Row: "+str(i)+"\n")
            try:
                print(df.iloc[i][['patient_link','Enrollment_Date','status','patient_name','cardiac_related']])
            except:
                print(df.iloc[i][['patient_link','cardiac_related']])
            print('-'*50)
        # now remove them
        df.drop(ind_cardiac,axis=0,inplace=True)
    # reset the index before moving on
    df=df.reset_index()
    print('\n \n Dropped '+str(len(ind_cardiac)+len(ind_cardiac))+' rows from the dataset')
    print('New size of dataset: '+str(df.shape))
    # return df

def determine_outcome_train_test(df,outcome_dict={
    'Good':['To Home','No Reason Given','Assissted Living Facility','No Reason Given'], # CAN WE ASSUME THIS??? that In Nursing Facility
    'Bad':['Hospital','Death'],
    'Test':['In Nursing Facility','Skilled Nursing Facility (SNF)',
    'Not approriate for program, removed']}):
    """ Input dataframe and Outcome dictionary
    Adds Train and Outcome columns to dataframe
    Mutating function
    """
    #first do quick imputations to status
    df.status=df.apply(lambda row: impute_from_special_status(
        row['status'],row['special_status']),axis=1)

    outcome={}
    train={}
    for row in range(df.shape[0]):
        if df.iloc[row]['status'] in outcome_dict['Good']:
            outcome[df.iloc[row]['patient_link']]=1
            train[df.iloc[row]['patient_link']]=1
        if df.iloc[row]['status'] in outcome_dict['Bad']:
            outcome[df.iloc[row]['patient_link']]=0
            train[df.iloc[row]['patient_link']]=1
        if df.iloc[row]['status'] in outcome_dict['Test']:
            train[df.iloc[row]['patient_link']]=0
        elif df.iloc[row]['discharge']==True:
            train[df.iloc[row]['patient_link']]=1
        elif df.iloc[row]['discharge']==False:
            train[df.iloc[row]['patient_link']]=0
    df['outcome']=df['patient_link'].map(outcome)
    df['train']=df['patient_link'].map(train)
    print("Successfully added two columns, Train, and Outcome")
    return df

def train_test_split_sg(df):
    """
    returns two datasets, train and test

    if you haven't already run determine_outcome_train_test(df), will call it first
    """
    try:
        lost_df=df.loc[df.train.isnull()][['patient_link','date_of_birth','facilities_link','special_status','enrollment_date','discharge_date','status']]
        print('{} patients dropped due to unknown outcome: \n'.format(lost_df.shape[0]))
        print(lost_df.sample(10))

        train_ind=df.loc[df.train==1].index
        train_df=df.iloc[train_ind].drop('train',axis=1)
        train_df=train_df.reset_index().drop('index',axis=1)
        test_ind=df.loc[df.train==0].index
        test_df=df.iloc[test_ind].drop('train',axis=1).reset_index().drop('index',axis=1)
        return train_df, test_df
    except:
        print("Calculating outcome first with determine_outcome_train_test()\n")
        return train_test_split_sg(determine_outcome_train_test(df))

def ef_deep_clean(x):
    """ helper function to clean_EF_rows
    extracts any digits from string
    recursively calls itself if there are too many digits
    """
    # remove EF from a previous record
    if re.search('previous',x):
        ind,__=re.search('previous',x).span()
        return ef_deep_clean(x[:ind])
    if re.search('(/)',x):
        ind,__=re.search('(/)',x).span()
        return ef_deep_clean(x[:ind-1])
    else: # Creates a list of digits
        tmp_dig=re.findall('\\b\\d+\\b', x)
        if len(tmp_dig)>2:
            print("Couldn't extract EF so set to na_val")
            print(x)
            return clean_EF_rows('pending')
        if len(tmp_dig)==2:
            return (float(tmp_dig[0])+float(tmp_dig[1]))/200.0
        if len(tmp_dig)==1:
            return clean_EF_rows(tmp_dig[0])
        # if there are really no digits, return na_val which corresponds to 'pending'
        if len(tmp_dig)==0:
            return clean_EF_rows('pending')

def clean_EF_rows(x,na_val=0.49,norm_val=0.55,list_strings=['pending','ordered','done','no data','new admission']):
    """ For use with a .apply(lambda) to the EF column
    ie. df['ef'].apply(lambda x: clean_EF_rows(x))
    Does not change NaN values, only messy string/percentages
    """
    #best case scenario: already a decimal or percentage with no sign
    x=str(x).replace('<','')
    x=str(x).replace('>','')
    try:
        if float(x)<1:
            return float(x)
        elif float(x)>10:
            return float(x)/100
    except:
        # For the percentages like 55%:
        x=str(x).replace('%','')
        # for percentage ranges like 50-55%
        try:
            st,en=re.search('-',x).span()
            # take the average
            return (float(x[:st])+float(x[en:]))/200.0
        except:
            if x.lower() in list_strings:
                return na_val
            elif re.search('normal',x.lower()):
                return norm_val
            else: # deep clean extracts digits from string text
                return ef_deep_clean(x)

def clean_diastolic_columns(di_sys,bp,col_type):
    """ Imputes diastolic or systolic from the BP columns
    col_type distinguishes between di or sys
    Use like: df.apply(lambda row: clean_diastolic_columns(row['Diastolic'],row['resting_BP'],col_type='di'),axis=1)
    """
    try:
        if np.isnan(di_sys):
            sys_tmp,di_tmp=re.findall('\\b\\d+\\b', bp)
            if col_type=='di':
                return di_tmp
            elif col_type=='sys':
                return sys_tmp
            else:
                print("Error: please correct input variable col_type to be either 'di' or 'sys'")
        else:
            return di_sys
        print("Imputing {},{} from Blood Pressure Column".format(sys_tmp,di_tmp))
    except:
        pass

def choose_most_recent(df,date_col):
    ''' Choose the most recent lab/test result from list of results
    To Do: make the drop duplicates more robust since misses some patients
    '''
    new_df=pd.DataFrame(columns=df.columns)
    for pat in df.patient_link.unique():
        pat_df=df.loc[df.patient_link==pat]
        rows,col =pat_df.shape
        if rows==1:
            tmp_df=pat_df
        else:
            try:
                tmp_df=pat_df.loc[pat_df[date_col]==max(pat_df[date_col])]
            except:
                continue
        new_df=pd.concat([new_df, tmp_df], axis=0)
    return new_df.drop_duplicates()

def lower_errors(x):
    try:
        return x.lower()
    except:
        return ""

def find_unique_diag(df_diag_column):
    """
    Within text Diagnosis Columns, returns a list of the Unique Diagnoses,
    removing the combinations of diagnoses
    Use as: uniq_diag=find_unique_diag(df.Diagnosis_1)
    and use this output within the dummify diagnoses function
    """
    all_diag=df_diag_column.apply(lambda x: lower_errors(x)).unique()
    all_diag[7].split(' , ')
    unique_diag=[]
    for diag in all_diag:
        if len(diag)==0:
            continue
        else:
            unique_diag.append(diag.split(' , '))
    flat_list = [item for sublist in unique_diag for item in sublist]
    unique_diag=pd.Series(flat_list).unique()
    return unique_diag

def dummify_diagnoses(df,unique_diag,diagnosis_col='diagnosis_1'):
    """
    Takes Diagnoses and dummifies them for patients. If a patient has multiple
    diagnoses, will put a 1 in all relevant Diagnoses.
    The kth column is NA, no diagnosis. Maybe we will impute with the mode?
    Use as: dummy_df_diag=dummify_diagnoses(df,uniq_diag)

    """
    header=unique_diag.tolist().append('patient_link')
    dummy_diag=pd.DataFrame(columns=header)

    for row in range(df.shape[0]):
        pat_diag=lower_errors(df.iloc[row][diagnosis_col]).split(' , ')
        # print(pat_diag)
        dict_dummy_diag=dict(zip(unique_diag,np.zeros(len(unique_diag))))
        # dict_dummy_diag['patient_link']=df.iloc[row]['patient_link']
        #pd.DataFrame(np.zeros(len(unique_diag)).reshape(-1),columns=unique_diag)
        for diag in pat_diag:
            if diag in unique_diag:
                dict_dummy_diag[diag]=1
            else:
                continue
        tmp_dummy_diag=pd.DataFrame(dict_dummy_diag, index=[row])
        tmp_dummy_diag['patient_link']=df.iloc[row]['patient_link']
        dummy_diag = pd.concat([dummy_diag,tmp_dummy_diag], axis=0)

    return dummy_diag

def impute_from_special_status(status_row,special_row):
    """ If status is empy and special status is Death, put Death into status
    use like:  df.apply(lambda row: impute_from_special_status(row['status'],row['special_status']),axis=1)
    """
    try:
        if np.isnan(status_row):
            if special_row=='Death':
                print('Added to status from special status')
                return 'Death'
            else:
                return status_row
    except:
        return status_row

def remove_invalid_rows(df):
    """ Takes the dataframe and removes specific instances where we have found
    invalid rows - when there is a row like: 1 2 3 ....
    or a test patient created by multitechvisions
    Check patient name for TEST, or for John Doe and Sally Test
    Should drop row "create_user", afterwards
    Mutating function
    """
    # find the index of invalid rows
    ind_inv=df.loc[df['patient_link'].apply(lambda x: True if len(str(x))<3 else False)].index
    ind_inv=ind_inv.append(df.loc[df['patient_name'].apply(lambda x: search_for_test(x,'test'))].index)
    ind_inv=ind_inv.append(df.loc[df['patient_name'].apply(lambda x: search_for_test(x,'john doe'))].index)
    if len(ind_inv)!=0:
        # print and remove them
        for i in ind_inv:
            print("removing invalid row: "+str(i)+"\n")
            try:
                print(df.iloc[i][['patient_link','Enrollment_Date','patient_name','create_user']])
            except:
                print(df.iloc[i]['patient_link'])
            print('-'*50)
        # now remove them
        df.drop(ind_inv,axis=0,inplace=True)
    # reset the index before moving on
    df=df.reset_index()

    # Could remove this section since now we caught them with the 'test' search. But just in case
    # find observations from Test
    ind_test=df.loc[df['create_user']=='multitechvisions@gmail.com'].index#[['patient_link','Enrollment_Date','patient_name','create_user']]
    if len(ind_test)!=0:
        df.iloc[ind_test]
        print("removing multitechvisions test rows: \n")
        try:
            print(df.iloc[ind_test][['patient_link','Enrollment_Date','patient_name','create_user']])
        except:
            print(df.iloc[ind_test]['patient_link'])
        print('-'*50)
        df.drop(ind_test,axis=0,inplace=True)
    print('\n \n Dropped '+str(len(ind_inv)+len(ind_test))+' rows from the dataset')
    print('New size of dataset: '+str(df.shape))
    # return df

# maybe there's an errors coerce function
def search_for_test(x,search_word):
    """ Handles errors and search for 'test' in the input variable
    Use as df.loc[df['patient_name'].apply(lambda x: search_for_test(x,'test'))]
    """
    try:
        return re.search(search_word,x.lower())!= None
    except:
        return False

def datetime_fixer(date_list):
    """
    Converts a list (or Pandas Series) to datetime objects

    Keyword Arguments
    -----------------
    date_list -- A list or Pandas Series containing date-like elements
    """
    # Checks if object is a Pandas Series and converts it to a list if true
    if isinstance(date_list, pd.core.series.Series):
        date_list = list(date_list)

    nats_added = 0

    for i in range(len(date_list)):
        # If the date is not a datetime
        if not isinstance(date_list[i], datetime.datetime):
            # If this date is an int
            if isinstance(date_list[i], int):
                if date_list[i] > 1000:
                    # Convert Excel style date to datetime
                    date_list[i] = datetime.datetime(*xlrd.xldate_as_tuple(date_list[i], 0))
                else:
                    date_list[i] = np.datetime64('NaT')
                    nats_added += 1
            # If this date is a string
            elif isinstance(date_list[i], str):
                # Try to convert to datetime using this format
                try:
                    date_list[i] = datetime.strptime(date_list[i], '%m/%d/%Y')
                    # If error, replace with NaT
                except:
                    date_list[i] = np.datetime64('NaT')
                    nats_added += 1
            else:
                date_list[i] = np.datetime64('NaT')
                nats_added += 1

    print('{} NaT added to list'.format(nats_added))
    return date_list

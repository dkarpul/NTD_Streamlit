# %%
import requests
import pandas as pd
import json

def get_data_from_excel(Sname):
    df = pd.read_excel(
        io="Calculations 20220704 lb.xlsx",
        engine="openpyxl",
        sheet_name=Sname
    )
    return df
def get_key_excel(Sname):
    df = pd.read_excel(
        io="Kim API data mapping 20220720 kw.xlsx",
        engine="openpyxl",
        sheet_name=Sname
    )
    return df

def ReadNTData(database_name,filters = ''):
    page_counter = 1
    number_read = 0
    to_read = 1
    df = pd.DataFrame()
    while number_read < to_read:
        print("Page " + str(page_counter) + '.',end = " ")
        request_string = 'https://municipaldata.treasury.gov.za/api/cubes/' + database_name + '/facts?page=' + str(page_counter)
        if len(filters)>0:
            request_string = request_string + filters

        response_API = requests.get(request_string)
        
        if response_API.status_code == 200:
            parse_json = json.loads(response_API.text)
            page_counter += 1
            to_read = parse_json['total_fact_count']
            print("Detected Page: " + str(parse_json['page']) + ", Total facts: " + str(to_read) + ", Facts read " + str(parse_json['page_size']) + '.')
            number_read += parse_json['page_size']
            df = pd.concat([df, pd.DataFrame.from_records(parse_json['data'])])
        else:
            print('Failure to load data from API, page: ' + str(page_counter) + '. status_code: ' + str(response_API.status_code))
            to_read = 0
            
    print('To read:' + str(to_read) + ", Read: " + str(number_read)+ ", shape Dataframe: ", end = '')
    print(df.shape)
    return df




def LoadAllNTD():
    Load_from_api = 1
    df = [None] * 3
    if Load_from_api:
        cubes = ('incexp_v2','cflow_v2','financial_position_v2')
        for x in range(3):
            print(cubes[x])
            df[x] = ReadNTData(cubes[x],filters = '&cut=amount_type.label:"Audited Actual"|financial_year_end.year:2020')
            #if there isn't a headings amount.sum then make amount that headings
            if 'amount.sum' not in df[x].columns:
                df[x]['amount.sum'] = df[x]['amount']
                print('No amount.sum')
            else:
                print('amount.sum')
    return df

def GetKimData():
    df = LoadAllNTD()
    sheets = ("Financial performance","Cash flow","Financial position")
    df_key = [None]*3
    for x in range(3):
        this_sheet = sheets[x]
        df_key[x] = get_key_excel(this_sheet)
        print(this_sheet)
        print(df_key[x].shape)

    #convert all labels to capitalise
    for x in range(3):
        df[x]['item.label.Cap'] = df[x]['item.label'].str.capitalize()
        for y in range(4):
            df_key[x].iloc[:,y] = df_key[x].iloc[:,y].str.capitalize()

    #for each element in key at find the elements that match for the appropriate years, and replace if there is a kim version
    for x in range(3):
        df[x]['include'] = 0
        df[x]['item.label.Cap.new'] = df[x]['item.label.Cap']
        mask_17_18_19 = ((df[x]['financial_year_end.year']==2017) | 
                                                    (df[x]['financial_year_end.year']==2018) |
                                                        (df[x]['financial_year_end.year']==2019))
        mask_20_21 = ((df[x]['financial_year_end.year']==2020) | (df[x]['financial_year_end.year']==2021))
        
        for y in range(df_key[x].shape[0]):
            old_name = df_key[x].iloc[y,0]
            new_name = df_key[x].iloc[y,1]
            if not (pd.isnull(new_name)|pd.isnull(old_name)):
                submask = (df[x]['item.label.Cap']==old_name) & mask_17_18_19
                df[x].loc[submask,['item.label.Cap.new']] = new_name
                df[x].loc[submask,['include']] = 1
                #if sum(submask)<1:
                    #print(sheets[x] + ': Did not find rows matching: ' + old_name + ". 2017-2019")
                

        for y in range(df_key[x].shape[0]):
            old_name = df_key[x].iloc[y,2]
            new_name = df_key[x].iloc[y,3]
            if not (pd.isnull(new_name)|pd.isnull(old_name)):
                submask = (df[x]['item.label.Cap']==old_name) & mask_20_21
                df[x].loc[submask,['item.label.Cap.new']] = new_name
                df[x].loc[submask,['include']] = 1
                if sum(submask)<1:
                    print(sheets[x] + ': Did not find rows matching: ' + old_name + ". 2020-2021")

        print(len( df[x][ df[x]['include']==1]['item.label.Cap.new'].unique()))   

    #remove unwanted rows and Municpalities
    DF_out_year = [None]*3
    #years = [2017, 2018, 2019, 2020, 2021]
    years = [2020]
    write_to_excel = 0
    old_set = list(set(df[0]['demarcation.code'].unique()).intersection(df[1]['demarcation.code'].unique()))
    old_set = list(set(old_set).intersection(df[2]['demarcation.code'].unique()))
    full_set = old_set
    print("full dataset in all three reports: " + str(len(full_set)))

    #establish which municpalities are present for all years within the new labels
    for x in range(3):
            for year in years:
                    mask = (df[x]['financial_year_end.year'] == year) & (df[x]['include']==1)
                    DF_out_year[x] = df[x][mask].groupby(['demarcation.code','item.label.Cap.new'],as_index=False)['amount.sum'].sum()
                    No_municipalities = len(DF_out_year[x]['demarcation.code'].unique())
                    old_set =  list(set(old_set).intersection(DF_out_year[x]['demarcation.code'].unique()))
                    print(sheets[x]+"_"+str(year)+"_"+str(No_municipalities))
                    DF_out_year[x] = pd.pivot(DF_out_year[x], index = 'item.label.Cap.new', columns = 'demarcation.code', values ='amount.sum' )
                    if write_to_excel:
                            with pd.ExcelWriter('output5b.xlsx', mode='a', if_sheet_exists = 'replace') as writer:
                                    DF_out_year[x].to_excel(writer, sheet_name=sheets[x]+"_"+ str(year))     
    print(len(old_set))
    #remove the rows without the correct branch
    for x in range(3):
            df[x]['mun_include'] = 0
            for branch in old_set:
                df[x].loc[df[x]['demarcation.code']== branch,['mun_include']] = 1
            mask =  (df[x]['mun_include']==1) & (df[x]['include']==1)
            print(str(len(df[x].loc[mask,'demarcation.code'])) + " " + str(len(df[x].loc[mask,'demarcation.code'].unique())))

    N = len(full_set)
    old_set = (old_set + N * [''])[:N]
    c = set(old_set).union(set(full_set))  # or c = set(list1) | set(list2)
    d = set(old_set).intersection(set(full_set))  # or d = set(list1) & set(list2)
    excluded = list(c - d)
    excluded = (excluded + N * [''])[:N]
    municipalities = pd.DataFrame(list(zip(full_set, old_set,excluded)), columns=['All', 'Included', 'Excluded'])
    if write_to_excel:
        with pd.ExcelWriter('output5b.xlsx', mode='a', if_sheet_exists = 'replace') as writer:
                                        municipalities.to_excel(writer, 'Municipalities')  
    print(municipalities.shape) 

    #reshape the output to match need
    write_to_excel = 0
    DF_out_gr = [None]*3
    for x in range(3):
        mask =  (df[x]['mun_include']==1) & (df[x]['include']==1)
        DF_out_gr[x] = df[x][mask].groupby(['financial_year_end.year','item.label.Cap.new'],as_index=False)['amount.sum'].sum()
        DF_out_gr[x] = pd.pivot(DF_out_gr[x], index = 'item.label.Cap.new', columns = 'financial_year_end.year', values ='amount.sum' )
        if write_to_excel:
            with pd.ExcelWriter('output5b.xlsx', mode='a', if_sheet_exists = 'replace') as writer:
                DF_out_gr[x].to_excel(writer, sheet_name=sheets[x])
        print(DF_out_gr[x].columns)
        print('Done')
    return DF_out_gr

if __name__ == "__main__":
   df = GetKimData() 
   print(df[0].shape)
   print(df[1].shape)
   print(df[2].shape)

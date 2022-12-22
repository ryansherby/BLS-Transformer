import json

import requests as rq
import pandas as pd
import numpy as np


class API:
    """
    This class provides an interface to the Bureau of Labor Statistics API.

    Attributes:
    series_id (list): A list of series IDs to access data for.
    registration_key (str): A registration key to access data with (optional).
    start_year (str): The start year to access data for (defaults to 2010).
    end_year (str): The end year to access data for (defaults to 2020).
    df_dict (dict): A dictionary containing the data for each seriself.json_response (dict): The raw JSON response from the API.
    """

    def __init__(self,series_id:list,registration_key:str=None,start_year:str='2011',end_year:str='2020',config=None):
        converted=self.convert(config)
        if converted:
            self.config=converted
            with open(self.config) as json_file:
                try:
                    self.series_id=json_file['seriesid']
                except KeyError:
                    raise Exception('You need to entire series ID(s).')
                try:
                    self.registration_key=json_file['registrationkey']
                except KeyError:
                    None
                try:
                    self.start_year=json_file['startyear']
                except KeyError:
                    self.start_year=start_year
                try:
                    self.end_year=json_file['endyear']
                except KeyError:
                    self.end_year=end_year

                self.json_response=None
                self.df_dict={}
                self.series_catalog={}
        else:
            self.series_id=series_id
            self.registration_key=registration_key
            self.start_year=start_year
            self.end_year=end_year
            self.json_response=None
            self.df_dict={}
            self.series_catalog={}

        headers = {'Content-type': 'application/json'}

        if self.registration_key==None:
            url="https://api.bls.gov/publicAPI/v1/timeseries/data/"
        else:
            url="https://api.bls.gov/publicAPI/v2/timeseries/data/"
        
        payload=json.dumps({"seriesid":self.series_id,
                    "startyear":self.start_year,
                    "endyear":self.end_year,
                    "registrationkey":self.registration_key,
                    "catalog":True})

        response=rq.post(url=url,data=payload,headers=headers)        
        
        self.json_response=response.json()

        print("Request Status: "+self.json_response['status'])

        for i, elem in enumerate(self.json_response['message']):
            if i < 4:
                print(f"Response Message: {elem}")
        

    def get_DataFrame(self,index:list[int]=[None],id:list[str]=[None]):
        """
        Retrieve one or more DataFrame objects from the dictionary by its index or ID.
    
        Args:
        index (int): The index of the series in the series list (optional).
        id (str): The series ID of the series (optional).
        
        Returns:
        pd.DataFrame: A DataFrame object containing the data for the given series.
        
        Raises:
        Exception: If the data dictionary has not been initialized (i.e. `self.df_dict` is empty).
        """
        if len(self.df_dict)==0 or self.df_dict==None:
            raise Exception("Please initialize the data dictionary with acceptable raw JSON.")



        df_list=[]
        id_list=[]


        for (keys, v) in self.df_dict.items():
            for i in range(len(keys)):
                if (keys[i] in index) or (keys[i] in id):
                    df_list.append(v)
                    id_list.append(keys[1])
        return pd.concat(df_list,keys=id_list,axis=1)


    


    def get_catalog(self,index:list[int]=[None],id:list[str]=[None]):
        """
        Extract the series catalog (a list of metadata for each series) from the `json_response` dictionary.
        
        Returns:
        List: A list containing json_response dictionaries.
        """

        if len(self.series_catalog)==0 or self.series_catalog==None:
            raise Exception("None of the requested series contained a catalog.")
        



        catalog_list=[]

        for (keys, v) in self.series_catalog.items():
            for i in range(len(keys)):
                if (keys[i] in index) or (keys[i] in id):
                    catalog_list.append(v)
        return catalog_list
       


    def get_data_dictionary(self):
        """
        Create a dictionary of DataFrame objects from the JSON response.
        
        Args:
        None
            
        Returns:
        None
            
        Raises:
        Exception: If the JSON response has not been set (i.e. `self.json_response` is None).
        Exception: If the JSON response does not any series.
        """

        
        if self.json_response==None:
            raise Exception("Please use the get_json() method.")
        
        for i in range(len(self.json_response['Results']['series'])):
            if i is IndexError:
                raise Exception("JSON response contains no series.")


                
            self.set_DataFrame_from_TimeSeries(i)
            self.set_series_catalog_dict(i)
        print('Success! Use get_DataFrame() to access one or more DataFrames by its index or id.')



    
    def set_DataFrame_from_TimeSeries(self,i): #Internal only
        """
        Create a DataFrame object from the raw JSON data for a given series.

        Args:
        i (int): The index of the series in the series list.

        Returns:
        dict: A dictionary containing the DataFrame object indexed by the series index and series ID.
        """
    
        year=[]
        period=[]
        periodName=[]
        value=[]

        for dict in self.json_response['Results']['series'][i]['data']:
            year+=[int(dict['year'])]
            period+=[int(dict['period'][1:])]
            periodName+=[str(dict['periodName'])]
            value+=[float(dict['value'])]
            
        json_list=[year,period,periodName,value]
        
        

        self.df_dict[(i,self.json_response['Results']['series'][i]['seriesID'])]=pd.DataFrame(json_list).transpose()
        self.df_dict[(i,self.json_response['Results']['series'][i]['seriesID'])].columns=['Year','Period','Period Name','Value']
        self.df_dict[(i,self.json_response['Results']['series'][i]['seriesID'])].index=[self.df_dict[(i,self.json_response['Results']['series'][i]['seriesID'])]['Year'].astype(int),
        self.df_dict[(i,self.json_response['Results']['series'][i]['seriesID'])]['Period'].astype(int)]


    def set_series_catalog_dict(self,i): #Internal only
        try:
            self.series_catalog[(i,self.json_response['Results']['series'][i]['seriesID'])]=self.json_response['Results']['series'][i]['catalog']
        except:
            pass



    def convert(self,json_file) -> dict: #Internal only                                                           
        """                                                                            
        Attempt to convert JSON to dict.

        AKA don't pass garbage to the config.                                                        
        """                                                                            
        try:                                                                           
            tup_json = json.loads(json_file)                                                 
            return tup_json                                                            
        except:                                                                                    
            return None
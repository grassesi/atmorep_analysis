import os
import json
from typing import List
from tqdm import tqdm
import zarr
import numpy as np
import xarray as xr
from pathlib import Path
from itertools import product
import warnings

class HandleAtmoRepData:
    """
    Handle outout data of AtmoRep.
    TODO:
    - support fixed location sampling
    """
    known_data_types = ["source", "pred", "target", "ens"]
    
    def __init__(self, model_id: str, results_basedir: str = "/p/scratch/atmo-rep/results/",):
        """
        :param model_id: ID of Atmorep-run to process
        :param results_basedir: top-directory where results are stored
        """
        self.model_id = model_id if model_id.startswith("id") else f"id{model_id}"
        self.results_dir = results_basedir
        self.config_file, self.config = self._get_config()
        
        self.target_type = "fields_prediction" if self.config["BERT_strategy"] in ["forecast", "BERT"] else "fields_targets"
        
        self.input_variables = self._extract_varnames_from_fields("fields")
        self.target_variables = self._extract_varnames_from_fields(self.target_type)
        
        self.input_token_config = self.get_input_token_config()
        self.target_token_config = self.get_target_token_config() 
        
    @property
    def results_dir(self):
        return self._results_dir
    
    @results_dir.setter
    def results_dir(self, results_basedir):
        results_dir = Path(results_basedir) / self.model_id
        config_file =  results_dir / f"model_{self.model_id}.json"
        zarr_files = list(results_dir.glob('*.zarr'))
        
        # basic checks: directory existence, availability of config-file and zarr-files
        if not results_dir.is_dir():
            raise NotADirectoryError(f"Could not find AtmoRep results-directory '{results_dir}'")
        
        if not config_file.exists():
            raise FileNotFoundError(f"Results directory exist, but configuration file '{config_file}' cannot be found.")
            
        if len(zarr_files) == 0:
            raise FileNotFoundError(f"Results directory exist, but no zarr-output files found.")
            
        self._results_dir = results_dir

        
    def _get_config(self) -> tuple[str, dict]:
        """
        Get configuration dictionary of trained AtmoRep-model.
        """
        config_jsf = self.results_dir / f"model_{self.model_id}.json"
        with open(config_jsf) as json_file:
            config = json.load(json_file)
        return config_jsf, config
    
    def _extract_varnames_from_fields(self, field: str) -> List:
        """
        Extract varnames from config keys: 'fields', 'fields_prediction', 'fields_targets.'
        """
        return [var_list[0] for var_list in self.config[field]]
    
    
    def _get_token_config(self, field_type_key) -> dict:
        """
        Generic function to retrieve token configuration.
        :param key: key in config: 'fields', 'target_fields', 'fields_targets'.
        """
        fields = self.config[field_type_key]
        var_names = [var_list[0] for var_list in fields]
        token_config_values = [var_list[1:] for var_list in fields]
        token_config_keys = ["general_config", "vlevel", "num_tokens", "token_shape", "bert_parameters"]
        
        token_config = {var_name: dict() for var_name in var_names}
        
        for var_name, config in product(
            var_names,
            zip(token_config_keys, token_config_values)
        ):
            key, value = config
            token_config[var_name][key] = value
        
        return token_config
    
    def get_input_token_config(self) -> dict:
        """
        Get input token configuration
        """
        return self._get_token_config("fields")
        
    def get_target_token_config(self) -> dict:
        """
        Retrieve token configuration of output/target data.
        Note that the token configuration is the same as the input data as long as target_fields is unset.
        """
        if self.target_type in ["target_fields", "fields_targets"]:
            return self._get_token_config(self.target_type)   
        else:
            return self.input_token_config
    
    
    def read_one_forecast_file(self, fname: str, varname: str, data_type: str):
        """
        Read data from a single output file of AtmoRep and convert to xarray DataArray with underlying coordinate information.
        :param fname: Name of zarr-file that should be read
        :param varname: name of variable in zarr-file to be accessed
        :param data_type: Type of data which should be retrieved (either 'source', 'target', 'ens' or 'pred')
        :return: list of DataArrays where each element provides one sample
        """    
        store = zarr.ZipStore(fname)
        grouped_store = zarr.group(store)
            
        dims = ["ml", "datetime", "lat", "lon"]
        if data_type == "ens":
            nens = self.config["net_tail_num_nets"]
            coords = {"ensemble": range(nens)}
        else:
            coords = {}
            
        print("debug grouped_storeg[varname]:", grouped_store[varname])
        
        da = []
        for ip, patch in tqdm(enumerate(grouped_store[varname])):    
            coords.update(
                {
                    dim: grouped_store[f"{varname}/{patch}/{dim}"] for dim in dims
                }
            )
            
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                da_p = xr.DataArray(
                    grouped_store[f"{varname}/{patch}/data"], coords=coords,                
                    dims = ["ensemble"] + dims if data_type == "ens" else dims,
                    name=f"{varname}_{patch.replace('=', '')}")
            
            da.append(da_p)
        
        # ML: This would trigger loading data into memory rather than lazy data access.
        #da = xr.concat(da, "patch")
        
        return da
    
    def read_one_bert_file(self, fname: str, varname: str, data_type: str, ml: int):
        
        store = zarr.ZipStore(fname)
        grouped_store = zarr.group(store)
        
        dims = ["itoken", "t", "y", "x"]
        dims_map = {"datetime": ("itoken", "t"), "lat": ("itoken", "y"), "lon": ("itoken", "x")}
        if data_type == "ens":
            dims.insert(1, "ensemble") 
            
        da = []
            
        for ip, patch in tqdm(enumerate(grouped_store[os.path.join(varname)])):
            data_coords = {dim: (dim_map, grouped_store[os.path.join(varname, patch, f"ml={ml:d}", dim)]) for dim, dim_map in dims_map.items()}
            data = grouped_store[os.path.join(varname, patch, f"ml={ml:d}", "data")]
            data_sh = data.shape
            _ = [data_coords.update({dim: range(data_sh[i]) for i, dim in enumerate(dims)})]

            da_p = xr.DataArray(grouped_store[os.path.join(varname, patch, f"ml={ml:d}", "data")], 
                                coords=data_coords, dims = dims, name=f"{varname}_ml{ml:d}_{patch.replace('=', '')}")
            da.append(da_p)

        return da
    
    def read_data(self, varname: str, data_type, epoch: int = -1, **kwargs):
        """
        Read data from a single output file of AtmoRep and convert to xarray DataArray with underlying coordinate information.
        :param varname: name of variable for which token info is requested
        :param data_type: Type of data which should be retrieved (either 'source', 'target', 'ens' or 'pred')
        :param epoch: training epoch of requested token information file
        """                  
        assert data_type in self.known_data_types, f"Data type '{data_type}' is unknown. Chosse one of the following: '{', '.join(self.known_data_types)}'"
        
        filelist = self.get_hierarchical_sorted_files(data_type, epoch)
        
        if self.config["BERT_strategy"] == "forecast":
            print("read_one_forecast_file")
            self.read_one_file = self.read_one_forecast_file
            args = {"varname": varname, "data_type": data_type}
        elif self.config["BERT_strategy"] == "BERT":
            print("read_one_bert_file")
            assert isinstance(kwargs.get("ml", None), int), f"Model-level ml must be an integer, but '{kwargs.get('ml', None)}' was parsed."
            self.read_one_file = self.read_one_bert_file
            args = {"varname": varname, "ml": kwargs.get("ml"), "data_type": data_type}
            # source data is still structured
            if data_type == "source":
                self.read_one_file = self.read_one_forecast_file
                args = {"varname": varname, "data_type": data_type}
        else:
            print(f"Handling data with sampling strategy '{self.config['BERT_strategy']}' is not supported yet.")
        
        print(f"Start reading {len(filelist)} files...")
        da = []
        for i, f in enumerate(filelist):
            da += self.read_one_file(f, **args)
            
        # return global data if global forecasting evaluation mode was chosen 
        # ML: preliminary approach: identification via token_overlap-attribute 
        if self.config["BERT_strategy"] == "forecast":
            try:
                self.config["token_overlap"]
                da = self.get_global_field(da)
                print("get_global_field")
            except KeyError:
                pass
               
        return da
    
    @staticmethod
    def get_global_field(da_list):
        
        # get unique time stamps
        times_unique = set([time for da in da_list for time in da["datetime"].values])
        dx, dy = np.abs(da_list[0]["lon"][1] - da_list[0]["lon"][0]), \
                 np.abs(da_list[0]["lat"][1] - da_list[0]["lat"][0])
        
        # initialize empty global data array
        dims = da_list[0].dims
        data_coords = {k: v for k, v in da_list[0].coords.items() if k not in ["lat", "lon"]}
        data_coords["lat"] = np.linspace(-90., 90., num=int(180/dy) + 1, endpoint=True)
        data_coords["lon"] = np.linspace(0, 360, num=int(360/dx), endpoint=False)  
        data_coords["datetime"] = sorted(times_unique)
        
        shape = [len(array) for array in data_coords.values()]

        da_global = xr.DataArray(
            np.empty(tuple(len(d) for d in data_coords.values())), 
            coords=data_coords,
            dims=dims
        )
        # fill global data array 
        for da in da_list:
            da_global.loc[{"datetime": da["datetime"], "lat": da["lat"], "lon": da["lon"]}] = da

        if np.any(da_global.isnull()): 
            raise ValueError(f"Could not get global data field.")
            
        return da_global                      
    
        
    def get_hierarchical_sorted_files(self, data_type: str, epoch: int = -1):
        """
        Get sorted list of file names.
        :param data_type: Type of data which should be retrieved (either 'source', 'target', 'ens' or 'pred')
        :param epoch: number of epoch for which data should be retrieved. Parse -1 for getting all epochs.
        """
        epoch_str = f"epoch*" if epoch == -1 else f"epoch{epoch:05d}"
        
        fpatt = f"results_{self.model_id}_{epoch_str}_{data_type}.zarr"
        filelist = list(Path(self.results_dir).glob(f"**/{fpatt}"))
        
        if len(filelist) == 0:
            raise FileNotFoundError(f"Could not file any files mathcing pattern '{fpatt}' under directory '{self.results_dir}'.")
        
        # hierarchical sorting: epoch -> rank -> batch
        sorted_filelist = sorted(filelist, key=lambda x: self.get_number(x, "_epoch"))
      
        return sorted_filelist
    
    @staticmethod
    def get_number(file_name, split_arg):
        # Extract the number from the file name using the provided split argument
        return int(str(file_name).split(split_arg)[1].split('_')[0])  

    
from pathlib import Path
import argparse

from utils.read_atmorep_data import HandleAtmoRepData


parser = argparse.ArgumentParser(
    prog="Atmorep-analysis produce netcdf",
    description="read zarr output from atmorep inference and construct netcdf file for analysis"
)
parser.add_argument("model_id", "inference run to be used.")

args = parser.parse_args()

data_loader = HandleAtmoRepData(
    model_id=args.model_id,
    results_basedir="/p/scratch/deepacf/grasse1/atmorep-results",
)

input_token_info = data_loader.get_input_token_config()
print(input_token_info)

da = data_loader.read_data("temperature", "pred")
print(da.nbytes)

writepath = Path(f"/p/scratch/deepacf/grasse1/atmorep-data/results_era5_{args.model_id}.nc")

da.to_netcdf(writepath)

print(da["datetime"])

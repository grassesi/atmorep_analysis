from pathlib import Path

from utils.read_atmorep_data import HandleAtmoRepData

grid_spacing = 0.25
model_id = "id9j3w84zs"
data_loader = HandleAtmoRepData(
    model_id=model_id,
    results_basedir="/p/scratch/deepacf/grasse1/atmorep-results",
)

input_token_info = data_loader.get_input_token_config()
print(input_token_info)

da = data_loader.read_data("temperature", "pred")
print(da.nbytes)

writepath = Path(f"/p/scratch/deepacf/grasse1/atmorep-data/results_era5_{model_id}.nc")

da.to_netcdf(writepath)

print(da["datetime"])

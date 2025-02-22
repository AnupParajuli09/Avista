# %% Importing all the required Modules
from Parser.parse import parse_all_data
from Build_Model.Constraints import build_pyomo_model
from Build_Model.Objective import substation_power_minimize,substation_power_minimize_with_discharge_cost,cost_minimize,cost_minimize_with_discharging_cost,pyomo_solve,power_flow
from Build_Model.store import store_results
from Plot.Plotting import *
import pandas as pd
from Distributed.separate_areas import split_data_into_areas
from Distributed.area_informatiion import *
from Distributed.admm import solve_ADMM
from Distributed.enapp import solve_EnAPP

system_name = 'avista_sys' ## System name
area_info = eval(f'{system_name}' + '_area_info') ## Gives Information about the area interconnection
obj = cost_minimize_with_discharging_cost  ## Objective function to be used

wd = os.getcwd()
filepath = os.path.join(wd, "rawData", system_name,"csvs") ## Connects to the path of all csvs corresponding to system name

# Import CSV files
bus_data = pd.read_csv(os.path.join(filepath, "node_data.csv"))
branch_data = pd.read_csv(os.path.join(filepath, "branch_data.csv"))
edo_kw_dis_data = pd.read_csv(os.path.join(filepath, "edo_kw_dis_profiles.csv"))
edo_kw_ch_data = pd.read_csv(os.path.join(filepath, "edo_kw_ch_profiles.csv"))
bat_kw_dis_data = pd.read_csv(os.path.join(filepath, "bat_kw_dis_profiles.csv"))
bat_kw_ch_data = pd.read_csv(os.path.join(filepath, "bat_kw_ch_profiles.csv"))
loadshape_data = pd.read_csv(os.path.join(filepath, "loadshape.csv"))
## using arbitrary price profile for 24 hours
price = [0.1,0.1,0.1,0.1,0.1,0.12,0.15,0.18,0.2,0.2,0.22,0.25,0.25,0.28,0.33,0.3,0.25,0.22,0.15,0.12,0.12,0.1,0.1,0.1]

data = parse_all_data(bus_data, branch_data, edo_kw_dis_data, edo_kw_ch_data, bat_kw_dis_data, bat_kw_ch_data, loadshape_data,price)

# %%
if __name__ == "__main__":
    centralized = True
    ADMM = True
    enapp = True

    if centralized:
        print("Solving centralized problem...")
        centralized_model = build_pyomo_model(data)
        centralized_model = pyomo_solve(centralized_model,obj)
        copfVals = store_results(centralized_model)
        print(f"Centralized Objective Value: {copfVals['objective_value']}")

    if ADMM:
        print("Solving ADMM ...")
        data_area = split_data_into_areas(data, area_info)
        admmVals,admm_obj,admm_aug_obj,admm_conv = solve_ADMM(data, data_area, area_info, obj, rho=5e-5, max_iterations=500)
        print("ADMM ran successfully")


    if enapp:
        print("Solving EnAPP ...")
        data_area = split_data_into_areas(data, area_info)
        enappVals, enapp_obj,enapp_conv = solve_EnAPP(data, data_area, area_info, obj, max_iterations=50)
        print("EnAPP ran successfully")

    print(f"COPF Objective Value:{copfVals['objective_value']}")
    print(f"ADMM Objective Value:{admm_obj}")
    print(f"Enapp Objective Value:{enapp_obj}")


    plot_substation_power(copfVals=copfVals,admmVals=admmVals,enappVals=enappVals)
    plot_battery_charging_discharging_combined(copfVals=copfVals,admmVals=admmVals,enappVals=enappVals)
    plot_edo_charging_discharging_combined(copfVals=copfVals,admmVals=admmVals,enappVals=enappVals)
    plot_active_power_flows(copfVals=copfVals,admmVals=admmVals,enappVals=enappVals)
    plot_battery_soc(copfVals=copfVals,admmVals=admmVals,enappVals=enappVals)

    print("Everything ran successfully")

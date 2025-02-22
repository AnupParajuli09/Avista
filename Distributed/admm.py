
import multiprocessing as mp
from Build_Model.Objective import cost_minimize_with_discharging_cost,cost_minimize,substation_power_minimize_with_discharge_cost,substation_power_minimize,pyomo_solve
from Build_Model.Constraints import build_pyomo_model
from Build_Model.store import store_results
from pyomo.environ import value
from collections import defaultdict,ChainMap
import numpy as np


def process_area(data_areas,area_name,area_info, shared_vars, dual_vars, rho,obj_fcn):
    model = build_pyomo_model(data_areas)

    model = pyomo_solve(
        model,
        augmented_obj_function,
        area_name=area_name,
        area_info=area_info,
        shared_vars=shared_vars,
        dual_vars=dual_vars,
        rho=rho,
        obj_fcn=obj_fcn,
    )
    solutions = store_results(model)

    return area_name, solutions

def augmented_obj_function(model, **kwargs):
    area_name = model.area_name
    area_info = model.area_info
    shared_vars = model.shared_vars
    dual_vars = model.dual_vars
    rho = model.rho
    obj_fcn = model.obj_fcn

    original_obj  = obj_fcn(model)

    f = original_obj

    for tt in model.Tset:
        t = tt-1
        # Handle upstream connections
        for idx, up_area in enumerate(area_info[area_name]['up_area']):
            local_node_id = area_info[area_name]['up_local_node_id'][idx]
            shared_p = shared_vars[f"{area_name}_{up_area}_p"][-1]
            dual_p = dual_vars[f"lambda_{area_name}_{up_area}_p"][-1]

            x_p = model.P_subs[tt]

            f += (
                    dual_p[t] * (x_p - shared_p[t]) +
                    (rho / 2) * ((x_p - shared_p[t]) ** 2))

        # Handle downstream connections
        for idx, down_area in enumerate(area_info[area_name]['down_areas']):
            local_node_id = area_info[area_name]['down_local_node_id'][idx]
            shared_p = shared_vars[f"{area_name}_{down_area}_p"][-1]
            dual_p = dual_vars[f"lambda_{area_name}_{down_area}_p"][-1]

            x_p = sum(model.P[tt, (i, k)] for (i, k) in model.Lset if k == local_node_id)

            f += (
                    dual_p[t] * (x_p - shared_p[t]) +
                    (rho / 2) * ((x_p - shared_p[t]) ** 2 ))
    # Update the objective function with dual and penalty expressions
    augmented_obj = f

    return augmented_obj


def initialize_shared_dual(area_info, data):
    shared_vars = {}
    dual_vars = {}

    # Initialize shared variables and dual variables dynamically
    for area in area_info.keys():
        for idx, conn_area in enumerate(area_info[area]['down_areas']):
            shared_vars[f"{area}_{conn_area}_p"] = [np.zeros((data['T'], 1))]
            dual_vars[f"lambda_{area}_{conn_area}_p"] = [np.zeros((data['T'], 1))]
        for idx, conn_area in enumerate(area_info[area]['up_area']):
            shared_vars[f"{area}_{conn_area}_p"] = [np.zeros((data['T'], 1))]
            dual_vars[f"lambda_{area}_{conn_area}_p"] = [np.zeros((data['T'], 1))]

    return shared_vars, dual_vars

def compute_locals(area_info,area_results):
    p_local = {}

    # Extract local variables
    for area in area_info.keys():
        area_p = area_results[area]['P']
        for idx, conn_area in enumerate(area_info[area]['up_area']):
            local_node_id = area_info[area]['up_local_node_id'][idx]
            p_local[f"{area}_{conn_area}_p"] = np.vstack([area_results[area]['P_subs'][key] for key in area_results[area]['P_subs'].keys()])

        for idx, conn_area in enumerate(area_info[area]['down_areas']):
            local_node_id = area_info[area]['down_local_node_id'][idx]
            p_local[f"{area}_{conn_area}_p"] = np.vstack([area_p[key] for key in area_p.keys() if key[1][1] == local_node_id])

    return p_local

def compute_globals(area_info,p_local):
    p_global = {}

    # Compute global variables as averages
    for area in area_info.keys():
        for idx, conn_area in enumerate(area_info[area]['down_areas']):
            p_global[f"{area}_{conn_area}_p"] = (p_local[f"{area}_{conn_area}_p"] + p_local[f"{conn_area}_{area}_p"]) / 2

        for idx, conn_area in enumerate(area_info[area]['up_area']):
            p_global[f"{area}_{conn_area}_p"] = (p_local[f"{area}_{conn_area}_p"] + p_local[f"{conn_area}_{area}_p"]) / 2

    return p_global

def update_area_values(area_info,data_by_area,p_global):
    for area in area_info.keys():
        for idx, conn_area in enumerate(area_info[area]['down_areas']):
            local_node_id = area_info[area]['down_local_node_id'][idx]
            for t in data_by_area[area]['Tset']:
                data_by_area[area]['p_L'][t,local_node_id] = p_global[f"{conn_area}_{area}_p"][t-1]

    return data_by_area

def update_lagrange(area_info,dual_vars,p_local,p_global,rho):
    lagrange_update = {}
    for area in area_info.keys():
        for idx, conn_area in enumerate(area_info[area]['down_areas']):
            lagrange_update[f"lambda_{area}_{conn_area}_p"] = dual_vars[f"lambda_{area}_{conn_area}_p"][-1] + rho * (p_local[f"{area}_{conn_area}_p"] - p_global[f"{area}_{conn_area}_p"])
        for idx, conn_area in enumerate(area_info[area]['up_area']):
            lagrange_update[f"lambda_{area}_{conn_area}_p"] = dual_vars[f"lambda_{area}_{conn_area}_p"][-1] + rho * (p_local[f"{area}_{conn_area}_p"] - p_global[f"{area}_{conn_area}_p"])
    return lagrange_update

def share_global_dual(area_info,shared_vars,dual_vars,lagrange_update,p_global):
    for area in area_info.keys():
        for idx, conn_area in enumerate(area_info[area]['down_areas']):
            shared_vars[f"{area}_{conn_area}_p"].append(p_global[f"{area}_{conn_area}_p"])
            dual_vars[f"lambda_{area}_{conn_area}_p"].append(lagrange_update[f"lambda_{area}_{conn_area}_p"])
        for idx, conn_area in enumerate(area_info[area]['up_area']):
            shared_vars[f"{area}_{conn_area}_p"].append(p_global[f"{area}_{conn_area}_p"])
            dual_vars[f"lambda_{area}_{conn_area}_p"].append(lagrange_update[f"lambda_{area}_{conn_area}_p"])

    return shared_vars,dual_vars

def arrange_solution_by_areas(area_info,area_results):
    for area in area_info.keys():
        for idx, conn_area in enumerate(area_info[area]['down_areas']):
            local_node_id = area_info[area]['down_local_node_id'][idx]
            global_node_id = area_info[conn_area]['up_global_node_id'][0]
            for key, value in area_results[area].items():
                if key in ['P']:  # For 'pij_values': key is (t, i, k)
                    updated_dict = {}
                    for (t, (i, k)), val in value.items():
                        if k == local_node_id:
                            updated_dict[(t, (i, global_node_id))] = val
                        else:
                            updated_dict[(t, (i, k))] = val
                    area_results[area][key] = updated_dict

    dopf = defaultdict(dict)
    for area_name, vars_dict in area_results.items():
        for key, value in vars_dict.items():
            dopf[key][area_name] = value

    return dopf

def merge_solutions(dopf):
    ## merging the area_wise dopf dictionary into one
    dopfVals = {}
    # Initialize containers for each variable
    dopfVals['P_subs'] = {}
    dopfVals['P'] = {}
    dopfVals['Pe_c'] = {}
    dopfVals['Pe_d'] = {}
    dopfVals['P_c'] = {}
    dopfVals['P_d'] = {}
    dopfVals['B'] = {}

    dopfVals["P_subs"] = {**dopf['P_subs']['area1']}
    dopfVals["P"] = dict(ChainMap(*[dopf['P'][area] for area in dopf['P']]))
    dopfVals["Pe_c"] = dict(ChainMap(*[dopf['Pe_c'][area] for area in dopf['Pe_c']]))
    dopfVals["Pe_d"] = dict(ChainMap(*[dopf['Pe_d'][area] for area in dopf['Pe_d']]))
    dopfVals["P_c"] = dict(ChainMap(*[dopf['P_c'][area] for area in dopf['P_c']]))
    dopfVals["P_d"] = dict(ChainMap(*[dopf['P_d'][area] for area in dopf['P_d']]))
    dopfVals["B"] = dict(ChainMap(*[dopf['B'][area] for area in dopf['B']]))

    return dopfVals


def solve_ADMM(data, data_by_area, area_info, obj_fcn, rho, max_iterations):
    shared_vars, dual_vars = initialize_shared_dual(area_info, data)

    convergence = {}
    objective = {}
    aug_objective = {}
    area_folders = area_info.keys()
    pool = mp.Pool(processes=len(area_folders))

    for i in range(max_iterations):
        results = pool.starmap(process_area,[(data_by_area[area], area, area_info, shared_vars, dual_vars, rho, obj_fcn) for area in area_folders])
        area_results = {area_name: solutions for area_name, solutions in results}

        p_local = compute_locals(area_info, area_results)

        p_global = compute_globals(area_info, p_local)

        data_by_area = update_area_values(area_info,data_by_area,p_global)

        lagrange_update = update_lagrange(area_info, dual_vars, p_local, p_global,rho)

        shared_vars, dual_vars = share_global_dual(area_info, shared_vars, dual_vars, lagrange_update, p_global)

        ## Convergence Check
        max_diff = {}

        for area in area_folders:
            max_diff[area] = []  # Initialize a list to store the max differences for the area

            # Iterate over down_areas
            for conn_area in area_info[area]['down_areas']:
                max_diff[area].append(max(
                    np.max(rho * (np.linalg.norm(shared_vars[f"{area}_{conn_area}_p"][-1] - shared_vars[f"{area}_{conn_area}_p"][-2]) ** 2)),
                    np.max(np.linalg.norm(dual_vars[f"lambda_{area}_{conn_area}_p"][-1] - dual_vars[f"lambda_{area}_{conn_area}_p"][-2]) ** 2)
                ))

            # Iterate over up_area
            for conn_area in area_info[area]['up_area']:
                max_diff[area].append(max(
                    np.max(rho * (np.linalg.norm(shared_vars[f"{area}_{conn_area}_p"][-1] - shared_vars[f"{area}_{conn_area}_p"][-2]) ** 2)),
                    np.max(np.linalg.norm(dual_vars[f"lambda_{area}_{conn_area}_p"][-1] - dual_vars[f"lambda_{area}_{conn_area}_p"][-2]) ** 2)
                ))

        # Print statement for debugging
        tol = np.max([np.max(sublist) for sublist in max_diff.values()])
        convergence[i] = tol

        if obj_fcn == cost_minimize_with_discharging_cost:
            objective[i] = sum(area_results[area]['objective_value'] for area in area_folders) - sum(area_results[area]['P_subs'][t] * data['costshape'][t] for area in ['area2', 'area3', 'area4'] for t in data['Tset'])
        else:
            objective[i] = area_results['area1']['objective_value']
        print(f"iteration = {i}, tolerance={tol}, objective value: {objective[i]}")

        if tol < 1e-5:
            print(f"Converged after {i} iterations")
            print(f"total objective value for DOPF:{objective[i]}")
            break

    pool.close()
    pool.join()

    dopf = arrange_solution_by_areas(area_info, area_results)

    dopfVals = merge_solutions(dopf)

    return dopfVals,objective,aug_objective,convergence

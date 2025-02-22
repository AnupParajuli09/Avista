from pyomo.environ import Objective, minimize, maximize, value, SolverFactory,SolverStatus,TerminationCondition

def substation_power_minimize(model):
    return sum(model.P_subs[t] for t in model.Tset)

def substation_power_minimize_with_discharge_cost(model):
    cost = model.cost
    sub_power = sum(model.P_subs[t] for t in model.Tset)
    bat_dis_cost = sum(model.P_d[t,j] * cost[t] for t in model.Tset for j in model.Bset)
    edo_dis_cost = sum(model.Pe_d[t, j] * cost[t] for t in model.Tset for j in model.Eset)

    return (sub_power + bat_dis_cost + edo_dis_cost)
def power_flow(model, **kwargs):
    return 0

def cost_minimize_with_discharging_cost(model):
    cost = model.cost
    subs_cost = sum(model.P_subs[t] * cost[t] for t in model.Tset)
    bat_dis_cost = sum(model.P_d[t,j] * cost[t] /2 for t in model.Tset for j in model.Bset)
    edo_dis_cost = sum(model.Pe_d[t, j] * cost[t] /3 for t in model.Tset for j in model.Eset)
    scd_term = sum((1 - model.n_c) * model.P_c[t, j] + ((1 / model.n_d) - 1) * model.P_d[t, j] for t in model.Tset for j in model.Bset)
    alpha = 1e-3

    return (subs_cost + alpha * scd_term + bat_dis_cost + edo_dis_cost)

def cost_minimize(model, **kwargs):
    cost = model.cost

    subs_cost = sum(model.P_subs[t] * cost[t] for t in model.Tset)
    scd_term = sum((1-model.n_c)*model.P_c[t,j] + ((1/model.n_d) -1) * model.P_d[t,j] for t in model.Tset for j in model.Bset)
    alpha = 1e-3

    return (subs_cost + alpha * scd_term)

def pyomo_solve(model, obj_func, **kwargs):
    # Store kwargs as attributes on the model
    for key, value in kwargs.items():
        setattr(model, key, value)

    model.obj = Objective(rule=obj_func, sense=minimize)
    # opt = SolverFactory('gurobi')
    opt = SolverFactory('osqp', executable=r"C:\Program Files\SCIPOptSuite 9.2.0\bin\scip.exe")
    results = opt.solve(model, tee=False)
    if results.solver.status == "ok" and results.solver.termination_condition == "optimal":
        print("Solver completed successfully.")
    else:
        print(f"Solver failed: {results.solver.termination_condition}")

    return model
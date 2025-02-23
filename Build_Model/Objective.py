from pyomo.environ import Objective, minimize, maximize, value, SolverFactory,SolverStatus,TerminationCondition

## Objective function to minimize the total substation power for all time periods
def substation_power_minimize(model):
    sub_power = sum(model.P_subs[t] for t in model.Tset) ## Total substation power for all time periods
    scd_term = sum((1 - model.n_c) * model.P_c[t, j] + ((1 / model.n_d) - 1) * model.P_d[t, j] for t in model.Tset for j in model.Bset) ## terms to get rid of simultaneous charging and discharging of battery
    alpha = 1e-3
    return sum(sub_power + alpha * scd_term)

## Objective function to minimize the total substation power for all time periods with associated discharging costs of edo and battery nodes
def substation_power_minimize_with_discharge_cost(model):
    cost = model.cost
    sub_power = sum(model.P_subs[t] for t in model.Tset) ## Total substation power for all time periods
    bat_dis_cost = sum(model.P_d[t,j] * cost[t] /2 for t in model.Tset for j in model.Bset) ## associated discharging costs of battery nodes
    edo_dis_cost = sum(model.Pe_d[t, j] * cost[t] /3 for t in model.Tset for j in model.Eset) ## associated discharging costs of edo nodes
    scd_term = sum((1 - model.n_c) * model.P_c[t, j] + ((1 / model.n_d) - 1) * model.P_d[t, j] for t in model.Tset for j in model.Bset) ## terms to get rid of simultaneous charging and discharging of battery
    alpha = 1e-3

    return (sub_power + alpha * scd_term + bat_dis_cost + edo_dis_cost)

## Zero Objective function (for just solving the circuit without any objective function)
def power_flow(model, **kwargs):
    return 0

## Objective function to minimize the total cost of substation power for all time periods with associated discharging costs of edo and battery nodes
def cost_minimize_with_discharging_cost(model):
    cost = model.cost
    subs_cost = sum(model.P_subs[t] * cost[t] for t in model.Tset) ## Total cost of substation power for all time periods
    bat_dis_cost = sum(model.P_d[t,j] * cost[t] /2 for t in model.Tset for j in model.Bset) ## associated discharging costs of battery nodes
    edo_dis_cost = sum(model.Pe_d[t, j] * cost[t] /3 for t in model.Tset for j in model.Eset) ## associated discharging costs of edo nodes
    scd_term = sum((1 - model.n_c) * model.P_c[t, j] + ((1 / model.n_d) - 1) * model.P_d[t, j] for t in model.Tset for j in model.Bset) ## terms to get rid of simultaneous charging and discharging of battery
    alpha = 1e-3

    return (subs_cost + alpha * scd_term + bat_dis_cost + edo_dis_cost)

## Objective function to minimize the total cost of substation power for all time periods
def cost_minimize(model, **kwargs):
    cost = model.cost

    subs_cost = sum(model.P_subs[t] * cost[t] for t in model.Tset) ## Total cost of substation power
    scd_term = sum((1-model.n_c)*model.P_c[t,j] + ((1/model.n_d) -1) * model.P_d[t,j] for t in model.Tset for j in model.Bset) ## terms to get rid of simultaneous charging and discharging of battery
    alpha = 1e-3

    return (subs_cost + alpha * scd_term)

## Solves the optimization model with the specified solver and logs the Solver status and termination condition
def pyomo_solve(model, obj_func, **kwargs):
    # Store kwargs as attributes on the model
    for key, value in kwargs.items():
        setattr(model, key, value)

    model.obj = Objective(rule=obj_func, sense=minimize) ## Minimizing the objective function
    # opt = SolverFactory('gurobi')
    ## You may need to give the complete path of your solver in executables
    opt = SolverFactory('osqp', executable=r"C:\Program Files\SCIPOptSuite 9.2.0\bin\scip.exe") ## using open-source solver
    results = opt.solve(model, tee=False)
    if results.solver.status == "ok" and results.solver.termination_condition == "optimal":
        print("Solver completed successfully.")
    else:
        print(f"Solver failed: {results.solver.termination_condition}")

    return model
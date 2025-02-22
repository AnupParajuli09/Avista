import math

from pyomo.environ import ConcreteModel, Var, Constraint, Reals, NonNegativeReals, Binary, inequality

def build_pyomo_model(data):
    model = ConcreteModel()

    # Sets
    model.Tset = data['Tset']
    model.Nset = data['Nset']
    model.Lset = data['Lset']
    model.Bset = data['Bset']
    model.Eset = data['Eset']
    model.substationBus = data['substationBus']
    model.n_c = data['n_c']
    model.n_d = data['n_d']

    default = 10e3
    substation_limit = 8000
    model.cost = data['costshape']

    ## Continuous Variables
    model.P_subs = Var(model.Tset, domain=NonNegativeReals)
    model.P = Var(model.Tset, model.Lset, domain=Reals)
    model.Pe_c = Var(model.Tset, model.Eset, domain=NonNegativeReals)
    model.Pe_d = Var(model.Tset, model.Eset, domain=NonNegativeReals)
    model.P_c = Var(model.Tset, model.Bset, domain=NonNegativeReals)
    model.P_d = Var(model.Tset, model.Bset, domain=NonNegativeReals)
    model.B = Var(model.Tset, model.Bset, domain=NonNegativeReals)
    ## Binary Variables
    # model.zeta = Var(model.Tset, model.Bset, domain=Binary)
    # model.slack = Var(model.Tset, domain=NonNegativeReals)

    def substation_power_limit_rule(model,t):
        return model.P_subs[t] <= substation_limit

    model.substation_power_limit_constraint = Constraint(model.Tset, rule=substation_power_limit_rule)

    # def slack_rule(model, t):
    #     return model.slack[t] >= model.P_subs[t] - substation_limit
    #
    # model.slack_constraint = Constraint(model.Tset, rule=slack_rule)

    # Real power balance constraint
    def real_power_balance_rule(model, t, j):
        substationBus = data['substationBus']
        p_L = data['p_L']
        incoming_pij = (0 if j in substationBus else sum(model.P[t, (i, j)] for (i, jj) in model.Lset if jj == j)
)
        outgoing_pij = sum(model.P[t, (j, k)] for (jj, k) in model.Lset if jj == j)
        Pc_t = model.P_c[t, j] if j in model.Bset else 0
        Pd_t = model.P_d[t, j] if j in model.Bset else 0
        Pec_t = model.Pe_c[t, j] if j in model.Eset else 0
        Ped_t = model.Pe_d[t, j] if j in model.Eset else 0
        load = p_L[(t,j)]

        if j in substationBus:
            return model.P_subs[t] - outgoing_pij - load - Pc_t + Pd_t - Pec_t + Ped_t == 0
        else:
            return incoming_pij - outgoing_pij - load - Pc_t + Pd_t - Pec_t + Ped_t == 0

    model.real_power_balance_constraint = Constraint(model.Tset, model.Nset, rule=real_power_balance_rule)

    def edo_charging_power_rule(model, t, j):
        Pmax = data['edo_ch'][t,j]
        return model.Pe_c[t, j] <=  Pmax

    model.edo_charging_power_constraint = Constraint(model.Tset, model.Eset, rule = edo_charging_power_rule)

    def edo_discharging_power_rule(model, t, j):
        Pmax = data['edo_dis'][t, j]
        return model.Pe_d[t, j] <= Pmax

    model.edo_discharging_power_constraint = Constraint(model.Tset, model.Eset, rule=edo_discharging_power_rule)

    def bat_charging_power_rule(model, t, j):
        Pb_rated = data['Pb_R']
        # return model.P_c[t, j] <= (1-model.zeta[t,j]) * Pb_rated
        return model.P_c[t, j] <=  Pb_rated

    model.bat_charging_power_constraint = Constraint(model.Tset, model.Bset, rule = bat_charging_power_rule)

    def bat_discharging_power_rule(model, t, j):
        Pb_rated = data['Pb_R']
        # return model.P_d[t, j] <= model.zeta[t,j] * Pb_rated
        return model.P_d[t, j] <= Pb_rated

    model.bat_discharging_power_constraint = Constraint(model.Tset, model.Bset, rule=bat_discharging_power_rule)

    def bat_soc_bound_rule(model,t,j):
        bmin = data['bmin']
        bmax = data['bmax']
        return inequality(bmin, model.B[t,j], bmax)

    model.bat_soc_bound_constraint = Constraint(model.Tset, model.Bset, rule = bat_soc_bound_rule)

    def battery_soc_evolve_rule(model, t, j):
        b0 = data['b0']
        n_c = data['n_c']
        n_d = data['n_d']
        delta_t = data['delta_t']
        if t == min(data['Tset']):
            # Initial SOC at midpoint between min and max
            return model.B[t, j] == b0 + (n_c * model.P_c[t, j] - (model.P_d[t, j] / n_d)) * delta_t
        else:
            return model.B[t, j] == model.B[t - 1, j] + (n_c * model.P_c[t, j] - (model.P_d[t, j] / n_d)) * delta_t

    model.battery_soc_evolve_constraint = Constraint(model.Tset, model.Bset, rule=battery_soc_evolve_rule)

    # final soc= initial soc rule
    def final_soc_rule(model, t, j):
        b0 = data['b0']
        if t == max(data['Tset']):
            return model.B[t, j] == b0
        else:
            return Constraint.Skip

    model.final_soc_constraint = Constraint(model.Tset, model.Bset, rule=final_soc_rule)


    return model
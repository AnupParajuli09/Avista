import math

from pyomo.environ import ConcreteModel, Var, Constraint, Reals, NonNegativeReals, Binary, inequality

def build_pyomo_model(data):
    model = ConcreteModel()

    # Define sets for different components of the network
    model.Tset = data['Tset']  # Time periods
    model.Nset = data['Nset']  # Network nodes
    model.Lset = data['Lset']  # Power lines
    model.Bset = data['Bset']  # Battery nodes
    model.Eset = data['Eset']  # Edo nodes
    model.substationBus = data['substationBus']  # Substation bus node
    model.n_c = data['n_c']  # Charging efficiency of batteries
    model.n_d = data['n_d']  # Discharging efficiency of batteries

    substation_limit = 8000
    model.cost = data['costshape']

    ## Continuous Variables
    model.P_subs = Var(model.Tset, domain=NonNegativeReals) ## Substation Power flow variables
    model.P = Var(model.Tset, model.Lset, domain=Reals) ## Active Power flow Variables
    model.Pe_c = Var(model.Tset, model.Eset, domain=NonNegativeReals) ## Edo Nodes Charging Power Variables
    model.Pe_d = Var(model.Tset, model.Eset, domain=NonNegativeReals) ## Edo Nodes DisCharging Power Variables
    model.P_c = Var(model.Tset, model.Bset, domain=NonNegativeReals) ## Battery Nodes Charging Power Variables
    model.P_d = Var(model.Tset, model.Bset, domain=NonNegativeReals) ## Battery Nodes DisCharging Power Variables
    model.B = Var(model.Tset, model.Bset, domain=NonNegativeReals) ## Battery Nodes State of Charge (S.O.C) Variables
    ## Binary Variables
    # model.zeta = Var(model.Tset, model.Bset, domain=Binary)

    ## Constraint: Substation power limit
    # Equation: P_subs(t) ≤ 8000, ∀ t ∈ T
    def substation_power_limit_rule(model, t):
        return model.P_subs[t] <= substation_limit

    model.substation_power_limit_constraint = Constraint(model.Tset, rule=substation_power_limit_rule)

    ## Constraint: Real power balance at each node
    # Equation:
    # If j is a substation node:
    #     P_subs(t) - ∑(P_outgoing) - Load - Battery and Edo charging + Battery and Edo discharging = 0
    # Otherwise:
    #     ∑(P_incoming) - ∑(P_outgoing) - Load - Battery and Edo charging + Battery and Edo discharging = 0
    def real_power_balance_rule(model, t, j):
        substationBus = data['substationBus']
        p_L = data['p_L']
        incoming_pij = (0 if j in substationBus else sum(model.P[t, (i, j)] for (i, jj) in model.Lset if jj == j)
)
        outgoing_pij = sum(model.P[t, (j, k)] for (jj, k) in model.Lset if jj == j)
        bat_charge = model.P_c[t, j] if j in model.Bset else 0
        bat_discharge = model.P_d[t, j] if j in model.Bset else 0
        edo_charge = model.Pe_c[t, j] if j in model.Eset else 0
        edo_discharge = model.Pe_d[t, j] if j in model.Eset else 0
        load = p_L[(t,j)]

        if j in substationBus:
            return model.P_subs[t] - outgoing_pij - load - bat_charge + bat_discharge - edo_charge + edo_discharge == 0
        else:
            return incoming_pij - outgoing_pij - load - bat_charge + bat_discharge - edo_charge+ edo_discharge == 0

    model.real_power_balance_constraint = Constraint(model.Tset, model.Nset, rule=real_power_balance_rule)

    ## Constraint: Edo nodes charging power
    # Equation: Pe_c(t, j) ≤ edo_ch_max(t, j), ∀ t ∈ T, j ∈ E
    def edo_charging_power_rule(model, t, j):

        Pmax = data['edo_ch'][t,j]
        return model.Pe_c[t, j] <=  Pmax

    model.edo_charging_power_constraint = Constraint(model.Tset, model.Eset, rule = edo_charging_power_rule)

    ## Constraint: Edo nodes discharging power
    # Equation: Pe_d(t, j) ≤ edo_dis_max(t, j), ∀ t ∈ T, j ∈ E
    def edo_discharging_power_rule(model, t, j):
        Pmax = data['edo_dis'][t, j]
        return model.Pe_d[t, j] <= Pmax

    model.edo_discharging_power_constraint = Constraint(model.Tset, model.Eset, rule=edo_discharging_power_rule)

    ## Constraint: Battery charging power
    # Equation: P_c(t, j) ≤ P_b_rated, ∀ t ∈ T, j ∈ B
    def bat_charging_power_rule(model, t, j):
        Pb_rated = data['Pb_R']
        # return model.P_c[t, j] <= (1-model.zeta[t,j]) * Pb_rated
        return model.P_c[t, j] <=  Pb_rated

    model.bat_charging_power_constraint = Constraint(model.Tset, model.Bset, rule = bat_charging_power_rule)

    ## Constraint: Battery discharging power
    # Equation: P_d(t, j) ≤ P_b_rated, ∀ t ∈ T, j ∈ B
    def bat_discharging_power_rule(model, t, j):
        Pb_rated = data['Pb_R']
        # return model.P_d[t, j] <= model.zeta[t,j] * Pb_rated
        return model.P_d[t, j] <= Pb_rated

    model.bat_discharging_power_constraint = Constraint(model.Tset, model.Bset, rule=bat_discharging_power_rule)

    ## Constraint: Battery SOC bounds
    # Equation: bmin ≤ B(t, j) ≤ bmax, ∀ t ∈ T, j ∈ B
    def bat_soc_bound_rule(model, t, j):
        return inequality(data['bmin'], model.B[t, j], data['bmax'])
    model.bat_soc_bound_constraint = Constraint(model.Tset, model.Bset, rule=bat_soc_bound_rule)

    ## Constraint: Battery SOC evolution
    # Equation: B(t, j) = B(t-1, j) + (n_c * P_c(t, j) - P_d(t, j) / n_d) * Δt, ∀ t ∈ T, j ∈ B
    def battery_soc_evolve_rule(model, t, j):
        b0 = data['b0']
        n_c = data['n_c']
        n_d = data['n_d']
        delta_t = data['delta_t']
        if t == min(data['Tset']):
            return model.B[t, j] == b0 + (n_c * model.P_c[t, j] - (model.P_d[t, j] / n_d)) * delta_t
        else:
            return model.B[t, j] == model.B[t - 1, j] + (n_c * model.P_c[t, j] - (model.P_d[t, j] / n_d)) * delta_t

    model.battery_soc_evolve_constraint = Constraint(model.Tset, model.Bset, rule=battery_soc_evolve_rule)

    ## Constraint: Battery final SOC
    # Equation: B(t_max, j) = B(0, j), ∀ j ∈ B
    def final_soc_rule(model, t, j):
        b0 = data['b0']
        if t == max(data['Tset']):
            return model.B[t, j] == b0
        else:
            return Constraint.Skip

    model.final_soc_constraint = Constraint(model.Tset, model.Bset, rule=final_soc_rule)


    return model
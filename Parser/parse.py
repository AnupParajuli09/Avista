# data_parser.py
"""
This script parses all the csv information to a data dictionary.
"""
import numpy as np

def parse_all_data(bus, branch, edo_kw_dis, edo_kw_ch, bat_kw_dis, bat_kw_ch, loadshape,price):
    bus_set = sorted(set(bus['Nodes']))  ## Set of all nodes in the system
    edo_set = sorted(set(edo_kw_ch.columns[1:].astype(int))) ## Set of all edo nodes in the system
    bat_set = sorted(set(bat_kw_ch.columns[1:].astype(int))) ## Set of all battery nodes in the system
    branch_set = sorted(set(zip(branch['fb'], branch['tb']))) ## Set of all Lines in the system
    substationBus = list(set(branch['fb']) - set(branch['tb'])) ## Substation Bus Indicator
    T = len(loadshape) ## Length of optimization horizon
    Tset = np.arange(1, T + 1) ## Set of time periods in optimization horizon

    ## parsing profiles_data and creating corresponding dictionaries
    loadshape_dict = dict(zip(loadshape['time'], loadshape['M']))
    loadshape = {t: loadshape_dict[t] for t in Tset}
    costshape = {t : price[t-1] for t in Tset} ## indicates price of energy variation over time

    ## parsing bus_data
    bus_lookup = bus.set_index('Nodes')
    p_L = {(t, i): bus_lookup.at[i, "P"] * loadshape[t] for t in Tset for i in bus_set} ## time varying loads of all nodes

    ## parsing edo_data
    edo_ch_lookup = edo_kw_ch.set_index('t')
    edo_ch = {(t, i): edo_ch_lookup.at[t, str(i)] for t in Tset for i in edo_set} ## time varying edo nodes charging power limits
    edo_dis_lookup = edo_kw_dis.set_index('t')
    edo_dis = {(t, i): edo_dis_lookup.at[t, str(i)] for t in Tset for i in edo_set} ## time varying edo nodes discharging power limits

    ## parsing bat_data
    bat_ch_lookup = bat_kw_ch.set_index('t')
    bat_ch = {(t, i): bat_ch_lookup.at[t, str(i)] for t in Tset for i in bat_set} ## ## time varying battery nodes charging power limits. Not used
    bat_dis_lookup = bat_kw_dis.set_index('t')
    bat_dis = {(t, i): bat_dis_lookup.at[t, str(i)] for t in Tset for i in bat_set} ## time varying battery nodes discharging power limits. Not used
    Pb_R = 500 ## Rated capacity of a battery
    bmin = 0.3 * Pb_R * 4 ## mimimum state of charge set to 30% of rated energy(KWh). 4 indicates the battery can charge/discharge continuously with its rated capacity for 4 hours.
    bmax = 0.95 * Pb_R * 4 ## maximum state of charge set to 95% of rated energy(KWh).
    b0 = (bmin+bmax)/2 ## initial state of charge (soc) set to mid-point of minimum and maximum soc.
    n_c = 0.95 ## charging efficiency set to 95%
    n_d = 0.95 ## discharging efficiency set to 95%
    delta_t = 1 ## time interval of 1 hour.

    data = {
        "Nset": bus_set,
        "Lset": branch_set,
        "Eset": edo_set,
        "Bset": bat_set,
        'substationBus': substationBus,
        'T': T,
        'Tset': Tset,
        'p_L': p_L,
        'edo_ch': edo_ch,
        'edo_dis': edo_dis,
        'bat_ch': bat_ch,
        'bat_dis': bat_dis,
        'Pb_R': Pb_R,
        'bmin': bmin,
        'bmax': bmax,
        'b0': b0,
        'n_c': n_c,
        'n_d': n_d,
        'delta_t': delta_t,
        'loadshape': loadshape,
        'costshape': costshape
    }
    return data

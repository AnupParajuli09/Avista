# data_parser.py
import numpy as np

def parse_all_data(bus, branch, edo_kw_dis, edo_kw_ch, bat_kw_dis, bat_kw_ch, loadshape,price):
    bus_set = sorted(set(bus['Nodes']))  # Directly convert column to set
    edo_set = sorted(set(edo_kw_ch.columns[1:].astype(int)))
    bat_set = sorted(set(bat_kw_ch.columns[1:].astype(int)))
    branch_set = sorted(set(zip(branch['fb'], branch['tb'])))
    substationBus = list(set(branch['fb']) - set(branch['tb']))
    T = len(loadshape)
    Tset = np.arange(1, T + 1)

    ## parsing profiles_data
    loadshape_dict = dict(zip(loadshape['time'], loadshape['M']))
    loadshape = {t: loadshape_dict[t] for t in Tset}
    costshape = {t : price[t-1] for t in Tset}

    ## parsing bus_data
    bus_lookup = bus.set_index('Nodes')
    p_L = {(t, i): bus_lookup.at[i, "P"] * loadshape[t] for t in Tset for i in bus_set}

    ## parsing edo_data
    edo_ch_lookup = edo_kw_ch.set_index('t')
    edo_ch = {(t, i): edo_ch_lookup.at[t, str(i)] for t in Tset for i in edo_set}
    edo_dis_lookup = edo_kw_dis.set_index('t')
    edo_dis = {(t, i): edo_dis_lookup.at[t, str(i)] for t in Tset for i in edo_set}

    ## parsing bat_data
    bat_ch_lookup = bat_kw_ch.set_index('t')
    bat_ch = {(t, i): bat_ch_lookup.at[t, str(i)] for t in Tset for i in bat_set}
    bat_dis_lookup = bat_kw_dis.set_index('t')
    bat_dis = {(t, i): bat_dis_lookup.at[t, str(i)] for t in Tset for i in bat_set}
    Pb_R = 500
    bmin = 0.3 * Pb_R * 4
    bmax = 0.95 * Pb_R * 4
    b0 = (bmin+bmax)/2
    n_c = 0.95
    n_d = 0.95
    delta_t = 1

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

## This Script is used to store the optimization variables in a dictionary after solving
from pyomo.environ import *
import numpy as np

def store_results(model):
    modelVals = {}

    # Initialize containers for each variable
    modelVals['P_subs'] = {} ## Initializing dictionary placeholder to store substation power flow for different time periods
    modelVals['P'] = {} ## Initializing dictionary placeholder to stores active power flows for different time periods and different lines
    modelVals['Pe_c'] = {} ## Initializing dictionary placeholder to store edo charging power for different time periods and edo nodes
    modelVals['Pe_d'] = {} ## Initializing dictionary placeholder to store edo discharging power for different time periods and edo nodes
    modelVals['P_c'] = {} ## Initializing dictionary placeholder to store battery charging power for different time periods and battery nodes
    modelVals['P_d'] = {} ## Initializing dictionary placeholder to store battery discharging power for different time periods and battery nodes
    modelVals['B'] = {} ## Initializing dictionary placeholder to store battery state of charge for different time periods and battery nodes

    # Store the optimization results for each variable
    for t in model.Tset:
        modelVals['P_subs'][t] = value(model.P_subs[t])

    for t in model.Tset:
        for (i, j) in model.Lset:
            modelVals['P'][(t, (i, j))] = value(model.P[t, (i, j)])

    for t in model.Tset:
        for j in model.Eset:
            modelVals['Pe_c'][(t, j)] = value(model.Pe_c[t, j])
            modelVals['Pe_d'][(t, j)] = value(model.Pe_d[t, j])

    for t in model.Tset:
        for j in model.Bset:
            modelVals['P_c'][(t, j)] = value(model.P_c[t, j])
            modelVals['P_d'][(t, j)] = value(model.P_d[t, j])
            modelVals['B'][(t, j)] = value(model.B[t, j])

    modelVals['objective_value'] = value(model.obj)

    return modelVals



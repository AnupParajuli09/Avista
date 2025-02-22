
from pyomo.environ import *
import numpy as np

def store_results(model):
    modelVals = {}

    # Initialize containers for each variable
    modelVals['P_subs'] = {}
    modelVals['P'] = {}
    modelVals['Pe_c'] = {}
    modelVals['Pe_d'] = {}
    modelVals['P_c'] = {}
    modelVals['P_d'] = {}
    modelVals['B'] = {}

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



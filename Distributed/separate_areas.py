"""
This script does the spatial decomposition of a system to n-smaller sub systems based on area_information.py script
and creates data dictionaries of  each sub systems to hold all of its own area specific infornmation like Nodes, Lines,
Bset, Eset and so on.
"""

import networkx as nx

###########################
# 1) Build the graph from data
###########################
def build_graph_from_data(full_data):
    """
    Constructs a directed graph from the 'full_data' dictionary and branch_list.
    """
    g = nx.DiGraph()
    # Add nodes
    for bus_id in full_data["Nset"]:
        g.add_node(bus_id)
    # Add edges from branch_list
    for branch in full_data["Lset"]:
        fb = branch[0]
        tb = branch[1]
        g.add_edge(fb, tb)
    return g

###########################
# 2) Remove cross-area edges and insert dummy nodes
###########################
def remove_inter_area_edges(g, area_info):
    for area in area_info.keys():
        for i, fb in enumerate(area_info[area]["down_global_node_id"]):
            down_area = area_info[area]["down_areas"][i]
            tb = area_info[down_area]["up_global_node_id"][0]
            dummy1 = area_info[area]["down_local_node_id"][i]
            dummy2 = area_info[down_area]["up_local_node_id"][0]

            if g.has_edge(fb, tb):
                # Remove the original edge
                g.remove_edge(fb, tb)

                # Add edges with dummy bus
                g.add_edge(fb, dummy1)
                g.add_edge(dummy2, tb)


    return g


###########################
# 3) Build sub-area data
###########################
def build_area_data(full_data, area_name, sg_local):

    # The sub-area's nodes and edges
    Nset_area = sg_local.nodes()
    Lset_area = list(sg_local.edges())

    # Subset Dset and Bset
    Eset_area = [edo_id for edo_id in full_data["Eset"] if edo_id in Nset_area]
    Bset_area = [bat_id for bat_id in full_data["Bset"] if bat_id in Nset_area]

    p_L_area = {
        key: full_data["p_L"][key]
        for key in full_data["p_L"]
        if key[1] in Nset_area
    }
    dummy_nodes = set(Nset_area) - set(full_data['Nset'])
    p_L_area_dummy  ={(t,i): 0 for t in full_data["Tset"] for i in dummy_nodes}
    p_L_area.update(p_L_area_dummy)

    edo_ch_area = {
        key: full_data["edo_ch"][key]
        for key in full_data["edo_ch"]
        if key[1] in Eset_area
    }
    edo_dis_area = {
        key: full_data["edo_dis"][key]
        for key in full_data["edo_dis"]
        if key[1] in Eset_area
    }
    bat_ch_area = {
        key: full_data["bat_ch"][key]
        for key in full_data["bat_ch"]
        if key[1] in Bset_area
    }
    bat_dis_area = {
        key: full_data["bat_dis"][key]
        for key in full_data["bat_dis"]
        if key[1] in Bset_area
    }
    Pb_R = full_data['Pb_R']
    bmin = full_data['bmin']
    bmax = full_data['bmax']
    b0 = full_data['b0']
    n_c = full_data['n_c']
    n_d = full_data['n_d']
    delta_t = full_data['delta_t']

    fb = [branch[0] for branch in Lset_area]
    tb = [branch[1] for branch in Lset_area]
    substation_bus = list(set(fb) - set(tb))

    # Now, create the area-level data dictionary
    data_area = {
        "Nset": Nset_area,
        "Lset": Lset_area,
        "Eset": Eset_area,
        "Bset": Bset_area,
        "substationBus": substation_bus,
        "T": full_data["T"],
        "Tset": full_data["Tset"],
        "p_L": p_L_area,
        "edo_ch": edo_ch_area,
        "edo_dis": edo_dis_area,
        "bat_ch": bat_ch_area,
        "bat_dis": bat_dis_area,
        'Pb_R': Pb_R,
        'bmin': bmin,
        'bmax': bmax,
        'b0': b0,
        'n_c': n_c,
        'n_d': n_d,
        'delta_t': delta_t,
        "loadshape": full_data["loadshape"],
        "costshape": full_data["costshape"],
    }
    return data_area

###########################
# 4) Main function
###########################
def split_data_into_areas(full_data,area_info):
    # ----------------------------
    # Step 1: Build the graph from data
    # ----------------------------
    g = build_graph_from_data(full_data)

    # ----------------------------
    # Step 2: Remove cross-area edges and insert dummy nodes with half impedances
    # ----------------------------
    g= remove_inter_area_edges(g, area_info)

    # ----------------------------
    # Step 3: Identify subgraphs
    # ----------------------------
    subgraphs = [g.subgraph(c).copy() for c in nx.weakly_connected_components(g)]

    # For each area, find the subgraph containing its up_global_node_id[0]
    area_subgraphs = {}
    for area_name, info in area_info.items():
        root_node = info["up_local_node_id"][0]
        sg = next((sg for sg in subgraphs if root_node in sg), None)
        if sg is not None:
            area_subgraphs[area_name] = sg
        else:
            print(f"Warning: No subgraph found containing root node {root_node} for area {area_name}.")

    # ----------------------------
    # Step 4: Build area-level data dictionaries
    # ----------------------------
    data_by_area = {}
    for area_name, sg_local in area_subgraphs.items():
        data_area = build_area_data(full_data, area_name, sg_local)
        data_by_area[area_name] = data_area

    return data_by_area



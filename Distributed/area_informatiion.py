## area separation into 4 areas
avista_sys_area_info = {
    'area1': {
        # Area connection information
        'up_area': [],
        'up_local_node_id': [1],
        'up_global_node_id': [1],
        'down_areas': ['area2', 'area3'],
        'down_local_node_id': ['D12', 'D13'],
        'down_global_node_id': [4, 4]
    },
    'area2': {
        # Area connection information
        'up_area': ['area1'],
        'up_local_node_id':['D21'],
        'up_global_node_id': [9],
        'down_areas': [],
        'down_local_node_id': [],
        'down_global_node_id': []
    },
    'area3': {
        # Area connection information
        'up_area': ['area1'],
        'up_local_node_id':['D31'],
        'up_global_node_id': [5],
        'down_areas': ['area4'],
        'down_local_node_id': ['D34'],
        'down_global_node_id': [6]
    },
    'area4': {
        # Area connection information
        'up_area': ['area3'],
        'up_local_node_id':['D43'],
        'up_global_node_id': [10],
        'down_areas': [],
        'down_local_node_id': [],
        'down_global_node_id': []

    },
}
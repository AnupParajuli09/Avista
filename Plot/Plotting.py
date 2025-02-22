import os
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

###############################################################################
# Helper function to save Plotly figures as PNG
###############################################################################
def save_plot_png(fig, filename):
    """
    Save the Plotly figure (PNG) to the same directory as this script.
    """
    script_dir = os.path.dirname(os.path.abspath(__file__))
    filepath = os.path.join(script_dir, filename)
    # Save the image with higher resolution (increase scale for sharper images)
    # fig.write_image(filepath, width=1200, height=800, scale=3)
    fig.write_image(filepath, width=1200, height=800, scale=2)

###############################################################################
# 1) plot_substation_power
###############################################################################
def plot_substation_power(**modelVals_dict):
    """
    Usage example:
        plot_substation_power(copfVals=copfVals, enappVals=enappVals)

    We expect each keyword to be something like "copfVals", "enappVals", etc.
    Each value is a dictionary with:
        modelVals["P_subs"] : dict { time -> value }

    Example:
        modelVals["P_subs"] = {
            0: 5000,
            1: 6500,
            2: 8100,
            ...
        }
    """
    # Gather data for all scenarios
    data = []
    for scenario_key, scenario_data in modelVals_dict.items():
        # Convert "copfVals" -> "copf", "enappVals" -> "enapp"
        scenario_label = scenario_key.replace("Vals", "")

        for time, val in scenario_data["P_subs"].items():
            data.append({
                "time": time,
                "scenario": scenario_label,
                "value": val
            })

    # Decide whether there's only one scenario or multiple
    if len(modelVals_dict) == 1:
        fig = px.bar(
            data, x="time", y="value",
            title="Substation Power"
        )
    else:
        fig = px.bar(
            data, x="time", y="value",
            color="scenario",
            barmode="group",
            title="Substation Power (All Scenarios)"
        )

    # Example horizontal line at 8000
    fig.add_hline(y=8000, line_color='red')

    fig.update_layout(
        xaxis_title="Time",
        yaxis_title="Power (KW)",
        bargap=0.2
    )

    # Save as PNG
    save_plot_png(fig, "P_subs.png")
    fig.show()

###############################################################################
# 2) plot_active_power_flows
###############################################################################
def plot_active_power_flows(**modelVals_dict):
    """
    Usage:
        plot_active_power_flows(copfVals=copfVals, enappVals=enappVals)

    We expect each keyword to be something like "copfVals", "enappVals", etc.
    Each value is a dictionary with:
        modelVals["P"] : dict { (time, (fb, tb)) -> value }
    """
    data = []
    for scenario_key, scenario_data in modelVals_dict.items():
        scenario_label = scenario_key.replace("Vals", "")
        for (time, (fb, tb)), val in scenario_data["P"].items():
            data.append({
                "time": time,
                "branch": f"{fb}->{tb}",
                "scenario": scenario_label,
                "value": val
            })

    if len(modelVals_dict) == 1:
        fig = px.bar(
            data, x="time", y="value",
            color="branch",
            title="Active Power Flows"
        )
    else:
        # Multiple scenarios: group or pattern_shape
        fig = px.bar(
            data, x="time", y="value",
            color="branch",
            pattern_shape="scenario",
            barmode="group",
            title="Active Power Flows (All Scenarios)"
        )

    fig.update_layout(
        xaxis_title="Time",
        yaxis_title="Active Power (KW)",
        legend_title="Branch"
    )

    save_plot_png(fig, "active_power_flows.png")
    fig.show()

###############################################################################
# 3) plot_edo_charging_discharging_combined
###############################################################################
def plot_edo_charging_discharging_combined(**modelVals_dict):
    """
    Usage:
        plot_edo_charging_discharging_combined(copfVals=copfVals, enappVals=enappVals)

    We expect each keyword to be something like "copfVals", "enappVals", etc.
    Each value is a dictionary with:
        modelVals["Pe_c"] : { (time, node) -> charging_power }
        modelVals["Pe_d"] : { (time, node) -> discharging_power }

    We'll store charging as negative, discharging as positive.
    """
    data = []
    for scenario_key, scenario_data in modelVals_dict.items():
        scenario_label = scenario_key.replace("Vals", "")

        # Charging data (negative)
        for (time, node), val in scenario_data["Pe_c"].items():
            data.append({
                "time": time,
                "node": str(node),
                "scenario": scenario_label,
                "value": -val,
                "type": "Charging"
            })
        # Discharging data (positive)
        for (time, node), val in scenario_data["Pe_d"].items():
            data.append({
                "time": time,
                "node": str(node),
                "scenario": scenario_label,
                "value": val,
                "type": "Discharging"
            })

    # We'll create a bar chart. Negative bars extend below the axis.
    if len(modelVals_dict) == 1:
        fig = px.bar(
            data, x="time", y="value",
            color="node",
            title="EDO Charging & Discharging",
            barmode="group"
        )
    else:
        fig = px.bar(
            data, x="time", y="value",
            color="node",
            pattern_shape="scenario",
            barmode="group",
            title="EDO Charging & Discharging (All Scenarios)"
        )

    fig.update_layout(
        xaxis_title="Time",
        yaxis_title="Power (KW)"
    )

    save_plot_png(fig, "EDO_Charging_Discharging.png")
    fig.show()

###############################################################################
# 4) plot_battery_charging_discharging_combined
###############################################################################
def plot_battery_charging_discharging_combined(**modelVals_dict):
    """
    Usage:
        plot_battery_charging_discharging_combined(copfVals=copfVals, enappVals=enappVals)

    We expect each keyword to be something like "copfVals", "enappVals", etc.
    Each value is a dictionary with:
        modelVals["P_c"]: { (time, node) -> charging_power }
        modelVals["P_d"]: { (time, node) -> discharging_power }

    We'll store charging as negative, discharging as positive.
    """
    data = []
    for scenario_key, scenario_data in modelVals_dict.items():
        scenario_label = scenario_key.replace("Vals", "")

        # Charging data (negative)
        for (time, node), val in scenario_data["P_c"].items():
            data.append({
                "time": time,
                "node": str(node),
                "scenario": scenario_label,
                "value": -val,
                "type": "Charging"
            })
        # Discharging data (positive)
        for (time, node), val in scenario_data["P_d"].items():
            data.append({
                "time": time,
                "node": str(node),
                "scenario": scenario_label,
                "value": val,
                "type": "Discharging"
            })

    if len(modelVals_dict) == 1:
        fig = px.bar(
            data, x="time", y="value",
            color="node",
            title="Battery Charging & Discharging",
            barmode="group"
        )
    else:
        fig = px.bar(
            data, x="time", y="value",
            color="scenario",
            pattern_shape="node",
            barmode="group",
            title="Battery Charging & Discharging (All Scenarios)"
        )

    fig.update_layout(
        xaxis_title="Time",
        yaxis_title="Power (KW)"
    )

    save_plot_png(fig, "Battery_Charging_Discharging.png")
    fig.show()

###############################################################################
# 5) plot_battery_soc
###############################################################################
def plot_battery_soc(**modelVals_dict):
    """
    Usage:
        plot_battery_soc(copfVals=copfVals, enappVals=enappVals)

    We expect each keyword to be something like "copfVals", "enappVals", etc.
    Each value is a dictionary with:
        modelVals["B"] : { (time, node) -> SOC_value }

    For example, original code references lines at 1500*0.95 and 1500*0.3,
    so we add horizontal lines at those values.
    """
    data = []
    for scenario_key, scenario_data in modelVals_dict.items():
        scenario_label = scenario_key.replace("Vals", "")

        for (time, node), val in scenario_data["B"].items():
            data.append({
                "time": time,
                "node": str(node),
                "scenario": scenario_label,
                "value": val
            })

    # Single or multiple scenario approach
    if len(modelVals_dict) == 1:
        fig = px.bar(
            data, x="time", y="value",
            color="node",
            title="Battery S.O.C",
            barmode="group"
        )
    else:
        fig = px.bar(
            data, x="time", y="value",
            color="scenario",
            pattern_shape="scenario",
            barmode="group",
            title="Battery S.O.C (All Scenarios)"
        )

    fig.update_layout(
        xaxis_title="Time",
        yaxis_title="Energy (KWh)"
    )

    # Add horizontal lines at 1500*0.95 and 1500*0.3 (example from original code)
    fig.add_hline(y=500 * 4 * 0.95, line_color='red')
    fig.add_hline(y=500 * 4 * 0.3, line_color='red')

    save_plot_png(fig, "battery_soc.png")
    fig.show()

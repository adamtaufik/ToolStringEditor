# calculations.py
import math
import numpy as np


def calculate_effective_weight(params, depth, use_metric=False):
    tool_weight = params['tool_weight']
    wire_weight = params['wire_weight']
    fluid_density = params['fluid_density']
    fluid_level = params['fluid_level']
    tool_avg_diameter = params['tool_avg_diameter']
    tool_length = params['tool_length']
    wire_diameter = params['wire_diameter']

    if use_metric:
        fluid_level *= 3.28084
    else:
        depth *= 3.28084

    # if depth == 0:
    #     print('metric:',use_metric,'\nf_level:',fluid_level)
    #     print('metric:',use_metric,'\ndepth:',depth)
    wire_in_hole = depth
    total_weight = tool_weight + wire_weight * wire_in_hole

    if depth >= fluid_level:
        tool_area = math.pi * (tool_avg_diameter / 12 / 2) ** 2
        tool_displacement = tool_area * tool_length
        tool_displacement_gal = tool_displacement * 7.48052

        submerged_length = max(depth - fluid_level, 0)
        A_wire = math.pi * (wire_diameter / 12 / 2) ** 2
        wire_displacement_gal = submerged_length * A_wire * 7.48052

        buoyancy_reduction = -(tool_displacement_gal+wire_displacement_gal) * fluid_density
        submerged_weight = total_weight + buoyancy_reduction
    else:
        buoyancy_reduction = 0
        submerged_weight = total_weight

    return submerged_weight, buoyancy_reduction

def calculate_fluid_drag(params, speed):
    fluid_density = params['fluid_density']
    tool_avg_diameter = params['tool_avg_diameter']

    v = speed / 60  # ft/s
    tool_diameter_ft = tool_avg_diameter / 12
    projected_area = math.pi * (tool_diameter_ft / 2) ** 2
    fluid_density_slug = fluid_density * 0.0160185
    fluid_density_ppcf = fluid_density * 0.13368
    mu = 0.00002093

    Re = fluid_density_slug * v * tool_diameter_ft / mu

    Cd = 0.82
    drag_force = 0.5 * Cd * fluid_density_ppcf * projected_area * v ** 2
    flow = "Turbulent"  # Added flow regime designation

    return drag_force, Re, flow

def calculate_wire_friction(trajectory_data, params, current_depth, use_metric=False):
    mds = [float(md) for md in trajectory_data['mds']]
    inclinations = [float(inc) for inc in trajectory_data['inclinations']]
    friction_coeff = params['friction_coeff']
    wire_weight = params['wire_weight']
    fluid_density = params['fluid_density']
    fluid_level = params['fluid_level']

    if use_metric:
        wire_weight *= 3.28084
        fluid_level *= 3.28084

    buoyancy_factor = 1 - (fluid_density / 65.4)
    wire_friction = []

    for i in range(len(mds) - 2, -1, -1):
        delta_L = mds[i + 1] - mds[i]
        theta_avg = math.radians((inclinations[i + 1] + inclinations[i]) / 2)
        avg_depth = (mds[i + 1] + mds[i]) / 2

        if avg_depth >= fluid_level:
            wire_submerged = wire_weight * delta_L * buoyancy_factor
        else:
            wire_submerged = wire_weight * delta_L

        normal_force = wire_submerged * math.sin(theta_avg)
        friction = friction_coeff * normal_force
        wire_friction.append(friction)

    wire_friction = wire_friction[::-1]
    idx = np.argmin(np.abs(np.array(mds) - current_depth))
    cumulative_friction = sum(wire_friction[:idx])

    return cumulative_friction, wire_friction

def calculate_tension(params, trajectory_data, current_depth, operation, cumulative_friction, drag_force, use_metric):
    stuffing_box = params['stuffing_box']
    pressure = params['pressure']
    wire_diameter = params['wire_diameter']

    idx = np.argmin(np.abs(np.array(trajectory_data['mds']) - current_depth))
    inclination = float(trajectory_data['inclinations'][idx])

    submerged_weight, buoyancy_reduction = calculate_effective_weight(params, current_depth, use_metric)
    inclination_rad = math.radians(inclination)
    effective_weight = submerged_weight * math.cos(inclination_rad)

    area = math.pi * (wire_diameter / 2) ** 2
    pressure_force = -pressure * area  # Correct sign to negative

    normal_force = submerged_weight * math.sin(inclination_rad)
    friction_magnitude = params['friction_coeff'] * normal_force

    effective_friction = friction_magnitude + stuffing_box + cumulative_friction

    if operation == "RIH":
        tension = max(effective_weight + pressure_force - effective_friction - abs(drag_force), 0)
    else:
        tension = max(effective_weight + pressure_force + effective_friction + abs(drag_force), 0)

    return tension, effective_friction, pressure_force, buoyancy_reduction


def calculate_dls(trajectory_data, use_metric=False):
    mds = [float(md) for md in trajectory_data['mds']]
    inclinations = [float(inc) for inc in trajectory_data['inclinations']]
    dls_values = []

    for i in range(len(mds)):
        if i == 0:
            dls = 0.0
        else:
            delta_md = mds[i] - mds[i - 1]
            delta_inc = inclinations[i] - inclinations[i - 1]
            if delta_md == 0:
                dls = 0.0
            else:
                if use_metric:
                    dls = abs(delta_inc) / (delta_md / 30.48)  # °/30m
                else:
                    dls = (abs(delta_inc) / delta_md) * 100  # °/100ft
        dls_values.append(dls)

    return dls_values


def calculate_tvd(mds, incl_data):
    """Calculate TVD from MD and Inclination data"""
    if len(mds) != len(incl_data):
        raise ValueError("MD and Inclination data must be the same length")

    tvd = [mds[0] * np.cos(np.radians(incl_data[0]))]  # Initial TVD

    for i in range(1, len(mds)):
        delta_md = mds[i] - mds[i - 1]
        avg_incl = np.radians(incl_data[i - 1])  # Use previous inclination
        delta_tvd = delta_md * np.cos(avg_incl)
        tvd.append(tvd[i - 1] + delta_tvd)
    return tvd

def calculate_inclinations(mds, tvds):
    """Calculate inclinations from MD and TVD data"""
    incl = [0.0]
    for i in range(1, len(mds)):
        delta_md = mds[i] - mds[i-1]
        delta_tvd = tvds[i] - tvds[i-1]
        if delta_md == 0:
            incl.append(0.0)
        else:
            ratio = delta_tvd / delta_md
            clamped = max(min(ratio, 1), -1)  # Clamp between -1 and 1
            angle = np.degrees(np.arccos(clamped))
            incl.append(angle)
    return incl

def calculate_north_east(mds, inclinations, azimuths):
    incl = np.radians(inclinations)
    azim = np.radians(azimuths)
    north = [0.0]
    east = [0.0]
    for i in range(1, len(mds)):
        delta_md = mds[i] - mds[i-1]
        north.append(north[i-1] + np.sin(incl[i]) * np.cos(azim[i]) * delta_md)
        east.append(east[i-1] + np.sin(incl[i]) * np.sin(azim[i]) * delta_md)
    return north, east

def plot_trajectory(trajectory_data, current_depth, use_metric, canvas):
    try:
        if not trajectory_data:
            return None

        fig = canvas.figure
        fig.clear()
        ax = fig.add_subplot(111, projection='3d')

        mds = trajectory_data['mds']
        tvd = np.array(trajectory_data['tvd'])
        north = np.array(trajectory_data['north'])
        east = np.array(trajectory_data['east'])

        if use_metric:
            unit_label = 'm'
            # current_depth_display = current_depth
        else:
            unit_label = 'ft'
        current_depth_display = current_depth

        ax.plot(north, east, tvd, color='navy', linewidth=4, linestyle='-', label='Well Path')

        if len(north) > 1:
            points = np.vstack([north, east, tvd]).T
            tangents = np.zeros_like(points)
            tangents[1:-1] = points[2:] - points[:-2]
            tangents[0] = points[1] - points[0]
            tangents[-1] = points[-1] - points[-2]
            tangents /= np.linalg.norm(tangents, axis=1, keepdims=True) + 1e-8

            normals = np.zeros_like(tangents)
            binormals = np.zeros_like(tangents)
            tube_radius = 0.15 if use_metric else 0.5
            tube_radius *= 150

            for i in range(len(tangents)):
                tangent = tangents[i]
                up = np.array([0, 0, 1])
                normal = np.cross(tangent, up)
                if np.linalg.norm(normal) < 1e-6:
                    up = np.array([1, 0, 0])
                    normal = np.cross(tangent, up)
                normal /= np.linalg.norm(normal) + 1e-8
                binormal = np.cross(tangent, normal)
                binormal /= np.linalg.norm(binormal) + 1e-8
                normals[i] = normal
                binormals[i] = binormal

            theta = np.linspace(0, 2 * np.pi, 20)
            X = np.zeros((len(theta), len(points)))
            Y = np.zeros((len(theta), len(points)))
            Z = np.zeros((len(theta), len(points)))

            for i in range(len(points)):
                x = points[i, 0] + tube_radius * (normals[i, 0] * np.cos(theta) + binormals[i, 0] * np.sin(theta))
                y = points[i, 1] + tube_radius * (normals[i, 1] * np.cos(theta) + binormals[i, 1] * np.sin(theta))
                z = points[i, 2] + tube_radius * (normals[i, 2] * np.cos(theta) + binormals[i, 2] * np.sin(theta))
                X[:, i] = x
                Y[:, i] = y
                Z[:, i] = z

            ax.plot_surface(X, Y, Z, color='lightgray', alpha=0.5, linewidth=0)

        if current_depth is not None:
            idx = np.argmin(np.abs(np.array(mds) - current_depth_display))
            ax.plot([north[idx]], [east[idx]], [tvd[idx]], 'ro', markersize=10, label='Tool Position')

        north_min, north_max = np.min(north), np.max(north)
        east_min, east_max = np.min(east), np.max(east)
        tvd_min, tvd_max = np.min(tvd), np.max(tvd)
        max_range = max(north_max - north_min, east_max - east_min, tvd_max - tvd_min)
        north_center = (north_max + north_min) * 0.5
        east_center = (east_max + east_min) * 0.5
        tvd_center = (tvd_max + tvd_min) * 0.5

        ax.set_xlim(north_center - max_range/2, north_center + max_range/2)
        ax.set_ylim(east_center - max_range/2, east_center + max_range/2)
        ax.set_zlim(tvd_center + max_range/2, tvd_center - max_range/2)
        ax.set_xlabel(f'North ({unit_label})')
        ax.set_ylabel(f'East ({unit_label})')
        ax.set_zlabel(f'TVD ({unit_label})')
        ax.set_title("Well Trajectory Overview")
        ax.legend()

        canvas.draw()
        return ax
    except Exception as e:
        print('Plot trajectory error:', e)
        return None

def plot_lubricator(operation, speed, current_depth, params, canvas):
    fig = canvas.figure
    fig.clear()
    ax = fig.add_subplot(111)

    wellhead_width = 30
    wellhead_height = 20
    christmas_tree_height = 25
    lubricator_height = 240
    lubricator_width = 25
    pce_height = 40
    pce_width = 30
    drum_radius = 20
    rsu_width = 50
    rsu_height = 60
    pp_width = 100
    pp_height = 60
    sheave_radius = 15

    wellhead_x = 100
    wellhead_bottom = 20
    christmas_tree_bottom = wellhead_bottom + wellhead_height
    pce_bottom = christmas_tree_bottom + christmas_tree_height
    lubricator_bottom = pce_bottom + pce_height

    wellhead = plt.Rectangle((wellhead_x, wellhead_bottom), wellhead_width, wellhead_height,
                             linewidth=2, edgecolor='black', facecolor='#555555')
    ax.add_patch(wellhead)

    christmas_tree = plt.Rectangle((wellhead_x + (wellhead_width - 20)/2, christmas_tree_bottom),
                                   20, christmas_tree_height, linewidth=2, edgecolor='darkgreen', facecolor='#006400')
    ax.add_patch(christmas_tree)

    pce = plt.Rectangle((wellhead_x + (wellhead_width - pce_width)/2, pce_bottom),
                        pce_width, pce_height, linewidth=2, edgecolor='black', facecolor='#777777')
    ax.add_patch(pce)

    lubricator = plt.Rectangle((wellhead_x + (wellhead_width - lubricator_width)/2, lubricator_bottom),
                               lubricator_width, lubricator_height, linewidth=2, edgecolor='black', facecolor='#999999')
    ax.add_patch(lubricator)

    rsu_x = wellhead_x - 320
    rsu_y = wellhead_bottom + 40
    rsu = plt.Rectangle((rsu_x, rsu_y), rsu_width, rsu_height,
                        linewidth=2, edgecolor='black', facecolor='#aaaaaa')
    ax.add_patch(rsu)

    pp_x = rsu_x - 150
    pp_y = wellhead_bottom + 40
    pp = plt.Rectangle((pp_x, pp_y), pp_width, pp_height,
                       linewidth=2, edgecolor='black', facecolor='#aaaaaa')
    ax.add_patch(pp)

    drum_center_x = rsu_x + rsu_width - drum_radius - 5
    drum_center_y = rsu_y + rsu_height / 2

    rotation_angle = 0
    if current_depth is not None:
        rotation_angle = (current_depth * 50) % 360
        if operation == "POOH":
            rotation_angle *= -1

    drum = plt.Circle((drum_center_x, drum_center_y), drum_radius,
                      linewidth=2, edgecolor='black', facecolor='#cccccc')
    ax.add_patch(drum)

    for i in range(4):
        angle = np.radians(rotation_angle + i * 90)
        end_x = drum_center_x + drum_radius * np.cos(angle)
        end_y = drum_center_y + drum_radius * np.sin(angle)
        ax.plot([drum_center_x, end_x], [drum_center_y, end_y], 'k-', linewidth=2)

    wire_start_angle = np.radians(90)
    wire_start_x = drum_center_x + drum_radius * np.cos(wire_start_angle)
    wire_start_y = drum_center_y + drum_radius * np.sin(wire_start_angle)

    turn_sheave_x = wellhead_x - 30
    turn_sheave_y = wire_start_y - 15
    turn_sheave = plt.Circle((turn_sheave_x, turn_sheave_y), sheave_radius,
                             linewidth=1, edgecolor='black', facecolor='#dddddd')
    ax.add_patch(turn_sheave)

    top_sheave_x = wellhead_x
    top_sheave_y = lubricator_bottom + lubricator_height
    top_sheave = plt.Circle((top_sheave_x, top_sheave_y), sheave_radius,
                            linewidth=1, edgecolor='black', facecolor='#dddddd')
    ax.add_patch(top_sheave)

    ax.plot([pp_x + pp_width, rsu_x], [pp_y + 8, rsu_y + 8], color='black', linewidth=3)

    ax.plot([wire_start_x, turn_sheave_x], [wire_start_y, turn_sheave_y - sheave_radius],
            color='#8b4513', linewidth=2)
    ax.plot([turn_sheave_x + sheave_radius, top_sheave_x - sheave_radius],
            [turn_sheave_y, top_sheave_y], color='#8b4513', linewidth=2)

    load_cell_x = wellhead_x + (wellhead_width - 15)/2
    load_cell_y = pce_bottom + pce_height - 5
    load_cell = plt.Rectangle((load_cell_x, load_cell_y), 15, 10,
                              linewidth=1, edgecolor='red', facecolor='#ffcccc')
    ax.add_patch(load_cell)

    valve_x = wellhead_x + wellhead_width/2 - 5
    valve_y = pce_bottom + pce_height - 15
    valve = plt.Rectangle((valve_x, valve_y), 10, 10,
                          linewidth=1, edgecolor='blue', facecolor='#ccccff')
    ax.add_patch(valve)

    if operation:
        status_text = f"{operation} at {speed} ft/min"
        ax.text(rsu_x - 100, rsu_y + rsu_height + 20, status_text,
                ha='center', color='red', fontweight='bold')

    ax.set_xlim(rsu_x - 200, wellhead_x + wellhead_width + 20)
    ax.set_ylim(0, lubricator_bottom + lubricator_height + 20)
    ax.axis('off')
    ax.set_aspect('equal')
    canvas.draw()

def plot_tool_view(params, trajectory_data, current_depth, operation, speed, use_metric, canvas):
    try:
        fig = canvas.figure
        fig.clear()
        ax = fig.add_subplot(111)

        if not params or not trajectory_data:
            canvas.draw()
            return

        mds = [float(md) for md in trajectory_data['mds']]
        idx = np.argmin(np.abs(np.array(mds) - current_depth))
        max_depth = float(mds[-1])

        WELL_WIDTH = 25
        TUBING_WIDTH = WELL_WIDTH - 10
        CENTER_X = WELL_WIDTH / 2
        FLUID_LEVEL = params['fluid_level']

        casing = plt.Rectangle((0, 0), WELL_WIDTH, max_depth,
                               linewidth=2, edgecolor='gray', facecolor='#f0f0f0')
        ax.add_patch(casing)

        if FLUID_LEVEL < max_depth:
            fluid = plt.Rectangle((5, FLUID_LEVEL), TUBING_WIDTH, max_depth - FLUID_LEVEL,
                                  linewidth=0, edgecolor='none', facecolor='#e6f3ff')
            ax.add_patch(fluid)
        ax.plot([5, 5 + TUBING_WIDTH], [FLUID_LEVEL, FLUID_LEVEL],
                color='#4682B4', linewidth=1, linestyle='--')

        tubing = plt.Rectangle((5, 0), TUBING_WIDTH, max_depth,
                               linewidth=1, edgecolor='darkgray', facecolor='none')
        ax.add_patch(tubing)

        if current_depth > 0:
            ax.plot([CENTER_X, CENTER_X], [0, current_depth],
                    color='#8b4513', linewidth=2)

        socket_height = 40
        socket = plt.Rectangle((CENTER_X - 3, current_depth), 6, socket_height,
                               linewidth=2, edgecolor='darkgray', facecolor='#646464')
        ax.add_patch(socket)

        current_inclination = float(trajectory_data['inclinations'][idx])
        current_azimuth = float(trajectory_data['azimuths'][idx])

        submerged_weight, buoyancy_reduction = calculate_effective_weight(
            params, current_depth, use_metric
        )

        drag_result = calculate_fluid_drag(params, speed, current_inclination)
        drag_force, Re, flow = drag_result

        friction_result = calculate_wire_friction(
            trajectory_data, params, current_depth, use_metric
        )
        cumulative_friction, _ = friction_result

        tension_result = calculate_tension(
            params, trajectory_data, current_depth, operation,
            cumulative_friction, drag_force
        )
        tension, effective_friction, pressure_force, _ = tension_result

        depth_unit = "m" if use_metric else "ft"
        wire_weight_display = (
            params['wire_weight'] * 3.28084 if use_metric else params['wire_weight']
        )
        wire_weight_unit = "lbs/m" if use_metric else "lbs/ft"

        param_text = (
            f"Current Downhole Parameters:\n"
            f"• Depth: {current_depth:.1f} {depth_unit}\n"
            f"• Tool Weight: {params['tool_weight']} lbs\n"
            f"• Wire Weight: {wire_weight_display:.3f} {wire_weight_unit}\n"
            f"• Buoyancy Reduction: {buoyancy_reduction:.1f} lbs\n"
            f"• Effective Weight: {submerged_weight:.1f} lbs\n"
            f"• Pressure Force: {pressure_force:.1f} lbs\n"
            f"• Fluid Drag: {drag_force:.1f} lbs\n"
            f"• Reynolds Number: {Re:.0f} ({flow})\n"
            f"• Stuffing Box Friction: {params['stuffing_box']} lbs\n"
            f"• Wire Friction: {cumulative_friction:+.1f} lbs\n"
            f"• Tool String Friction: {effective_friction:+.1f} lbs\n"
            f"----------------------------------\n"
            f"• Net Tension: {tension:.1f} lbs\n"
            f"• Inclination: {current_inclination:.1f}°\n"
            f"• Azimuth: {current_azimuth:.1f}°"
        )
        ax.text(WELL_WIDTH + 70, 50, param_text,
                bbox=dict(facecolor='white', alpha=0.9, edgecolor='gray', boxstyle='round'),
                fontsize=9, verticalalignment='top')

        for depth_mark in range(0, int(max_depth) + 1, 1000):
            ax.plot([WELL_WIDTH, WELL_WIDTH + 10], [depth_mark, depth_mark], color='black', linewidth=1)
        ax.text(WELL_WIDTH + 15, depth_mark - 10, f"{depth_mark} ft")

        ax.set_xlim(-10, WELL_WIDTH + 180)
        ax.set_ylim(max_depth, 0)
        ax.set_ylabel(f"Depth ({depth_unit}-MD)", fontweight='bold')
        ax.grid(True, axis='y', linestyle='--', alpha=0.5)
        ax.set_xticks([])
        ax.set_title("Wellbore View", pad=20)
        canvas.draw()
        return tension  # Return the tension value
    except Exception as e:
        print(f"Tool view update error: {str(e)}")
        canvas.draw()
        return None  # Return None in case of error

# In plot.py

import numpy as np
from matplotlib import pyplot as plt
from features.simulator.calculations import (
    calculate_dls,
    calculate_tension,
    calculate_effective_weight,
    calculate_wire_friction,
    calculate_fluid_drag
)

def plot_tension(trajectory_data, params, current_depth, use_metric, canvas):
    """Plot tension vs depth for RIH and POOH operations."""
    fig = canvas.figure
    fig.clear()
    ax = fig.add_subplot(111)

    if not trajectory_data or not params:
        return None, None, None

    modified_params = params.copy()
    if use_metric:
        modified_params['wire_weight'] *= 3.28084  # Convert lbs/ft to lbs/m

    mds = [float(md) for md in trajectory_data['mds']]
    inclinations = [float(inc) for inc in trajectory_data['inclinations']]
    max_depth = float(mds[-1]) if mds else 0

    rih_weights, pooh_weights = [], []

    # Pre-calculate cumulative wire friction
    _, wire_friction = calculate_wire_friction(trajectory_data, modified_params, max_depth + 1, use_metric)

    for idx in range(len(mds)):
        depth = mds[idx]
        inc = inclinations[idx]

        submerged_weight, _ = calculate_effective_weight(modified_params, depth, use_metric)
        drag_force, _, _ = calculate_fluid_drag(modified_params, modified_params['speed'], inc)
        cumulative_friction = sum(wire_friction[:idx])

        rih_tension, _, _, _ = calculate_tension(
            modified_params, trajectory_data, depth, "RIH", cumulative_friction, drag_force
        )
        pooh_tension, _, _, _ = calculate_tension(
            modified_params, trajectory_data, depth, "POOH", cumulative_friction, drag_force
        )

        rih_weights.append(rih_tension)
        pooh_weights.append(pooh_tension)

    ax.plot(rih_weights, mds, 'b-', label='RIH Tension')
    ax.plot(pooh_weights, mds, 'c-', label='POOH Tension')
    ax.axvline(0, color='red', linestyle='-')

    if current_depth is not None:
        idx = np.argmin(np.abs(np.array(mds) - current_depth))
        ax.plot(rih_weights[idx], mds[idx], 'bo')
        ax.plot(pooh_weights[idx], mds[idx], 'co')
        ax.axhline(current_depth, color='gray', linestyle='--')

    ax.set_xlabel("Tension (lbs)")
    ax.set_ylabel("Depth (m MD)" if use_metric else "Depth (ft MD)")
    ax.set_title("Tension vs Depth Profile")
    ax.grid(True)
    ax.legend()
    ax.set_ylim(max_depth, 0)
    if min(rih_weights) > -50:
        ax.set_xlim(left=-50)
    canvas.draw()

    return rih_weights, pooh_weights, mds

def plot_overpull(pooh_weights, depth_points, breaking_strength, safe_operating_load, current_depth, use_metric, canvas):
    """Plot maximum overpull vs depth."""
    fig = canvas.figure
    fig.clear()
    ax = fig.add_subplot(111)

    if not pooh_weights or not depth_points:
        return None

    safe_pull = (safe_operating_load / 100) * breaking_strength
    max_overpulls = [max(safe_pull - pooh, 0) for pooh in pooh_weights]

    ax.plot(max_overpulls, depth_points, 'r-', label='Max Overpull')

    if current_depth is not None:
        idx = np.argmin(np.abs(np.array(depth_points) - current_depth))
        ax.plot(max_overpulls[idx], depth_points[idx], 'ro')
        ax.axhline(current_depth, color='gray', linestyle='--', alpha=0.5)

    ax.set_xlabel('Max Overpull (lbs)')
    ax.set_ylabel("Depth (m MD)" if use_metric else "Depth (ft MD)")
    ax.set_title("Maximum Overpull vs Depth")
    ax.grid(True)
    ax.legend()
    ax.set_ylim(max(depth_points) if depth_points else 0, 0)
    ax.set_xlim(left=0)
    canvas.draw()

    return max_overpulls

def plot_inclination_dls(trajectory_data, use_metric, current_depth, canvas):
    """Plot inclination and DLS vs depth."""
    fig = canvas.figure
    fig.clear()
    ax = fig.add_subplot(111)

    if not trajectory_data:
        return None

    mds = [float(md) for md in trajectory_data['mds']]
    inclinations = [float(inc) for inc in trajectory_data['inclinations']]
    max_depth = float(mds[-1]) if mds else 0

    dls_values = calculate_dls(trajectory_data, use_metric)

    ax2 = ax.twiny()
    ax.plot(inclinations, mds, 'b-', label='Inclination')

    if len(mds) >= 2:
        ax2.step(dls_values[1:], mds[:-1], where='post', color='r', label='DLS')
    else:
        ax2.plot([], [], 'r-', label='DLS')

    ax2.set_xlabel('DLS (°/30m)' if use_metric else 'DLS (°/100ft)')

    if current_depth is not None and mds:
        idx = np.argmin(np.abs(np.array(mds) - current_depth))
        ax.plot(inclinations[idx], mds[idx], 'bo', markersize=8)
        ax.axhline(current_depth, color='gray', linestyle='--', alpha=0.5)
        if len(mds) >= 2 and idx < len(dls_values):
            ax2.plot(dls_values[idx], mds[idx], 'ro', markersize=8)

    ax.set_title("Inclination & DLS vs Depth")
    ax.set_ylabel("Depth (m MD)" if use_metric else "Depth (ft MD)")
    ax.grid(True)
    ax.set_ylim(max_depth, 0)

    lines, labels = ax.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax.legend(lines + lines2, labels + labels2, loc='upper right')
    canvas.draw()

    return dls_values
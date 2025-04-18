import numpy as np

def get_fluid_name(gradient):
    abs_gradient = abs(gradient)
    if abs_gradient <= 0.10:
        return f"Gas Gradient ({abs_gradient:.2f} psi/ft)"
    elif 0.27 <= abs_gradient <= 0.32:
        return f"Oil Gradient ({abs_gradient:.2f} psi/ft)"
    elif 0.40 <= abs_gradient <= 0.46:
        return f"Water Gradient ({abs_gradient:.2f} psi/ft)"
    else:
        return f"Unknown Fluid ({abs_gradient:.2f} psi/ft)"

def plot_survey(ax, tvd_list, pressure_list, survey_type, trendline):
    ax.clear()

    # Sort TVD descending
    combined = list(zip(tvd_list, pressure_list))
    combined.sort(reverse=True, key=lambda x: x[0])
    tvd, pressure = zip(*combined)
    tvd = np.array(tvd)
    pressure = np.array(pressure)

    marker = 'o' if survey_type.startswith("Static") else '^'
    ax.plot(pressure, tvd, marker=marker, label=survey_type)

    if trendline:
        # Smart split index finder using RMSE of two fits
        min_error = float('inf')
        best_split = None

        for i in range(5, len(tvd) - 5):
            m1, c1 = np.polyfit(tvd[:i], pressure[:i], 1)
            m2, c2 = np.polyfit(tvd[i:], pressure[i:], 1)
            err1 = np.sqrt(np.mean((pressure[:i] - (m1 * tvd[:i] + c1))**2))
            err2 = np.sqrt(np.mean((pressure[i:] - (m2 * tvd[i:] + c2))**2))
            total_error = err1 + err2
            if total_error < min_error:
                min_error = total_error
                best_split = i
                best_params = (m1, c1, m2, c2)

        split_index = best_split
        m1, c1, m2, c2 = best_params

        if m1 != m2:
            tvd_fluid = (c2 - c1) / (m1 - m2)
            pressure_fluid = m1 * tvd_fluid + c1

            delta_pressure = 100
            pressure_min = min(pressure)
            pressure_max = max(pressure)

            flatter, steeper = (m1, m2) if abs(m1) > abs(m2) else (m2, m1)
            gas_label = get_fluid_name(steeper)
            liquid_label = get_fluid_name(flatter)

            if abs(m1) > abs(m2):
                # m1 is steeper → gas
                p1_range = np.linspace(pressure_min, pressure_fluid + delta_pressure, 100)
                tvd1_range = (p1_range - c2) / m2
                ax.plot(p1_range, tvd1_range, '--', color='orange', label=gas_label)

                p2_range = np.linspace(pressure_fluid - delta_pressure, pressure_max, 100)
                tvd2_range = (p2_range - c1) / m1
                ax.plot(p2_range, tvd2_range, '--', color='green', label=liquid_label)
            else:
                # m2 is steeper → gas
                p2_range = np.linspace(pressure_min, pressure_fluid + delta_pressure, 100)
                tvd2_range = (p2_range - c2) / m2
                ax.plot(p2_range, tvd2_range, '--', color='orange', label=gas_label)

                p1_range = np.linspace(pressure_fluid - delta_pressure, pressure_max, 100)
                tvd1_range = (p1_range - c1) / m1
                ax.plot(p1_range, tvd1_range, '--', color='green', label=liquid_label)

            ax.plot(pressure_fluid, tvd_fluid, 'ro', label='Fluid Level')
            ax.annotate(f"Fluid Level\nTVD: {tvd_fluid:.0f} ft\nP: {pressure_fluid:.0f} psi",
                        (pressure_fluid, tvd_fluid),
                        textcoords="offset points", xytext=(10, -10),
                        ha='left', color='red')

    ax.set_title(f"{survey_type} Pressure vs TVD")
    ax.set_xlabel("Pressure (psi)")
    ax.set_ylabel("TVD (ft)")
    ax.invert_yaxis()
    ax.grid(True)
    ax.legend()
    return ax

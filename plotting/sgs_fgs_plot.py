import numpy as np

def plot_survey(ax, tvd_list, pressure_list, survey_type, trendline):
    ax.clear()

    # Sort TVD descending
    combined = list(zip(tvd_list, pressure_list))
    combined.sort(reverse=True, key=lambda x: x[0])
    tvd, pressure = zip(*combined)

    # Derivatives
    gradient = np.gradient(pressure, tvd)
    second_derivative = np.gradient(gradient, tvd)

    marker = 'o' if survey_type.startswith("Static") else '^'
    ax.plot(pressure, tvd, marker=marker, label=survey_type)


    if trendline:
        split_index = np.argmax(np.abs(second_derivative[1:-1])) + 1

        coeffs1 = np.polyfit(tvd[:split_index], pressure[:split_index], 1)
        coeffs2 = np.polyfit(tvd[split_index:], pressure[split_index:], 1)

        m1, c1 = coeffs1
        m2, c2 = coeffs2

        if m1 != m2:
            tvd_fluid = (c2 - c1) / (m1 - m2)
            pressure_fluid = m1 * tvd_fluid + c1

            delta_pressure = 100  # pressure range around intersection
            pressure_min = min(pressure)
            pressure_max = max(pressure)

            if abs(m1) > abs(m2):
                # m1 is steeper
                # Steeper: from min pressure to just after fluid level
                p1_range = np.linspace(pressure_min, pressure_fluid + delta_pressure, 100)
                tvd1_range = (p1_range - c2) / m2
                ax.plot(p1_range, tvd1_range, '--', color='orange', label='Gas Gradient')

                # Flatter: from just before fluid level to max pressure
                p2_range = np.linspace(pressure_fluid - delta_pressure, pressure_max, 100)
                tvd2_range = (p2_range - c1) / m1
                ax.plot(p2_range, tvd2_range, '--', color='green', label='Liquid Gradient')
            else:
                # m2 is steeper
                # Steeper: from min pressure to just after fluid level
                p2_range = np.linspace(pressure_min, pressure_fluid + delta_pressure, 100)
                tvd2_range = (p2_range - c2) / m2
                ax.plot(p2_range, tvd2_range, '--', color='orange', label='Gas Gradient')

                # Flatter: from just before fluid level to max pressure
                p1_range = np.linspace(pressure_fluid - delta_pressure, pressure_max, 100)
                tvd1_range = (p1_range - c1) / m1
                ax.plot(p1_range, tvd1_range, '--', color='green', label='Liquid Gradient')

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
    # ax.tick_params(left=False, bottom=False, labelleft=False, labelbottom=False)
    return ax

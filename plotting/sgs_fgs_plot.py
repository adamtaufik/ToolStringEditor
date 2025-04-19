import numpy as np
import matplotlib.pyplot as plt

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

def plot_survey(ax, tvd_list, pressure_list, survey_type, trendline,
                temperature_list=None, fgs_temp_list=None):

    ax.clear()
    ax.invert_yaxis()

    print('7')
    # Sort TVD descending
    combined = list(zip(tvd_list, pressure_list))
    combined.sort(reverse=True, key=lambda x: x[0])
    tvd, pressure = zip(*combined)
    tvd = np.array(tvd)
    pressure = np.array(pressure)

    print('8')
    # Plot pressure data
    marker = 'o' if survey_type.startswith("Static") else '^'
    if survey_type.startswith("Static"):
        ax.scatter(pressure, tvd, marker=marker, label="SGS Pressure")
    else:
        ax.plot(pressure, tvd, marker=marker, label="FGS Pressure")

    print('9')
    # Trendline logic for pressure
    if trendline:
        min_error = float('inf')
        best_split = None

        print('10')
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

    print('11')
    # === SECONDARY X-AXIS FOR TEMPERATURE === #
    if temperature_list is not None:
        ax_temp = ax.twiny()

        # Sort for plotting
        temp_combined = list(zip(tvd_list, temperature_list))
        temp_combined.sort(reverse=True, key=lambda x: x[0])

        if temp_combined:  # Ensure it's not empty
            tvd_temp, temp = zip(*temp_combined)
            tvd_temp = np.array(tvd_temp)
            temp = np.array(temp)

            print('12')

            try:
                ax_temp.plot(temp, tvd_temp, color='blue', label='SGS Temperature', marker='s', linestyle='None')
                # === SGS Temperature Linear Trendline ===
                # Fit linear trendline (1st degree polynomial)
                sgs_fit_coeffs = np.polyfit(tvd_temp, temp, 1)
                sgs_slope, sgs_intercept = sgs_fit_coeffs

                # Calculate fitted temps using the linear fit
                sgs_temp_fit = np.polyval(sgs_fit_coeffs, tvd_temp)

                # Plot the linear trendline
                ax_temp.plot(sgs_temp_fit, tvd_temp, color='lightblue', linestyle=':', linewidth=2,
                             label=f'Temp. Gradient ({sgs_slope * 100:.2f} °F/100ft)')

                ax_temp.set_xlabel("Temperature (°F)")
            except Exception as e:
                print("Error during temperature plotting:", str(e))
                return ax

            ax_temp.set_xlabel("Temperature (°F)")
            ax_temp.set_xlim(min(temp), max(temp))
            ax_temp.set_ylim(ax.get_ylim())
        else:
            print("Temperature list mismatch or empty.")

        print('13')
        # Optional curved trendline for FGS
        if fgs_temp_list is not None:
            fgs_combined = list(zip(tvd_list, fgs_temp_list))
            fgs_combined.sort(reverse=True, key=lambda x: x[0])

            if fgs_combined:  # Ensure it's not empty
                tvd_fgs, temp_fgs = zip(*fgs_combined)
                tvd_fgs = np.array(tvd_fgs)
                temp_fgs = np.array(temp_fgs)

                coeffs = np.polyfit(tvd_fgs, temp_fgs, deg=2)
                fitted_temp = np.polyval(coeffs, tvd_fgs)
                ax_temp.plot(fitted_temp, tvd_fgs, color='purple', linestyle='--', label='FGS Temp Fit')

    ax.set_title(f"{survey_type} Pressure vs TVD")
    ax.set_xlabel("Pressure (psi)")
    ax.set_ylabel("TVD (ft)")
    ax.grid(True)

    # Collect handles and labels from both axes
    handles_main, labels_main = ax.get_legend_handles_labels()
    handles_temp, labels_temp = ax_temp.get_legend_handles_labels()

    # Combine them
    combined_handles = handles_main + handles_temp
    combined_labels = labels_main + labels_temp

    # Show one unified legend on the main axis
    ax.legend(combined_handles, combined_labels, loc='upper right')

    return ax

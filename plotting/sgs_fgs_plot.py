import matplotlib.pyplot as plt

def plot_survey(ax, tvd_list, pressure_list, survey_type, trendline=False):

    ax.clear()

    # Sort TVD in descending order and rearrange pressures accordingly
    combined = list(zip(tvd_list, pressure_list))
    combined.sort(reverse=True, key=lambda x: x[0])  # sort by TVD descending
    tvd_list, pressure_list = zip(*combined)

    marker = 'o' if survey_type.startswith("Static") else '^'
    ax.plot(pressure_list, tvd_list, marker=marker, label=survey_type)

    if survey_type == "Flowing Gradient Survey (FGS)":
        trendline = False

    # Optional linear regression
    if trendline:
        from numpy import polyfit, linspace, polyval
        coeffs = polyfit(tvd_list, pressure_list, 1)
        tvd_range = linspace(min(tvd_list), max(tvd_list), 100)
        pressure_fit = polyval(coeffs, tvd_range)
        ax.plot(pressure_fit, tvd_range, linestyle='--', color='gray', label='Trendline')

    ax.set_title(f"{survey_type} Pressure vs TVD")
    ax.set_xlabel("Pressure (psi)")
    ax.set_ylabel("TVD (ft)")
    ax.invert_yaxis()
    ax.grid(True)
    ax.legend()
    return ax

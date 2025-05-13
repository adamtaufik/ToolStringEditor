"""
Core physics calculations for wireline operations
"""
import math
import numpy as np
from dataclasses import dataclass
from typing import List, Tuple


@dataclass
class SimulationParameters:
    wire_diameter: float  # inches
    wire_weight: float  # lbs/ft
    tool_weight: float  # lbs
    fluid_density: float  # ppg
    fluid_level: float  # ft
    well_pressure: float  # psi
    friction_coeff: float
    static_friction_factor: float = 1.2


def calculate_buoyancy_factor(fluid_density: float) -> float:
    """Calculate buoyancy factor (1 - ρ_fluid/ρ_steel)"""
    return 1 - (fluid_density / 65.4)


def calculate_tension(
        depth: float,
        params: SimulationParameters,
        inclination: float,
        operation: str = None,
        last_operation: str = None
) -> Tuple[float, dict]:
    """
    Calculate wireline tension with all factors considered
    Returns tuple of (tension, calculation_breakdown)
    """
    # Weight calculations
    wire_weight = depth * params.wire_weight
    total_weight = params.tool_weight + wire_weight

    # Buoyancy effect
    submerged_length = max(depth - params.fluid_level, 0)
    buoyancy_reduction = submerged_length * params.wire_weight * (1 - calculate_buoyancy_factor(params.fluid_density))
    submerged_weight = total_weight - buoyancy_reduction

    # Pressure force
    wire_area = math.pi * (params.wire_diameter / 2) ** 2
    pressure_force = params.well_pressure * wire_area

    # Inclination effects
    inclination_rad = math.radians(inclination)
    effective_weight = submerged_weight * math.cos(inclination_rad)

    # Friction calculation
    friction_force = 0
    if inclination > 1.0:  # Only in deviated sections
        normal_force = submerged_weight * math.sin(inclination_rad)
        friction_magnitude = params.friction_coeff * normal_force

        if operation == "RIH":
            friction_force = -friction_magnitude  # Opposes RIH
        elif operation == "POOH":
            friction_force = friction_magnitude  # Opposes POOH
        elif last_operation:  # Static friction
            if last_operation == "RIH":
                friction_force = -friction_magnitude * params.static_friction_factor
            else:
                friction_force = friction_magnitude * params.static_friction_factor

    # Final tension (minimum of 0)
    tension = max(effective_weight - pressure_force + friction_force, 0)

    # Return breakdown for debugging/display
    breakdown = {
        'wire_weight': wire_weight,
        'total_weight': total_weight,
        'buoyancy_reduction': buoyancy_reduction,
        'submerged_weight': submerged_weight,
        'pressure_force': pressure_force,
        'effective_weight': effective_weight,
        'friction_force': friction_force,
        'inclination': inclination
    }

    return tension, breakdown


def calculate_dls(md1: float, md2: float, inc1: float, inc2: float) -> float:
    """Calculate Dog Leg Severity between two survey points"""
    if md1 == md2:
        return 0.0
    delta_inc = abs(inc2 - inc1)
    return (delta_inc / (md2 - md1)) * 100
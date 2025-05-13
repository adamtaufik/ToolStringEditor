"""
Data structures for well trajectory and simulation state
"""
from dataclasses import dataclass
from typing import List, Optional
import numpy as np
from scipy.interpolate import interp1d

from features.simulator import calculate_dls


@dataclass
class SurveyPoint:
    md: float      # Measured depth (ft)
    tvd: float     # True vertical depth (ft)
    incl: float    # Inclination (degrees)
    azim: float    # Azimuth (degrees)
    north: float = 0
    east: float = 0

class WellTrajectory:
    def __init__(self, survey_points: List[SurveyPoint]):
        self.survey_points = sorted(survey_points, key=lambda x: x.md)
        self._calculate_derived_data()

    def _calculate_derived_data(self):
        """Calculate north/east coordinates and DLS for full trajectory"""
        mds = [p.md for p in self.survey_points]
        tvds = [p.tvd for p in self.survey_points]
        incls = [p.incl for p in self.survey_points]
        azims = [p.azim for p in self.survey_points]

        # Calculate north/east coordinates
        north = [0.0]
        east = [0.0]

        for i in range(1, len(mds)):
            delta_md = mds[i] - mds[i-1]
            rad_inc = np.radians(incls[i])
            rad_azim = np.radians(azims[i])

            north.append(north[i-1] + np.sin(rad_inc) * np.cos(rad_azim) * delta_md)
            east.append(east[i-1] + np.sin(rad_inc) * np.sin(rad_azim) * delta_md)

        # Update survey points
        for i, point in enumerate(self.survey_points):
            point.north = north[i]
            point.east = east[i]

        # Create interpolation functions
        self._tvd_interp = interp1d(mds, tvds, kind='linear', fill_value='extrapolate')
        self._incl_interp = interp1d(mds, incls, kind='linear', fill_value='extrapolate')
        self._azim_interp = interp1d(mds, azims, kind='linear', fill_value='extrapolate')
        self._north_interp = interp1d(mds, north, kind='linear', fill_value='extrapolate')
        self._east_interp = interp1d(mds, east, kind='linear', fill_value='extrapolate')

    def get_point_at_depth(self, depth: float) -> SurveyPoint:
        """Get interpolated survey data at specified depth"""
        return SurveyPoint(
            md=depth,
            tvd=float(self._tvd_interp(depth)),
            incl=float(self._incl_interp(depth)),
            azim=float(self._azim_interp(depth)),
            north=float(self._north_interp(depth)),
            east=float(self._east_interp(depth))
        )

    @property
    def mds(self) -> List[float]:
        return [p.md for p in self.survey_points]

    @property
    def max_depth(self) -> float:
        return max(p.md for p in self.survey_points) if self.survey_points else 0

    def get_dls_profile(self) -> List[float]:
        """Calculate DLS for entire trajectory"""
        dls = [0.0]  # Surface point has no DLS
        for i in range(1, len(self.survey_points)):
            p1 = self.survey_points[i-1]
            p2 = self.survey_points[i]
            dls.append(calculate_dls(p1.md, p2.md, p1.incl, p2.incl))
        return dls
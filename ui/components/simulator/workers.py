#workers.py
from PyQt6.QtCore import QThread, pyqtSignal

import numpy as np


class CalculationWorker(QThread):
    finished = pyqtSignal(object)
    error = pyqtSignal(Exception)

    def __init__(self, trajectory_data, current_depth):
        super().__init__()
        self.t_data = trajectory_data
        self.depth = current_depth

    def run(self):
        try:
            if self.isInterruptionRequested():
                return

            # Add bounds checking
            if len(self.t_data['mds']) == 0:
                return

            idx = np.argmin(np.abs(self.t_data['mds'] - self.depth))
            result = {
                'north': self.t_data['north'][idx],
                'east': self.t_data['east'][idx],
                'tvd': self.t_data['tvd'][idx]
            }
            self.finished.emit(result)

        except Exception as e:
            self.error.emit(e)


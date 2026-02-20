"""
Base load classes for the HEMS system.
"""

import cvxpy as cp
import numpy as np

from .const import T_DEFAULT


class GenericLoad:
    """A generic load class representing a load in the HEMS system.

    This is the base class for all load types in the Home Energy Management System.
    It defines the common interface and basic attributes shared by all loads.

    Attributes:
        name (str): Name identifier for the load.
        T (int): Time horizon (number of time steps) for the load.
    """

    def __init__(self, name: str, T: int):
        """Initialize a generic load.

        Args:
            name (str): Name identifier for the load.
            T (int): Time horizon (number of time steps) for the load.
        """
        self.name = name
        self.T = T  # Time horizon for the load


class FlexibleLoad(GenericLoad):
    """A flexible load that can be scheduled or controlled.

    This class represents loads whose power consumption can be optimized
    over the time horizon. The power consumption is modeled as a decision
    variable in the optimization problem.
    """

    def __init__(self, name: str, T: int):
        """Initialize a flexible load.

        Args:
            name (str): Name identifier for the load.
            T (int): Time horizon (number of time steps) for the load.
        """
        super().__init__(name, T)
        self.P = cp.Variable(T, nonneg=True)


class FixedLoad(GenericLoad):
    """A fixed load that has a prescribed consumption pattern.

    This class represents loads with predetermined power consumption that
    cannot be controlled or modified by the optimization. The power profile
    is fixed throughout the time horizon.
    """

    def __init__(self, name: str, power_profile: np.ndarray):
        """Initialize a fixed load with a prescribed power profile.

        Args:
            name (str): Name identifier for the load.
            power_profile (np.ndarray): Array of power consumption values (kW)
                for each time step. The length of this array determines the
                time horizon T.
        """
        super().__init__(name, len(power_profile))
        self.P = cp.Parameter(self.T, nonneg=True)
        self.P.value = power_profile


class BaseLoad(FixedLoad):
    """A base load that represents non-flexible, non-controllable consumption.

    This class is a specific type of fixed load that represents the baseline
    energy consumption in the home. It can be used to model essential loads
    that must be met regardless of optimization decisions.
    """

    def __init__(self, name: str, P_base: np.ndarray | float = 0.5):
        """Initialize a base load with a fixed power profile.

        Args:
            name (str): Name identifier for the load.
            P_base (np.ndarray | float): Power consumption profile (kW) for each
                time step. If a single float is provided, it will be repeated
                for all time steps.
        """
        if isinstance(P_base, (int, float)):
            power_profile = np.full(T_DEFAULT, P_base)
        else:
            power_profile = P_base
        super().__init__(name, power_profile)

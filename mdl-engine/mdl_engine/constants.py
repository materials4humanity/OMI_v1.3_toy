Q = 1.602176634e-19      # C
KB = 1.380649e-23        # J/K
H = 6.62607015e-34       # J s
C = 2.99792458e8         # m/s
T_CELL = 298.15          # K (25 C, STC)
T_SUN = 5772.0           # K, effective solar temperature
P_STC = 0.1              # W/cm^2 (1000 W/m^2)


def vt(temp_k: float = T_CELL) -> float:
    """Thermal voltage kT/q in volts."""
    return KB * temp_k / Q

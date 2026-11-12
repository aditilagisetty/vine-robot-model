"""
Single source of truth for every model parameter.
Change a value here, then rerun the scripts; nothing else should need editing.

Values marked PLACEHOLDER are guesses until the bench tests replace them.
"""

# ---------------------------------------------------------------- geometry
d = 0.05            # body diameter [m]                     PLACEHOLDER -> your tube
L = 0.70            # total grown length [m], two equal segments (B3 body)

# ---------------------------------------------------------------- material
EI_eff = 0.05       # effective bending stiffness [N m^2]   PLACEHOLDER -> B0
density = 200.0     # rod density for PyElastica [kg/m^3]   (only affects settling time)

# ---------------------------------------------------------------- sPAM strains
EPS_SAMPLES = (0.05, 0.06, 0.08)   # strains used in examples  PLACEHOLDER -> B2

# Shape cases: (eps1, eps2) on segment 1 (base) and 2 (tip). Sign = side.
SHAPE_CASES = {
    "Straight (no actuation)": (0.00, 0.00),
    "C-shape (same side)":     (0.05, 0.05),
    "S-shape (opposite)":      (0.06, -0.06),
    "Tip-only bend":           (0.00, 0.08),
}

# ---------------------------------------------------------------- B0 cantilever test
TIP_LOADS = (0.05, 0.10, 0.20)     # tip forces [N]; keep delta/L < ~0.1 for linear fit

# ---------------------------------------------------------------- wall (sanity checks)
p_body = 7e3        # body pressure [Pa]
t_wall = 0.1e-3     # film thickness [m]

# ---------------------------------------------------------------- simulation
n_elem = 70         # PyElastica elements (1 cm each at L = 0.7 m)
n_regions = 35      # PCC regions per segment (1 cm each, matches n_elem)

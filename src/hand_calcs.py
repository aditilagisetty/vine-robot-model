"""
Hand calculations for the vine baseline model, done step by step.
Every number in docs/hand_calculations.md comes from this script.

Run:  python src/hand_calcs.py
"""
import numpy as np

d   = 0.05    # body diameter [m]
r   = d / 2
L   = 0.70    # total length [m]
ell = L / 2   # length of each segment [m]
EI  = 0.05    # effective bending stiffness [N m^2] (placeholder until B0)

print("=" * 64)
print("1. Curvature from sPAM strain:  kappa = eps / d")
print("=" * 64)
for eps in (0.05, 0.06, 0.08):
    k = eps / d
    print(f"  eps = {eps:.2f}  ->  kappa = {eps:.2f} / {d} = {k:.2f} 1/m"
          f"   (radius R = 1/kappa = {1/k:.3f} m)")

def arc(kappa, ell):
    """Tip displacement and heading change of one constant-curvature arc,
    in the arc's own starting frame (starts at origin pointing along +x)."""
    if abs(kappa) < 1e-12:
        return ell, 0.0, 0.0
    th = kappa * ell
    return np.sin(th) / kappa, (1 - np.cos(th)) / kappa, th

def two_segment(k1, k2, verbose=True):
    # Segment 1
    x1, y1, th1 = arc(k1, ell)
    # Segment 2 in its own frame, then rotate by th1 and shift to (x1, y1)
    dx, dy, th2 = arc(k2, ell)
    c, s = np.cos(th1), np.sin(th1)
    X = x1 + c * dx - s * dy
    Y = y1 + s * dx + c * dy
    if verbose:
        print(f"  Segment 1: kappa1*ell = {k1:.2f}*{ell} = {th1:.4f} rad "
              f"({np.degrees(th1):.1f} deg)")
        if k1:
            print(f"     x1 = sin({th1:.4f})/{k1} = {x1:.4f} m, "
                  f"y1 = (1-cos({th1:.4f}))/{k1} = {y1:.4f} m")
        else:
            print(f"     straight: x1 = ell = {x1:.4f} m, y1 = 0")
        print(f"  Segment 2 (own frame): theta2 = {th2:.4f} rad, "
              f"dx = {dx:.4f} m, dy = {dy:.4f} m")
        print(f"     rotate by theta1: cos = {c:.5f}, sin = {s:.5f}")
        print(f"     X = {x1:.4f} + {c:.5f}*{dx:.4f} - {s:.5f}*{dy:.4f} = {X:.4f} m")
        print(f"     Y = {y1:.4f} + {s:.5f}*{dx:.4f} + {c:.5f}*{dy:.4f} = {Y:.4f} m")
        print(f"  Tip heading = {th1 + th2:.4f} rad ({np.degrees(th1 + th2):.1f} deg)")
    return X, Y, th1 + th2

print()
print("=" * 64)
print("2. Two-segment piecewise-constant-curvature (PCC) tip positions")
print("=" * 64)
cases = {
    "C-shape (eps1=eps2=+0.05)":   (1.0, 1.0),
    "S-shape (eps1=+0.06, eps2=-0.06)": (1.2, -1.2),
    "Tip-only (eps2=+0.08)":       (0.0, 1.6),
}
hand = {}
for name, (k1, k2) in cases.items():
    print(f"\n{name}")
    hand[name] = two_segment(k1, k2)

print()
print("=" * 64)
print("3. Choosing E for PyElastica (it uses a SOLID circular section)")
print("=" * 64)
I_solid = np.pi * r**4 / 4
print(f"  I_solid = pi r^4 / 4 = pi*{r}^4/4 = {I_solid:.4e} m^4")
print(f"  E = EI_eff / I_solid = {EI}/{I_solid:.4e} = {EI/I_solid:.4e} Pa")
t = 1e-3
I_tube = np.pi * r**3 * t
print(f"  (Wrong way, thin tube t=1 mm: I_tube = pi r^3 t = {I_tube:.4e} m^4,")
print(f"   E = {EI/I_tube:.3e} Pa -> PyElastica's actual EI = {EI/I_tube*I_solid:.3f}"
      f" N m^2, {I_solid/I_tube:.2f}x too stiff)")

print()
print("=" * 64)
print("4. Cantilever tip deflection (B0 test), small-deflection theory")
print("=" * 64)
print(f"  delta = F L^3 / (3 EI),  L^3 = {L**3:.3f} m^3,  3EI = {3*EI:.2f} N m^2")
for F in (0.05, 0.10, 0.20):
    dl = F * L**3 / (3 * EI)
    print(f"  F = {F:.2f} N -> delta = {F}*{L**3:.3f}/{3*EI:.2f} = {dl*1000:.1f} mm"
          f"   (delta/L = {dl/L:.2f})")
print("  Rule of thumb: linear theory is good while delta/L < ~0.1.")

print()
print("=" * 64)
print("5. Wall stresses at a sample body pressure (sanity check)")
print("=" * 64)
p = 7e3      # 7 kPa, a typical vine robot body pressure
tw = 0.1e-3  # 0.1 mm film
print(f"  p = {p/1e3:.0f} kPa, r = {r} m, t = {tw*1e3} mm")
print(f"  hoop  sigma = p r / t     = {p*r/tw/1e6:.2f} MPa")
print(f"  axial sigma = p r / (2 t) = {p*r/(2*tw)/1e6:.2f} MPa")
print(f"  wrinkling moment M_w = pi p r^3 / 2 = {np.pi*p*r**3/2*1000:.1f} N mm")
print(f"  tip force ~ p * pi r^2 = {p*np.pi*r**2:.1f} N")

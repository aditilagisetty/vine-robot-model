"""Large-deflection cantilever (Euler elastica) via scipy solve_bvp.
EI*theta'' = -F*cos(theta), theta(0)=0, theta'(L)=0. Independent check of PyElastica."""
import numpy as np
from scipy.integrate import solve_bvp, cumulative_trapezoid
L, EI = 0.70, 0.05
def tip_deflection(F):
    f = lambda s, y: np.vstack([y[1], -F/EI*np.cos(y[0])])
    bc = lambda a, b: np.array([a[0], b[1]])
    s = np.linspace(0, L, 400)
    sol = solve_bvp(f, bc, s, np.zeros((2, s.size)), tol=1e-8)
    th = sol.sol(s)[0]
    return abs(cumulative_trapezoid(np.sin(th), s, initial=0)[-1])  # magnitude
if __name__ == "__main__":
    for F, sim in [(0.05, 109.2), (0.10, 204.1), (0.20, 336.8)]:
        d = tip_deflection(F)*1000
        print(f"F={F:.2f} N  elastica={d:6.1f} mm  PyElastica={sim:6.1f} mm  diff={abs(sim-d)/d*100:4.1f}%")

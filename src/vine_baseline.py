"""
Vine robot baseline model (P0 / pre-hardware)
=============================================
Two-segment planar vine on a table (gravity out of plane, so ignored).
Each segment is bent by an sPAM, modeled as a rest curvature:

    kappa = eps / d        (eps = sPAM contraction strain, d = body diameter)

We simulate the rod in PyElastica (Cosserat rod) and compare the settled
shape with the analytical piecewise-constant-curvature (PCC) model.
If both agree, the simulation pipeline is trustworthy and ready for real
parameters (EI_eff from B0, eps(p) from B2) once the hardware arrives.

Run:  python src/vine_baseline.py   (~6 min; figures go to figures/)
"""
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import elastica as ea
from pathlib import Path

FIG = Path(__file__).resolve().parent.parent / "figures"
FIG.mkdir(exist_ok=True)

# ---------------------------------------------------------------- parameters
L       = 0.70      # total grown length [m]  (B3 fixed-length body ~0.7 m)
d       = 0.05      # body diameter [m]       (placeholder, set from your tube)
n_elem  = 70        # elements (1 cm each)
EI_eff  = 0.05      # effective bending stiffness [N m^2] PLACEHOLDER -> from B0
# Rest curvature doesn't depend on EI in free bending, but contact/loads will.

# ------------------------------------------------------- analytical PCC model
def pcc_shape(kappas, seg_lengths, n=400):
    """Planar piecewise-constant-curvature centerline starting at origin, +x."""
    s_all = np.linspace(0, sum(seg_lengths), n)
    edges = np.concatenate([[0], np.cumsum(seg_lengths)])
    x, y, th = np.zeros(n), np.zeros(n), np.zeros(n)
    ds = s_all[1] - s_all[0]
    for i in range(1, n):
        seg = min(np.searchsorted(edges, s_all[i - 1], side="right") - 1,
                  len(kappas) - 1)
        k = kappas[seg]
        th[i] = th[i - 1] + k * ds
        thm = 0.5 * (th[i] + th[i - 1])
        x[i] = x[i - 1] + np.cos(thm) * ds
        y[i] = y[i - 1] + np.sin(thm) * ds
    return x, y

# ------------------------------------------------------- PyElastica model
class VineSim(ea.BaseSystemCollection, ea.Constraints, ea.Damping,
              ea.CallBacks, ea.Forcing):
    pass

def simulate(eps1, eps2, tip_force=0.0, final_time=20.0, n_elem=n_elem):
    """eps1, eps2: sPAM strain on segment 1 (base) and 2 (tip). Sign = side."""
    sim = VineSim()
    r = d / 2
    # PyElastica uses a SOLID circular section: I = pi r^4 / 4.
    # The real vine is a thin pressurized tube, so we pick E so that the
    # product E*I equals the measured EI_eff (from B0). Only EI matters.
    I_solid = np.pi * r**4 / 4
    E = EI_eff / I_solid
    rod = ea.CosseratRod.straight_rod(
        n_elements=n_elem,
        start=np.zeros(3),
        direction=np.array([1.0, 0.0, 0.0]),
        normal=np.array([0.0, 0.0, 1.0]),           # d1 = z -> bends in x-y plane
        base_length=L,
        base_radius=r,
        density=200.0,
        youngs_modulus=E,
        shear_modulus=E / 1.5,
    )
    # sPAM actuation = rest curvature on each half (voronoi nodes)
    kappa1, kappa2 = eps1 / d, eps2 / d
    # voronoi index j sits on node j+1; joint is node n_elem//2
    joint = n_elem // 2
    rod.rest_kappa[0, :joint - 1] = kappa1
    rod.rest_kappa[0, joint - 1] = 0.5 * (kappa1 + kappa2)
    rod.rest_kappa[0, joint:] = kappa2
    sim.append(rod)

    sim.constrain(rod).using(ea.OneEndFixedBC,
                             constrained_position_idx=(0,),
                             constrained_director_idx=(0,))
    if tip_force:
        sim.add_forcing_to(rod).using(ea.EndpointForces,
                                      np.zeros(3),
                                      np.array([0.0, -tip_force, 0.0]),
                                      ramp_up_time=1.0)
    dt = 4e-5 * (70 / n_elem)          # stable: well under dx / sqrt(E/rho)
    sim.dampen(rod).using(ea.AnalyticalLinearDamper,
                          damping_constant=1.0, time_step=dt)
    sim.finalize()
    # integrate in two chunks so we can check the rod has stopped moving
    stepper = ea.PositionVerlet()
    t1 = 0.9 * final_time
    ea.integrate(stepper, sim, t1, int(t1 / dt), progress_bar=False)
    tip_before = rod.position_collection[:, -1].copy()
    t = np.float64(t1)
    for _ in range(int((final_time - t1) / dt)):
        t = stepper.step(sim, t, np.float64(dt))
    pos = rod.position_collection
    drift = np.linalg.norm(pos[:, -1] - tip_before) * 1000
    if drift > 0.5:
        print(f"  WARNING: tip still moving ({drift:.2f} mm in last 10%) - run longer")
    return pos[0].copy(), pos[1].copy(), (kappa1, kappa2)

# ------------------------------------------------------- cases
cases = {
    "Straight (no actuation)": (0.00, 0.00),
    "C-shape (same side)":     (0.05, 0.05),
    "S-shape (opposite)":      (0.06, -0.06),
    "Tip-only bend":           (0.00, 0.08),
}

fig, axes = plt.subplots(2, 2, figsize=(11, 8))
axes = axes.ravel()
rows = []
for ax, (name, (e1, e2)) in zip(axes, cases.items()):
    xs, ys, (k1, k2) = simulate(e1, e2)
    xa, ya = pcc_shape([k1, k2], [L / 2, L / 2])
    tip_err = np.hypot(xs[-1] - xa[-1], ys[-1] - ya[-1]) * 1000
    # mean shape error: nearest-point distance from sim nodes to PCC curve
    dists = [np.min(np.hypot(xa - px, ya - py)) for px, py in zip(xs, ys)]
    shape_err = np.mean(dists) * 1000
    rows.append((name, e1, e2, k1, k2, xs[-1]*1000, ys[-1]*1000,
                 tip_err, shape_err))
    ax.plot(xa, ya, "k--", lw=2, label="Analytical (PCC)")
    ax.plot(xs, ys, "o-", ms=2.5, color="tab:green", label="PyElastica")
    ax.plot(xs[n_elem // 2], ys[n_elem // 2], "s", color="tab:red",
            label="segment joint")
    ax.set_title(f"{name}\nε1={e1:+.2f}, ε2={e2:+.2f}\ntip err {tip_err:.2f} mm",
                 fontsize=10)
    ax.set_aspect("equal"); ax.grid(alpha=.3)
    ax.set_xlabel("x [m]")
for a in axes: a.set_ylabel("y [m]")
axes[1].legend(fontsize=9, loc="upper left")
plt.tight_layout()
plt.savefig(FIG / "vine_shapes.png", dpi=150)

# ------------------------------------------------------- tip load sweep (EI matters)
loads = [0.0, 0.05, 0.1, 0.2]   # N
fig2, ax2 = plt.subplots(figsize=(6, 4.5))
defl = []
for F in loads:
    xs, ys, _ = simulate(0.0, 0.0, tip_force=F, final_time=30.0)
    ax2.plot(xs, ys, label=f"F = {F:.2f} N")
    defl.append(-ys[-1])
ax2.set_aspect("equal"); ax2.grid(alpha=.3); ax2.legend()
ax2.set_title(f"Unactuated cantilever, tip load (EI_eff = {EI_eff} N·m²)\n"
              "Mirror of experiment B0")
ax2.set_xlabel("x [m]"); ax2.set_ylabel("y [m]")
plt.tight_layout(); plt.savefig(FIG / "vine_tipload.png", dpi=150)

print(f"{'case':26s} {'k1':>6s} {'k2':>6s} {'tip x':>7s} {'tip y':>7s} "
      f"{'tip err':>8s} {'shape err':>9s}")
for r in rows:
    print(f"{r[0]:26s} {r[3]:6.2f} {r[4]:6.2f} {r[5]:7.1f} {r[6]:7.1f} "
          f"{r[7]:8.2f} {r[8]:9.2f}")
print("\nTip load sweep (small-deflection theory: delta = F L^3 / 3EI)")
for F, dsim in zip(loads, defl):
    print(f"F={F:.2f} N  sim={dsim*1000:7.1f} mm  linear={F*L**3/(3*EI_eff)*1000:7.1f} mm")

print("\nMesh convergence, S-shape tip error vs PCC")
for n in (35, 70, 140):
    xs, ys, (k1, k2) = simulate(0.06, -0.06, n_elem=n)
    xa, ya = pcc_shape([k1, k2], [L/2, L/2], n=4000)
    print(f"n_elem={n:4d}  tip err={np.hypot(xs[-1]-xa[-1], ys[-1]-ya[-1])*1000:6.2f} mm")

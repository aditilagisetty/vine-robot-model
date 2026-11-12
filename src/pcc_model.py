"""
Discretized PCC model: each segment is split into many short regions,
and every region is its own constant-curvature arc.

Step 1 (this file): every region in a segment gets the same curvature,
kappa = eps / d, so the shape must match the two-arc model exactly.
Later steps give each region its own curvature (same pressure instead of
same curvature, plus external loads), and nothing here needs to change
except how region_kappas is filled in.

Run:  python src/pcc_model.py   (instant; prints the check, writes a figure)
"""
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from pathlib import Path
from params import L, d, n_regions, SHAPE_CASES

FIG = Path(__file__).resolve().parent.parent / "figures"
FIG.mkdir(exist_ok=True)


def region_kappas(eps_per_segment, n_per_segment=n_regions):
    """Curvature of every region, base to tip. For now each region in a
    segment gets that segment's kappa = eps / d."""
    return np.repeat(np.asarray(eps_per_segment) / d, n_per_segment)


def chain_arcs(kappas, region_len):
    """Chain constant-curvature arcs end to end, starting at the origin along +x.
    Returns node x, y and heading theta (len(kappas) + 1 nodes)."""
    n = len(kappas)
    x, y, th = np.zeros(n + 1), np.zeros(n + 1), np.zeros(n + 1)
    for i, k in enumerate(kappas):
        dth = k * region_len
        # arc in its own frame: chord = region_len * sinc(dth/2), at half-angle
        chord = region_len * np.sinc(dth / (2 * np.pi))   # np.sinc(x) = sin(pi x)/(pi x)
        x[i + 1] = x[i] + chord * np.cos(th[i] + dth / 2)
        y[i + 1] = y[i] + chord * np.sin(th[i] + dth / 2)
        th[i + 1] = th[i] + dth
    return x, y, th


def vine_shape(eps_per_segment, n_per_segment=n_regions):
    """Node positions of the whole vine for the given segment strains."""
    n_seg = len(eps_per_segment)
    ell = L / n_seg
    return chain_arcs(region_kappas(eps_per_segment, n_per_segment),
                      ell / n_per_segment)


def two_arc_tip(k1, k2, ell=L / 2):
    """Closed-form tip of the original two-arc PCC model (hand_calcs.py)."""
    def arc(k):
        if abs(k) < 1e-12:
            return ell, 0.0, 0.0
        return np.sin(k * ell) / k, (1 - np.cos(k * ell)) / k, k * ell
    x1, y1, th1 = arc(k1)
    dx, dy, th2 = arc(k2)
    c, s = np.cos(th1), np.sin(th1)
    return x1 + c * dx - s * dy, y1 + s * dx + c * dy, th1 + th2


def two_arc_curve(k1, k2, ell=L / 2, n=400):
    """Dense centerline of the original two-arc model, from the closed-form
    arc equations (independent of chain_arcs), for plotting."""
    def arc(k, s):
        if abs(k) < 1e-12:
            return s, np.zeros_like(s)
        return np.sin(k * s) / k, (1 - np.cos(k * s)) / k
    s = np.linspace(0, ell, n)
    x1, y1 = arc(k1, s)
    dx, dy = arc(k2, s)
    th1 = k1 * ell
    c, sn = np.cos(th1), np.sin(th1)
    x2 = x1[-1] + c * dx - sn * dy
    y2 = y1[-1] + sn * dx + c * dy
    return np.concatenate([x1, x2]), np.concatenate([y1, y2])


if __name__ == "__main__":
    print(f"Check: {n_regions} regions/segment, same curvature in every region,")
    print("vs. the original two-arc PCC model\n")
    print(f"{'case':26s} {'tip x':>8s} {'tip y':>8s} {'two-arc x':>9s} "
          f"{'two-arc y':>9s} {'diff':>9s}")
    for name, (e1, e2) in SHAPE_CASES.items():
        x, y, th = vine_shape((e1, e2))
        X, Y, TH = two_arc_tip(e1 / d, e2 / d)
        diff = np.hypot(x[-1] - X, y[-1] - Y)
        print(f"{name:26s} {x[-1]*1000:8.2f} {y[-1]*1000:8.2f} {X*1000:9.2f} "
              f"{Y*1000:9.2f} {diff*1000:7.1e} mm")
        assert diff < 1e-9 and abs(th[-1] - TH) < 1e-9, name

    print("\nRegion count doesn't matter while curvature is uniform per segment:")
    e1, e2 = SHAPE_CASES["S-shape (opposite)"]
    X, Y, _ = two_arc_tip(e1 / d, e2 / d)
    for n in (1, 5, 35, 350):
        x, y, _ = vine_shape((e1, e2), n)
        print(f"  n_regions={n:4d}  tip diff = {np.hypot(x[-1]-X, y[-1]-Y)*1000:.1e} mm")

    # figure: discretized model overlaid on the original two-arc model
    fig, axes = plt.subplots(2, 2, figsize=(11, 8))
    for ax, (name, (e1, e2)) in zip(axes.ravel(), SHAPE_CASES.items()):
        x, y, _ = vine_shape((e1, e2))
        xa, ya = two_arc_curve(e1 / d, e2 / d)
        diff = np.hypot(x[-1] - xa[-1], y[-1] - ya[-1]) * 1000
        ax.plot(xa, ya, "k--", lw=2, label="Two-arc PCC (original)")
        ax.plot(x, y, "o", ms=3, color="tab:blue",
                label=f"Discretized PCC ({n_regions} regions/segment)")
        ax.plot(x[n_regions], y[n_regions], "s", color="tab:red", label="segment joint")
        ax.set_title(f"{name}\nε1={e1:+.2f}, ε2={e2:+.2f}\ntip diff {diff:.1e} mm",
                     fontsize=10)
        ax.set_aspect("equal"); ax.grid(alpha=.3)
        ax.set_xlabel("x [m]"); ax.set_ylabel("y [m]")
    axes[0, 1].legend(fontsize=9, loc="upper left")
    plt.tight_layout()
    plt.savefig(FIG / "pcc_regions.png", dpi=150)
    print(f"\nwrote {FIG / 'pcc_regions.png'}")

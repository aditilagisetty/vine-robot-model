"""Draws the two geometry sketches used in docs/hand_calculations.md."""
import numpy as np, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from pathlib import Path
FIG = Path(__file__).resolve().parent.parent / "figures"; FIG.mkdir(exist_ok=True)

fig, (a, b) = plt.subplots(1, 2, figsize=(12, 5))

# --- (a) kappa = eps / d : bent element, outer side unchanged, inner side shortened
R, d, th = 2.0, 0.6, 0.55
t = np.linspace(-th/2, th/2, 100) + np.pi/2
for rad, sty, lab in [(R + d/2, "-", "outer wall (no sPAM): length ℓ"),
                      (R,       "--", "centerline"),
                      (R - d/2, "-", "inner wall (sPAM side): length (1−ε)ℓ")]:
    a.plot(rad*np.cos(t), rad*np.sin(t), sty, lw=2.5 if sty=="-" else 1.2,
           color="tab:red" if rad < R else ("k" if rad > R else "gray"), label=lab)
for e in (t[0], t[-1]):
    a.plot([0, (R+d/2)*np.cos(e)], [0, (R+d/2)*np.sin(e)], ":", color="gray")
a.annotate("", xy=((R+d/2)*np.cos(t[0]), (R+d/2)*np.sin(t[0])),
           xytext=((R-d/2)*np.cos(t[0]), (R-d/2)*np.sin(t[0])),
           arrowprops=dict(arrowstyle="<->"))
a.text((R)*np.cos(t[0])+0.08, R*np.sin(t[0])-0.05, "d", fontsize=13)
a.text(0.05, 0.9, "θ", fontsize=13); a.plot(0, 0, "ko")
a.text(-0.35, 1.05, "R = 1/κ", fontsize=12, rotation=78)
a.set_title("(a) one-sided strain → curvature\nℓ = (R + d/2)θ,  (1−ε)ℓ = (R − d/2)θ  ⇒  κ ≈ ε/d")
a.set_aspect("equal"); a.axis("off"); a.legend(loc="lower center", fontsize=9)
a.set_ylim(-0.6, 2.6)

# --- (b) two-segment PCC chaining (S-shape)
ell = 0.35
def arc_pts(k, th0, x0, y0, n=60):
    s = np.linspace(0, ell, n); th = th0 + k*s
    if k == 0: return x0 + s*np.cos(th0), y0 + s*np.sin(th0), th
    return x0 + (np.sin(th)-np.sin(th0))/k, y0 - (np.cos(th)-np.cos(th0))/k, th
x1, y1, th1 = arc_pts(1.2, 0, 0, 0)
x2, y2, th2 = arc_pts(-1.2, th1[-1], x1[-1], y1[-1])
b.plot(x1, y1, lw=3, color="tab:blue", label="segment 1: κ₁ = +1.2 1/m")
b.plot(x2, y2, lw=3, color="tab:orange", label="segment 2: κ₂ = −1.2 1/m")
b.plot([0], [0], "ks"); b.text(0, -0.015, "base (0,0)", va="top")
b.plot(x1[-1], y1[-1], "ko")
b.text(x1[-1], y1[-1]-0.015, f"joint\n({x1[-1]:.3f}, {y1[-1]:.3f})\nheading θ₁ = κ₁ℓ = 0.42 rad",
       va="top", ha="center", fontsize=9)
b.plot(x2[-1], y2[-1], "k*", ms=14)
b.text(x2[-1], y2[-1]+0.012, f"tip ({x2[-1]:.3f}, {y2[-1]:.3f})", ha="right")
L = 0.08
b.annotate("", xy=(x1[-1]+L*np.cos(th1[-1]), y1[-1]+L*np.sin(th1[-1])),
           xytext=(x1[-1], y1[-1]), arrowprops=dict(arrowstyle="->", color="gray"))
b.set_title("(b) chaining arcs: rotate segment 2 by θ₁, then add the joint position")
b.set_aspect("equal"); b.grid(alpha=.3); b.legend(loc="upper left", fontsize=9)
b.set_xlabel("x [m]"); b.set_ylabel("y [m]"); b.set_ylim(-0.08, 0.22)
plt.tight_layout(); plt.savefig(FIG / "hand_calc_geometry.png", dpi=150)

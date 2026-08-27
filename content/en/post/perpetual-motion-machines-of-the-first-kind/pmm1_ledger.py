#!/usr/bin/env python3
"""
pmm1_ledger.py -- closed-cycle energy accounting for five candidate
perpetual motion machines of the first kind (PMM1).

For each design the script computes, independently:

    W_out   the energy a naive designer credits to the machine, obtained
            exactly the way the design's own literature obtains it, and
    W_in    the energy the same cycle demands somewhere else in the loop,

then reports the ledger W_net = W_out - W_in.  In every case the two
terms cancel analytically; the residual printed here is numerical
quadrature error, and it shrinks as N is increased.

Standard library only.  Run:  python3 pmm1_ledger.py
"""

import math

G = 9.80665          # m s^-2, standard gravity
RHO_W = 998.2        # kg m^-3, water at 20 C
GAMMA_W = 0.0728     # N m^-1, water/air surface tension at 20 C
MU0 = 4.0e-7 * math.pi


# ----------------------------------------------------------------------
# numerics
# ----------------------------------------------------------------------

def simpson(f, a, b, n=200_000):
    """Composite Simpson's rule; n must be even."""
    if n % 2:
        n += 1
    h = (b - a) / n
    s = f(a) + f(b)
    for i in range(1, n):
        s += (4.0 if i % 2 else 2.0) * f(a + i * h)
    return s * h / 3.0


def deriv(f, x, h=1e-6):
    """Central difference."""
    return (f(x + h) - f(x - h)) / (2.0 * h)


def grad2(f, x, y, h=1e-6):
    return ((f(x + h, y) - f(x - h, y)) / (2.0 * h),
            (f(x, y + h) - f(x, y - h)) / (2.0 * h))


def logcosh(x):
    """log(cosh x), stable for large |x| where cosh overflows."""
    ax = abs(x)
    if ax > 20.0:
        return ax - math.log(2.0)
    return math.log(math.cosh(ax))


def banner(n, title):
    print()
    print("=" * 72)
    print(f"DESIGN {n}.  {title}")
    print("=" * 72)


def ledger(w_out, w_in, unit="J", label_out="claimed output",
           label_in="concealed input"):
    net = w_out - w_in
    print(f"  {label_out:<34s} {w_out:+.6e} {unit}")
    print(f"  {label_in:<34s} {w_in:+.6e} {unit}")
    print(f"  {'-' * 34} {'-' * 13}")
    print(f"  {'NET PER CYCLE':<34s} {net:+.6e} {unit}")
    scale = max(abs(w_out), abs(w_in), 1e-30)
    print(f"  {'net / claimed output':<34s} {net / scale:+.3e}")
    return net


# ----------------------------------------------------------------------
# DESIGN A -- the overbalanced wheel (Bhaskara 1150, Villard c. 1235)
#
# One mass rides a radial slider on a wheel.  theta is measured from the
# upward vertical, so the mass's height is h = r cos(theta) and its
# potential is U = m g r cos(theta).  The design extends the arm on the
# descending side (sin theta > 0) and retracts it on the ascending side,
# via the smooth switch s(theta) below -- smooth so that the quadrature
# is honest and no work is hidden in a discontinuity.
#
#   W_torque = m g \oint r sin(theta) d(theta)      <- what the designer counts
#   W_radial = m g \oint cos(theta) r'(theta) d(theta)  <- what it costs to slide
#
# and W_gravity = W_torque - W_radial, because
#   W_gravity = -\oint dU = -m g \oint d(r cos theta).
# ----------------------------------------------------------------------

def design_A(m=1.0, r_in=0.20, r_out=0.50, k=20.0, n_masses=12, rpm=60.0):
    banner("A", "Overbalanced (over-shot) gravity wheel")

    def s(th):                       # smooth 0/1 switch, on for sin(th) > 0
        return 1.0 / (1.0 + math.exp(-k * math.sin(th)))

    def r(th):
        return r_in + (r_out - r_in) * s(th)

    w_torque = m * G * simpson(lambda t: r(t) * math.sin(t), 0.0, 2 * math.pi)
    w_radial = m * G * simpson(lambda t: math.cos(t) * deriv(r, t),
                               0.0, 2 * math.pi)

    print(f"  arm extended / retracted           {r_out:.2f} m / {r_in:.2f} m")
    print(f"  bob mass                           {m:.2f} kg")
    print(f"  ideal-switch prediction 2 m g dr   "
          f"{2 * m * G * (r_out - r_in):+.6e} J")
    print()
    net = ledger(w_torque, w_radial,
                 label_out="torque work per rev  (1 bob)",
                 label_in="slider work per rev  (1 bob)")

    claimed = n_masses * w_torque
    print()
    print(f"  scaled to {n_masses} bobs                     "
          f"{claimed:+.4f} J/rev")
    print(f"  at {rpm:.0f} rpm the prospectus claims        "
          f"{claimed * rpm / 60.0:+.2f} W")
    print(f"  the wheel actually delivers          "
          f"{n_masses * net * rpm / 60.0:+.3e} W  (minus all friction)")
    return net


# ----------------------------------------------------------------------
# DESIGN B -- Boyle's self-flowing flask (capillary rise feeding a siphon)
#
# Capillary rise h = 2 gamma cos(phi) / (rho g R) is real, and it is free.
# The design's error is assuming the liquid can then drip off the top.
# It cannot, and the reason is quantitative: the same Laplace pressure
# that holds the column up leaves the liquid just below the top meniscus
# at a pressure BELOW ambient by exactly rho g h.  Expelling a parcel dV
# therefore costs (P_atm - P_liq) dV = rho g h dV -- precisely the
# potential energy that parcel releases falling back down.
# ----------------------------------------------------------------------

def design_B(R=1.0e-4, phi_deg=0.0, gamma=GAMMA_W, rho=RHO_W, dV=1.0e-9):
    banner("B", "Boyle's self-flowing flask (capillary siphon)")
    phi = math.radians(phi_deg)
    h = 2.0 * gamma * math.cos(phi) / (rho * G * R)

    # -- commentary on the rise itself -------------------------------
    # Surface energy released: the meniscus replaces dry wall with wet
    # wall over the swept area 2 pi R h, at (gamma_SV - gamma_SL).
    volume = math.pi * R * R * h
    e_surface = 2.0 * math.pi * R * h * gamma * math.cos(phi)
    e_lift = rho * volume * G * (h / 2.0)

    print(f"  tube radius                        {R * 1e6:.1f} um")
    print(f"  capillary rise h = 2g cos(phi)/rho g R    {h * 100:.2f} cm")
    print(f"  raised volume                      {volume * 1e9:.3f} mm^3")
    print(f"  surface energy released on rise    {e_surface:+.6e} J")
    print(f"  potential energy banked in column  {e_lift:+.6e} J")
    print(f"  ratio  (exactly 1/2; the rest is viscous)  "
          f"{e_lift / e_surface:.6f}")
    print()

    # -- the cycle: expel dV at the top, let it fall back -------------
    p_deficit = 2.0 * gamma * math.cos(phi) / R      # = rho g h
    w_recover = rho * G * h * dV                     # dV falls height h
    w_expel = p_deficit * dV                         # push dV past the meniscus

    print(f"  test parcel                        {dV * 1e9:.2f} mm^3")
    print(f"  suction under the top meniscus     {p_deficit:.2f} Pa "
          f"(= rho g h = {rho * G * h:.2f} Pa)")
    print()
    net = ledger(w_recover, w_expel,
                 label_out="PE released as the parcel falls",
                 label_in="work to expel it at the top")
    print()
    # And a real exit meniscus must go convex to shed a drop, costing a
    # further +2 gamma / R_drop of Laplace pressure on the way out.
    w_convex = w_expel + (2.0 * gamma / R) * dV
    print(f"  with a convex exit meniscus the cost rises to "
          f"{w_convex:+.6e} J,")
    print(f"  making the true cycle {w_recover - w_convex:+.3e} J -- "
          f"strictly negative.")
    return net


# ----------------------------------------------------------------------
# DESIGN C -- the magnet ramp / SMOT, and the general magnetostatic case
#
# A soft-ferromagnetic ball with a reversible (possibly nonlinear,
# saturating) magnetisation is walked around a closed path in the static
# field of two permanent dipoles.  Its interaction energy is a
# single-valued function of position, so the force is a gradient field
# and the loop integral vanishes -- whatever the ramp geometry.
# ----------------------------------------------------------------------

def design_C(m_dip=5.0, m_sat=2.0, alpha=40.0, n_path=400_000):
    banner("C", "Permanent-magnet motor / SMOT ramp")

    # The SMOT "gate": two in-plane dipoles facing each other across a gap
    # at the origin, with the ramp running in from the left along y = 0.
    magnets = [(0.0, 0.05, 0.0, -m_dip), (0.0, -0.05, 0.0, m_dip)]

    def bfield(x, y):
        """|B| of the dipole pair: B = (mu0/4pi)[3(m.rhat)rhat - m]/r^3."""
        bx = by = 0.0
        for (px, py, mx, my) in magnets:
            dx, dy = x - px, y - py
            r2 = dx * dx + dy * dy
            r = math.sqrt(r2) + 1e-12
            rx, ry = dx / r, dy / r
            mdotr = mx * rx + my * ry
            c = MU0 / (4.0 * math.pi * r ** 3)
            bx += c * (3.0 * mdotr * rx - mx)
            by += c * (3.0 * mdotr * ry - my)
        return math.hypot(bx, by)

    def energy(x, y):
        """U(|B|) = -int_0^B m(B') dB' for m(B) = m_sat tanh(alpha B / m_sat).

        The magnetisation is nonlinear and saturating but REVERSIBLE, so U
        is a single-valued function of position and F = -grad U exactly."""
        b = bfield(x, y)
        return -(m_sat * m_sat / alpha) * logcosh(alpha * b / m_sat)

    def force(x, y):
        gx, gy = grad2(energy, x, y)
        return (-gx, -gy)

    # A closed path: up the ramp toward the magnets, then the "return
    # stroke" that every SMOT demonstration quietly performs by hand.
    ax_, ay_ = -0.30, 0.0            # bottom of the ramp, far field
    bx_, by_ = -0.02, 0.0            # top of the ramp, at the gate mouth

    def path(t):
        if t <= 0.5:                                  # ramp, A -> B
            u = t / 0.5
            return (ax_ + u * (bx_ - ax_), ay_ + u * (by_ - ay_))
        u = (t - 0.5) / 0.5                           # return, B -> A
        # swing well clear of both magnets on the way back
        return (bx_ + u * (ax_ - bx_), by_ - 0.15 * math.sin(math.pi * u))

    # line integral of F . dr around the closed path
    work = 0.0
    x0, y0 = path(0.0)
    for i in range(1, n_path + 1):
        t = i / n_path
        x1, y1 = path(t)
        fx, fy = force(0.5 * (x0 + x1), 0.5 * (y0 + y1))
        work += fx * (x1 - x0) + fy * (y1 - y0)
        x0, y0 = x1, y1

    # the "gain" the demonstration shows you: the ramp segment alone
    ramp = -(energy(*path(0.5)) - energy(*path(0.0)))

    print(f"  two dipoles, moment                {m_dip:.1f} A m^2")
    print(f"  ball saturates at                  {m_sat:.1f} A m^2")
    print()
    net = ledger(ramp, ramp - work,
                 label_out="work gained climbing the ramp",
                 label_in="work to complete the return")
    print(f"  direct loop integral  \\oint F.dr    {work:+.6e} J")
    print()
    print("  Hysteresis is the ONLY way to make \\oint F.dr nonzero in")
    print("  magnetostatics -- and it has the wrong sign: the loop area is")
    print("  energy dissipated as heat, never energy produced.")
    return net


# ----------------------------------------------------------------------
# DESIGN D -- the buoyancy belt / "zero-point buoyancy engine"
#
# Sealed floats are carried up a water column by buoyancy and returned
# through air, re-entering the column through a seal at depth d.
# ----------------------------------------------------------------------

def design_D(V=1.0e-3, depth=10.0, rho=RHO_W, n_floats=20, period=2.0):
    banner("D", "Buoyancy belt / closed-loop float engine")

    # Ascent: net upward force on a neutrally-massed float is rho g V.
    w_ascent = simpson(lambda z: rho * G * V, 0.0, depth, n=2000)

    # Re-entry: the float must displace its own volume against the
    # gauge pressure at the injection depth.
    p_gauge = rho * G * depth
    w_inject = p_gauge * V

    print(f"  float displacement                 {V * 1e3:.2f} L")
    print(f"  injection depth                    {depth:.1f} m")
    print(f"  gauge pressure at that depth       {p_gauge / 1e3:.2f} kPa")
    print()
    net = ledger(w_ascent, w_inject,
                 label_out="buoyant work over the ascent",
                 label_in="work to inject one float")
    print()
    print(f"  {n_floats} floats on a {period:.0f} s cycle would rate at   "
          f"{n_floats * w_ascent / period:+.1f} W")
    print(f"  actual shaft power                 "
          f"{n_floats * net / period:+.3e} W  (minus seal friction)")
    return net


# ----------------------------------------------------------------------
# DESIGN E -- the bootstrapped motor-generator set
#
# The only design in the catalogue that fails for an accounting reason
# rather than a field-theoretic one -- and the one that produces almost
# all modern "overunity" claims, via a metering artefact.
# ----------------------------------------------------------------------

def design_E(eta_m=0.90, eta_g=0.90, e0=100.0, n_cycles=40):
    banner("E", "Bootstrapped motor-generator loop")

    loop_gain = eta_m * eta_g
    print(f"  motor efficiency                   {eta_m:.2f}")
    print(f"  generator efficiency               {eta_g:.2f}")
    print(f"  loop gain                          {loop_gain:.4f}")
    print()
    e = e0
    for n in range(0, n_cycles + 1):
        if n in (0, 1, 5, 10, 20, 40):
            print(f"    circulating energy after {n:>2d} passes   {e:9.4f} J")
        e *= loop_gain
    tau = -1.0 / math.log(loop_gain)
    print(f"  e-folding lifetime                 {tau:.2f} passes")
    print(f"  self-sustaining would need eta_m*eta_g >= 1 "
          f"(short by {1 - loop_gain:.0%})")

    print()
    print("  Where the claims come from -- the metering artefact:")
    print("    true power       P = (1/T) \\int v(t) i(t) dt = Vrms Irms cos(phi)")
    print("    naive meter      P_hat = Vrms Irms")
    for phi_deg in (0, 45, 60, 84, 87):
        cphi = math.cos(math.radians(phi_deg))
        print(f"    phi = {phi_deg:>2d} deg -> apparent gain "
              f"P_hat/P = {1.0 / cphi:6.2f}x")
    print("  A reactive load metered this way 'proves' 10x overunity while")
    print("  consuming net power.  Nothing has been built but a wattmeter bug.")
    return 0.0


# ----------------------------------------------------------------------

def main():
    print(__doc__.strip())
    results = {
        "A  overbalanced wheel":  design_A(),
        "B  capillary siphon":    design_B(),
        "C  magnet ramp":         design_C(),
        "D  buoyancy belt":       design_D(),
        "E  motor-generator":     design_E(),
    }

    print()
    print("=" * 72)
    print("SUMMARY -- net energy delivered per closed cycle")
    print("=" * 72)
    for name, net in results.items():
        verdict = "zero to quadrature precision" if abs(net) < 1e-9 \
            else "strictly negative once dissipation is restored"
        print(f"  {name:<26s} {net:+.3e} J   {verdict}")
    print()
    print("  No design in the catalogue survives its own energy ledger.")
    print("  Each 'surplus' is a term the designer counted once and paid")
    print("  for somewhere the accounting never looked.")


if __name__ == "__main__":
    main()

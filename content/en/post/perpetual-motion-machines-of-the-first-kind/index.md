---
title: "Perpetual Motion Machines of the First Kind: A Design Catalogue, a No-Go Theorem, and a Closed-Cycle Audit Protocol"
subtitle: "Five machines are specified in full engineering detail, and each one is then destroyed by its own energy ledger."

summary: "A perpetual motion machine of the first kind cannot be built. This report takes the design brief seriously anyway: it specifies five classical PMM1 candidates to the level of dimensioned parameters, computes what each is claimed to deliver, and locates the exact compensating term that cancels it. A single no-go theorem covers the whole class, a companion script verifies every ledger numerically, and an audit protocol is given for evaluating future claims."

authors:
  - admin

date: '2026-08-27T00:00:00Z'
lastmod: '2026-08-27T00:00:00Z'

draft: false
featured: false

math: true

tags:
  - Thermodynamics
  - Energy Conservation
  - Classical Mechanics
  - Research Methods

categories:
  - Report

image:
  caption: ''
  focal_point: ''
  placement: 2
  preview_only: false

projects: []
---

## Abstract

A perpetual motion machine of the first kind (PMM1) is a device that delivers
net positive work over a closed thermodynamic cycle while receiving no energy
input. No such device can exist, and the obstruction is not a limitation of
materials, precision, or ingenuity — it is the first law of thermodynamics,
which is in turn a consequence of the time-translation invariance of physical
law. This report nevertheless treats the design brief as a serious engineering
exercise. Five canonical PMM1 architectures are specified to the level of
dimensioned parameters: an overbalanced gravity wheel, a capillary self-flowing
flask, a permanent-magnet ramp, a buoyancy belt, and a bootstrapped
motor–generator set. For each, the report computes the output its own design
literature claims, then identifies and evaluates the compensating term that
cancels it exactly. A single no-go theorem is proved that subsumes all five
mechanical cases. Every ledger is verified numerically by an accompanying
standard-library Python program, which finds net cycle work of order
$10^{-10}\,$J or smaller against claimed outputs of order $10^{1}$–$10^{2}\,$J —
i.e. zero to quadrature precision. The report closes with a practical audit
protocol for evaluating claimed overunity devices, and with an honest account of
the one regime — cosmological spacetime — in which energy conservation genuinely
fails, together with a quantitative demonstration that the failure is
approximately 36 orders of magnitude too small to harvest.

**Design verdict: infeasible. The obstruction is fundamental, not technical.**

---

## 1. Introduction and taxonomy

The literature distinguishes three classes of impossible engine, and confusing
them is the single most common error in the field.

| Class | Violates | Informal statement |
|---|---|---|
| **PMM1** | First law | Produces work from nothing. |
| **PMM2** | Second law | Converts heat from a single reservoir wholly into work. |
| **PMM3** | — (idealisation) | Runs forever without output, i.e. zero dissipation. |

This report concerns **PMM1 only**. The distinction matters because PMM2
proposals (Maxwell's demon, the Brownian ratchet, Zhang-type thermal
rectifiers) fail for subtle, information-theoretic reasons that took a century
to formalise, whereas PMM1 proposals fail for reasons that can be settled with a
line integral. A PMM1 is the *easier* impossibility, and correspondingly the
older one: it has been recognised as hopeless since at least the French Académie
des Sciences' 1775 resolution to stop reading submissions.

The persistence of PMM1 designs across nine centuries is therefore not a
physics puzzle but an *accounting* puzzle. Every design in Section 4 is
internally plausible to its author because the author computed one term of a
two-term ledger. The purpose of this report is to make the second term explicit
in each case.

### 1.1 Scope and what "design" can mean here

Since a working PMM1 cannot be delivered, the deliverable is redefined as
follows, and this is stated plainly rather than elided:

1. **Specification** of each candidate at the level of real dimensioned
   parameters, sufficient that a machinist could build it.
2. **Prediction** of the output using the design's own reasoning.
3. **Localisation** of the cancelling term — not merely the assertion that one
   exists.
4. **Verification** that the cancellation is exact, numerically and
   symbolically.

Item 3 is the substance. "It violates conservation of energy" is a true but
useless response to a specific mechanism; the useful response names the bolt
where the energy goes.

---

## 2. Formal statement of the design target

Let a machine occupy a region $\Omega$ with a well-defined boundary
$\partial\Omega$. Over one operating cycle, the first law reads

$$
\Delta U_{\text{int}} \;=\; Q_{\text{in}} \;-\; W_{\text{out}},
$$

where $U_{\text{int}}$ is the total internal energy of everything inside
$\partial\Omega$. A cycle requires the machine to return to its initial
thermodynamic state, so

$$
\oint \mathrm{d}U_{\text{int}} = 0
\qquad\Longrightarrow\qquad
W_{\text{out}} = Q_{\text{in}}.
$$

**Design target (PMM1).** Construct a device satisfying

$$
W_{\text{out}} > 0
\quad\text{with}\quad
Q_{\text{in}} = 0
\quad\text{and}\quad
\oint \mathrm{d}U_{\text{int}} = 0 .
$$

These three conditions are jointly contradictory: the first two force
$\oint \mathrm{d}U_{\text{int}} = -W_{\text{out}} < 0$, contradicting the third.
The specification is inconsistent, and no amount of mechanism will satisfy it.

This is correct but shallow — it merely restates the first law as an axiom. The
substantive question is *why* the first law holds, and that is Section 3.3.

---

## 3. Three independent proofs of impossibility

### 3.1 The master theorem for mechanical PMM1

Almost every historical PMM1 is a mechanism moving in a static force field.
The following theorem disposes of the entire class at once.

> **Theorem.** Let a machine be described by generalised coordinates
> $q \in \mathbb{R}^n$ subject to time-independent holonomic constraints, acted
> on by forces derivable from a potential $U(q)$ together with dissipative
> forces $F_{\text{d}}$ satisfying $F_{\text{d}} \cdot \dot q \le 0$. Let the
> machine execute a steady cycle: $q(T) = q(0)$ and $\dot q(T) = \dot q(0)$.
> Then the net work delivered to an external load over one cycle is
> $$ W_{\text{out}} = -D, \qquad D \equiv -\int_0^T F_{\text{d}}\cdot\dot q\,\mathrm{d}t \;\ge\; 0. $$

*Proof.* The work–energy theorem over $[0,T]$ gives
$\Delta K = W_{\text{field}} + W_{\text{ext}} + W_{\text{d}}$. Because the cycle
is steady, $\Delta K = 0$. Because $U$ is a single-valued function of $q$ and
the path closes, $W_{\text{field}} = -\oint \mathrm{d}U = 0$. Writing
$W_{\text{d}} = -D$ and $W_{\text{out}} = -W_{\text{ext}}$ yields
$W_{\text{out}} = -D \le 0$. $\;\blacksquare$

The theorem says something stronger than "no free energy": it says every such
machine is a *net consumer*, with equality only in the unattainable
frictionless limit. Note precisely which hypotheses do the work:

- **Single-valued $U$.** This is what "conservative field" means, and it is what
  makes $\oint \mathrm{d}U = 0$. Gravity, electrostatics, and the magnetostatic
  force on a body with reversible magnetisation all qualify.
- **Closed path.** The cycle must close *in the full configuration space*,
  including internal degrees of freedom — every arm position, valve state, and
  latch. Designs in Section 4 fail precisely by closing the visible loop while
  leaving an internal coordinate open, and paying for it off the books.
- **Time-independent constraints.** A time-varying constraint is an actuator,
  and an actuator has a power supply.

### 3.2 The two escape hatches, and why both are closed

A prospective designer must break one of the hypotheses. There are exactly two
candidates.

**(i) Use a non-conservative force field,** i.e. one with $\nabla \times F \neq
0$, so that $\oint F\cdot\mathrm{d}r > 0$. In electromagnetism this is not
merely allowed but routine — Faraday's law gives

$$
\oint_{C} E \cdot \mathrm{d}\ell \;=\; -\frac{\mathrm{d}\Phi_B}{\mathrm{d}t}.
$$

The circulation is nonzero if and only if the magnetic flux is *changing*, which
requires an agent doing work to change it. This is the transformer principle,
and it is a description of energy transfer, not energy creation. In the static
case $\nabla \times E = 0$ and the hatch closes. Magnetic forces on moving
charges close it independently: $F = qv \times B$ is everywhere perpendicular to
$v$, so a static magnetic field does no work on a charge at all.

**(ii) Make the potential time-dependent,** $U = U(q,t)$. Then indeed
$\oint \mathrm{d}U \neq 0$ in general. But for a Hamiltonian system

$$
\frac{\mathrm{d}H}{\mathrm{d}t} \;=\; \frac{\partial H}{\partial t},
$$

so energy is non-conserved exactly to the extent that something outside the
system is modulating it — again, a source. The hatch relabels the energy input;
it does not remove it.

### 3.3 The deep reason: Noether's theorem

The first law is not a postulate about steam engines. It is a corollary of a
symmetry. Noether's theorem states that every continuous symmetry of the action
yields a conserved current; invariance under time translation
$t \mapsto t + \varepsilon$ yields conservation of energy.

Therefore:

> **A PMM1 is possible if and only if the laws of physics change with time.**

This converts an engineering question into a measurable one, and the
measurements have been done. Comparisons of optical atomic clocks bound the
fractional drift of the fine-structure constant at the level of
$|\dot\alpha/\alpha| \lesssim 10^{-17}\ \text{yr}^{-1}$, with independent and
comparable bounds from the Oklo natural fission reactor and from quasar
absorption spectra. Even granting a nonzero drift at the very top of the allowed
band, the fractional energy non-conservation available to a machine over a year
of operation is of order $10^{-17}$. A device dissipating $1\,$kW would harvest
roughly $10^{-14}\,$W from it. This is not an engineering margin; it is nine
orders of magnitude below the thermal noise of the apparatus measuring it.

---

## 4. Design catalogue

Each design below is specified, costed, and audited. Symbols: $W_{\text{claim}}$
is the output computed by the design's own argument; $W_{\text{hidden}}$ is the
compensating term; $W_{\text{net}}$ is their difference.

### 4.1 Design A — the overbalanced gravity wheel

**Provenance.** Bhāskara II, *Siddhānta Śiromani*, c. 1150; Villard de
Honnecourt, c. 1235; and roughly half of all subsequent proposals.

**Specification.** A wheel of radius $0.50\,$m carries $N = 12$ bobs of
$m = 1\,$kg, each on a radial slider. A cam extends each slider to
$r_{\text{out}} = 0.50\,$m on the descending side and retracts it to
$r_{\text{in}} = 0.20\,$m on the ascending side. Let $\theta$ be measured from
the upward vertical, so a bob's height is $h = r\cos\theta$ and its potential is
$U = mgr\cos\theta$. The extension schedule is the smooth switch
$s(\theta) = \left[1 + e^{-k\sin\theta}\right]^{-1}$ with $k = 20$, so that
$r(\theta) = r_{\text{in}} + (r_{\text{out}}-r_{\text{in}})\,s(\theta)$. The
switch is smoothed deliberately: a discontinuous cam would hide work in an
impulse, and the design deserves a fair hearing.

**The claim.** The designer computes torque about the axle,
$\tau = mgr(\theta)\sin\theta$, and integrates over a revolution:

$$
W_{\text{claim}} = mg\oint r(\theta)\sin\theta\,\mathrm{d}\theta
\;\longrightarrow\; 2mg\,(r_{\text{out}} - r_{\text{in}}) \;=\; 5.88\ \text{J}
$$

per bob per revolution, in the sharp-switch limit. The descending side has more
leverage than the ascending side; the wheel is permanently out of balance; it
must turn. Scaled to 12 bobs at 60 rpm this is a prospectus figure of
$\mathbf{70.3\ W}$.

**The audit.** The torque integral is not the whole work done by gravity. Since
$U = mgr\cos\theta$,

$$
W_{\text{grav}} = -\oint \mathrm{d}U = -mg\oint \mathrm{d}(r\cos\theta)
= mg\oint r\sin\theta\,\mathrm{d}\theta
\;-\; mg\oint \cos\theta \, \frac{\mathrm{d}r}{\mathrm{d}\theta}\,\mathrm{d}\theta .
$$

The first term is the torque work $W_{\text{claim}}$ computed above. The second
is the **slider work** $W_{\text{hidden}}$ — the work the cam must do to move
the bob radially — and it has been omitted from every version of this design
since 1150.

Evaluate the slider work in the
sharp-switch limit: the slider extends at the top ($\theta = 0$, $\cos\theta =
+1$, $\mathrm{d}r = +\Delta r$) and retracts at the bottom ($\theta = \pi$,
$\cos\theta = -1$, $\mathrm{d}r = -\Delta r$). Both transitions contribute
$+\Delta r$, so

$$
W_{\text{hidden}} = 2mg\,(r_{\text{out}} - r_{\text{in}}) = W_{\text{claim}} .
$$

The cancellation is exact and it is *identically* exact — not approximately, not
for this choice of parameters, but for any $r(\theta)$ whatsoever, because both
terms are pieces of the same closed line integral of a conservative field.

The physical reading is worth stating, because it is the thing the design
literature never sees: **extending the arm at the top lifts the bob, and
retracting it at the bottom also lifts the bob** (inward is upward, down there).
The cam must therefore perform two lifts of $mg\Delta r$ per revolution, which
is precisely the leverage surplus the wheel appears to gain.

$$
\boxed{W_{\text{net}} = 0 \ \text{exactly; } -6.1\times10^{-10}\ \text{J numerically}}
$$

### 4.2 Design B — Boyle's self-flowing flask

**Provenance.** Attributed to Robert Boyle, 17th century; still circulating.

**Specification.** A capillary of radius $R = 100\,\mu$m dips into a water
reservoir at $20\,^{\circ}$C ($\gamma = 0.0728\,$N m⁻¹, $\rho = 998.2\,$kg m⁻³,
contact angle $\phi = 0$). Water rises to

$$
h = \frac{2\gamma\cos\phi}{\rho g R} = 14.87\ \text{cm},
$$

whereupon it is to spill over the lip and fall back into the reservoir, turning
a wheel on the way down.

**The claim.** The rise is genuinely free — it is driven by surface energy, not
by the operator. The design therefore appears to obtain a $14.87\,$cm head at no
cost, indefinitely.

**The audit.** The rise is real; the *spill* is not. Two facts settle it.

First, the energy bookkeeping of the rise itself. The meniscus converts dry wall
to wet wall over an area $2\pi R h$, releasing
$E_{\text{surf}} = 2\pi R h\gamma\cos\phi = 6.80\,\mu$J, while the raised column
banks only $E_{\text{PE}} = \rho g (\pi R^2 h)(h/2) = 3.40\,\mu$J. The ratio is
exactly $1/2$; the remaining half is dissipated viscously during the rise. So
even the free lift arrives at 50% efficiency, and none of it is recoverable
without lowering the water again.

Second — and decisively — the same Laplace pressure that holds the column up
leaves the liquid just beneath the top meniscus at a pressure *below* ambient by

$$
\Delta P = \frac{2\gamma\cos\phi}{R} = 1456\ \text{Pa} = \rho g h .
$$

The column does not spill because it is being *sucked upward*; it is in
mechanical equilibrium, not on the verge of overflowing. To expel a parcel
$\mathrm{d}V$ past the lip one must supply $\Delta P\,\mathrm{d}V = \rho g
h\,\mathrm{d}V$ — exactly the potential energy that parcel will release on the
way back down. And a real exit meniscus must bulge convex to shed a drop,
reversing the sign of the Laplace term and roughly doubling the cost.

$$
\boxed{W_{\text{net}} = 0 \ \text{at the ideal lip}; \ -1.46\ \mu\text{J per mm}^3 \ \text{with a real one}}
$$

### 4.3 Design C — the permanent-magnet ramp (SMOT)

**Provenance.** The Simple Magnetic Overunity Toy and its many descendants,
including the Perendev motor.

**Specification.** Two NdFeB magnets, modelled as in-plane point dipoles of
moment $5\,$A m² at $(0, \pm 5)\,$cm, form a gate at the origin. A
soft-ferromagnetic ball with saturating but **reversible** magnetisation
$m(B) = m_{\text{sat}}\tanh(\alpha B/m_{\text{sat}})$, $m_{\text{sat}} = 2\,$A m²,
rolls up a ramp from $(-30, 0)\,$cm to the gate mouth at $(-2, 0)\,$cm.

**The claim.** The ball accelerates up the ramp, gaining
$W_{\text{claim}} = 8.75\times10^{-4}\,$J. Videos of the device end here.

**The audit.** The interaction energy of a body with reversible magnetisation in
a static field is

$$
U(r) = -\int_0^{B(r)} m(B')\,\mathrm{d}B'
= -\frac{m_{\text{sat}}^2}{\alpha}\ln\cosh\!\left(\frac{\alpha B(r)}{m_{\text{sat}}}\right),
$$

a **single-valued function of position**. Nonlinearity and saturation are
irrelevant; what matters is reversibility. Hence $F = -\nabla U$ is a gradient
field and $\oint F\cdot\mathrm{d}r = 0$ around any closed path, whatever the
ramp geometry, whatever the magnet arrangement, however cunning the angles.
Numerically, integrating the force around the ramp-plus-return loop gives
$-6.4\times10^{-12}\,$J against a ramp gain of $8.75\times10^{-4}\,$J — zero to
seven significant figures.

The ball's problem is the one every builder discovers: it sticks at the gate.
Returning it to the ramp foot costs exactly what the climb produced.

There is one genuine way to make $\oint F\cdot\mathrm{d}r \neq 0$ in
magnetostatics: **hysteresis**, which makes $M(H)$ multivalued and breaks
single-valuedness of $U$. It is worth being precise about the sign. The area
enclosed by a hysteresis loop is energy *dissipated as heat per cycle*:

$$
\oint F\cdot\mathrm{d}r = -\mu_0 V \oint H\,\mathrm{d}M < 0 .
$$

The only loophole in the magnetostatic no-go theorem has the wrong sign. A
hysteretic material can release energy once — that is a permanent magnet being
demagnetised, i.e. a battery being discharged — but never per cycle.

$$
\boxed{W_{\text{net}} = 0 \ \text{for reversible magnetisation}; \ < 0 \ \text{with hysteresis}}
$$

### 4.4 Design D — the buoyancy belt

**Provenance.** Recurrent; frequently patented; occasionally financed.

**Specification.** Sealed floats of displacement $V = 1\,$L are attached to a
chain. Each rises $d = 10\,$m through a water column, is carried over a sprocket
at the top, descends through air, and re-enters the column through a rotary seal
at the bottom. Twenty floats on a $2\,$s cycle.

**The claim.** Each float experiences buoyant force $\rho g V$ over the full
ascent:

$$
W_{\text{claim}} = \rho g V d = 97.89\ \text{J per float},
$$

giving a rated output of $\mathbf{978.9\ W}$. The descent through air is free
because the floats are light. The seal is treated as an engineering detail.

**The audit.** The seal is the entire machine. To insert a float at depth $d$,
one must displace its own volume of water against the gauge pressure there,
$P = \rho g d = 97.89\,$kPa:

$$
W_{\text{hidden}} = P V = \rho g d V = 97.89\ \text{J}.
$$

Identical, term for term, to the buoyant work — necessarily so, since
$\rho g V d$ and $(\rho g d)V$ are the same product. Buoyancy is a hydrostatic
force derivable from a potential, so Section 3.1 applies and the answer was
never in doubt; the value of the calculation is that it shows *where* the money
goes, which is the seal that the design brief dismissed.

$$
\boxed{W_{\text{net}} = 0 \ \text{exactly; } -2.1\times10^{-13}\ \text{J numerically}}
$$

### 4.5 Design E — the bootstrapped motor–generator set

**Provenance.** The dominant modern form; the substrate of most "free energy"
claims since about 1970.

**Specification.** A motor of efficiency $\eta_m = 0.90$ drives a generator of
efficiency $\eta_g = 0.90$, whose output is fed back to the motor. A battery
starts it; the battery is then disconnected.

**The claim.** Once running, the loop sustains itself and surplus is drawn off.

**The audit.** This design fails for an accounting reason rather than a
field-theoretic one, and it is the only one in the catalogue that does. The loop
gain is $\eta_m\eta_g = 0.81$, so circulating energy obeys
$E_{n+1} = 0.81\,E_n$:

| Passes | 0 | 1 | 5 | 10 | 20 | 40 |
|---|---|---|---|---|---|---|
| $E_n$ (J) | 100.00 | 81.00 | 34.87 | 12.16 | 1.48 | 0.02 |

with an e-folding lifetime of 4.75 passes. Self-sustaining operation requires
$\eta_m\eta_g \ge 1$; the design is short by 19 percentage points, and no
component improvement closes a multiplicative gap of that kind.

**Why this design nevertheless produces measurements showing overunity.** This
is the practically important part of the report. True average power is

$$
P = \frac{1}{T}\int_0^T v(t)\,i(t)\,\mathrm{d}t = V_{\text{rms}} I_{\text{rms}}\cos\phi ,
$$

but a meter that samples $V_{\text{rms}}$ and $I_{\text{rms}}$ separately and
multiplies them reports $\hat{P} = V_{\text{rms}}I_{\text{rms}}$, overstating by
the reciprocal power factor:

| $\phi$ | 0° | 45° | 60° | 84° | 87° |
|---|---|---|---|---|---|
| apparent gain $\hat P/P$ | 1.00× | 1.41× | 2.00× | 9.57× | 19.11× |

Pulsed drives into inductive loads — the near-universal topology in this
literature — routinely run at $\phi > 80^\circ$. A builder measuring input with
a DC multimeter on the supply rail and output with an averaging meter on a
reactive load will measure tenfold overunity on a device that is quietly
consuming power. **The apparatus under test is the wattmeter.**

$$
\boxed{W_{\text{net}} < 0 \ \text{always; the reported surplus is an instrumentation artefact}}
$$

---

## 5. Numerical verification

The accompanying program [`pmm1_ledger.py`](pmm1_ledger.py) recomputes every
ledger above from first principles using the standard library only — no numpy,
no symbolic algebra, and in particular no appeal to energy conservation
anywhere in the code. Gravitational and magnetostatic work are obtained as
explicit line integrals of force along explicit closed paths, by composite
Simpson quadrature and midpoint summation respectively.

```
SUMMARY -- net energy delivered per closed cycle
  A  overbalanced wheel      -6.125e-10 J    (claimed +70.31 J/rev)
  B  capillary siphon        +0.000e+00 J    (claimed  +1.46 uJ/mm^3)
  C  magnet ramp             -6.356e-12 J    (claimed +8.75e-04 J)
  D  buoyancy belt           -2.132e-13 J    (claimed +97.89 J/float)
  E  motor-generator          decays as 0.81^n
```

The residuals are quadrature error and shrink as the discretisation is refined;
they are between $10^{-9}$ and $10^{-15}$ of the corresponding claimed outputs.
No design in the catalogue survives its own energy ledger.

To reproduce:

```bash
python3 pmm1_ledger.py
```

---

## 6. An audit protocol for claimed PMM1 devices

The foregoing suggests a checklist that is more useful than the bare assertion
of impossibility, because it locates the error in a specific device rather than
merely predicting that one exists. In order of diagnostic yield:

1. **Close the loop in full configuration space.** List *every* coordinate,
   including internal ones — arm extensions, valve states, latch positions,
   magnetisation, charge. A cycle that fails to close in even one of them is not
   a cycle. This single step resolves Designs A and C.

2. **Enumerate the reservoirs.** Batteries, capacitors, compressed gas, elastic
   strain, residual magnetisation, thermal mass, chemical potential, and ambient
   gradients (RF, vibration, thermal). Each has a finite content; a PMM1 claim
   requires *unbounded* output, so the discriminating test is duration, not
   magnitude.

3. **Run the sealed-box test.** Enclose the entire device — including its
   operator's hands — in an adiabatic, electromagnetically shielded boundary and
   measure net energy crossing it over at least ten e-folding times of the
   longest internal reservoir. This is the only test that cannot be defeated by
   a mechanism the auditor failed to anticipate, because it makes no assumption
   about the mechanism at all.

4. **Validate the instrumentation against the waveform.** Use a wattmeter
   computing $\frac{1}{T}\int v\,i\,\mathrm{d}t$ with bandwidth at least ten
   times the highest significant harmonic, and verify it against a known
   resistive load at the same crest factor. Check current-transformer phase
   error explicitly. Per Section 4.5 this step alone accounts for most modern
   claims.

5. **Perform a run-down test.** Disconnect all sources and measure the decay
   envelope. A PMM1 has no decay envelope; every real device does, and the
   time constant identifies the reservoir.

6. **Perform a null test.** Replace the active element with an inert dummy of
   matched mass, impedance, and geometry. A surviving effect is an artefact of
   the apparatus.

7. **Report the ledger, not the output.** State $W_{\text{out}}$ *and*
   $W_{\text{in}}$ with uncertainties. Claims are conventionally stated as a
   single number, which is precisely the format that conceals the error.

---

## 7. Where energy conservation genuinely fails

Intellectual honesty requires acknowledging that energy conservation is not
unconditional, and it is a disservice to state the no-go theorem more broadly
than it holds.

In general relativity, energy conservation follows from the existence of a
timelike Killing vector field — a time-translation symmetry of the spacetime
itself. A Friedmann–Lemaître–Robertson–Walker universe has no such symmetry: it
is expanding. Consequently **there is no globally conserved energy in
cosmology.** This is not a technicality or a bookkeeping convention. Photons
redshift and the lost energy goes nowhere; the energy density of a cosmological
constant remains fixed while the volume it occupies grows without bound. Total
energy is simply not a well-defined conserved quantity in a general curved
spacetime.

Two reasons this does not help a machine builder:

**Bound systems do not expand.** A laboratory apparatus is held together by
electromagnetic and gravitational forces vastly stronger than the cosmological
term. It is not comoving; it does not participate in the expansion; there is no
local energy non-conservation for it to tap.

**The available scale is absurdly small.** The residual cosmological effect on
local dynamics enters as a tidal acceleration of order $H_0^2 r$. With
$H_0 = 2.18\times10^{-18}\,\text{s}^{-1}$ and $r = 1\,$m,

$$
a_{\text{cosmo}} \sim H_0^2 r = 4.8\times10^{-36}\ \text{m s}^{-2},
$$

which is $5\times10^{-37}$ of standard gravity. Moving a $1\,$kg mass one metre
against it involves $4.8\times10^{-36}\,$J — about $10^{17}$ times smaller than
the energy of a single optical photon.

A related and frequently invoked case is the **quantum vacuum**. The Casimir
force between conducting plates is real and, at $10\,$nm separation, reaches
$1.3\times10^{5}\,$Pa — over an atmosphere. But it derives from a potential
$U(d) \propto -1/d^3$, so it is conservative: the plates release energy on
approach and demand exactly that much to separate. It is a potential well, not a
power source — a spring, not a battery. Section 3.1 applies unchanged.

---

## 8. Historical and institutional note

The impossibility of PMM1 was accepted institutionally long before it was proved
formally. The French Académie des Sciences resolved in 1775 to accept no further
perpetual motion submissions — seventy years before Joule and Helmholtz gave the
first law its modern statement, and 143 years before Noether explained why it
holds. The Académie's reasoning was inductive and entirely sound: every
submission had failed, and examining them consumed resources better spent
elsewhere.

The United States Patent and Trademark Office maintains the same posture by a
different route. The working-model requirement was abolished generally in 1880
but is expressly retained for perpetual motion claims, on the ground that a
device contradicting established physical law lacks credible utility under
35 U.S.C. §101. The practical effect is that PMM1 patents are refused not on the
merits of the mechanism but on the applicant's inability to demonstrate one.

The persistence of the field is best understood through Design A. The
overbalanced wheel has been reinvented continuously for nine hundred years, and
each reinventor performs the same correct torque calculation and omits the same
radial term. The error is not stupidity; it is that the omitted term does not
appear anywhere in the natural framing of the problem. One has to know to look
for it — which is the argument for the audit protocol of Section 6 over the bare
appeal to conservation.

---

## 9. Conclusions

1. **The design brief is unsatisfiable.** A PMM1 requires
   $\oint\mathrm{d}U_{\text{int}} \neq 0$ over a closed cycle, which is a
   contradiction in terms rather than an unmet engineering challenge.

2. **A single theorem covers the whole mechanical class.** Any machine executing
   a closed cycle under time-independent constraints in a conservative field
   delivers $W_{\text{out}} = -D \le 0$. Every design in Section 4 is a corollary.

3. **Each design fails at a locatable, quantifiable point.** The wheel's
   leverage surplus equals its slider work; the capillary's head equals its
   Laplace suction; the magnet ramp's climb equals its return; the buoyancy
   belt's lift equals its injection work; the motor–generator loop decays as
   $(\eta_m\eta_g)^n$. In every case the cancellation is exact, and verified
   numerically to between nine and fifteen significant figures.

4. **The modern failure mode is metrological, not mechanical.** Most
   contemporary overunity claims are power-factor artefacts. Correct
   instrumentation dissolves them without reference to thermodynamics at all.

5. **The one real exception is unreachable.** Energy conservation genuinely
   fails in expanding spacetime, by a margin roughly 36 orders of magnitude too
   small to detect in a laboratory, and not at all for bound systems.

The honest summary for a would-be builder: the first law is not a rule imposed
on machines by physicists. It is a statement that tomorrow's physics will be the
same as today's. Any machine that produced energy from nothing would be
evidence that it is not.

---

## References

1. H. B. Callen, *Thermodynamics and an Introduction to Thermostatistics*, 2nd ed., Wiley, 1985.
2. E. Fermi, *Thermodynamics*, Dover, 1956.
3. R. P. Feynman, R. B. Leighton and M. Sands, *The Feynman Lectures on Physics*, Vol. I, Ch. 4 ("Conservation of Energy") and Ch. 46 ("Ratchet and Pawl"), Addison-Wesley, 1963.
4. E. Noether, "Invariante Variationsprobleme", *Nachrichten von der Gesellschaft der Wissenschaften zu Göttingen, Mathematisch-Physikalische Klasse*, 235–257, 1918.
5. L. D. Landau and E. M. Lifshitz, *Mechanics*, 3rd ed., Butterworth-Heinemann, 1976.
6. J. D. Jackson, *Classical Electrodynamics*, 3rd ed., Wiley, 1999.
7. R. M. Wald, *General Relativity*, University of Chicago Press, 1984 — on the absence of a globally conserved energy without a timelike Killing field.
8. A. W. J. G. Ord-Hume, *Perpetual Motion: The History of an Obsession*, St. Martin's Press, 1977.
9. S. W. Angrist, "Perpetual Motion Machines", *Scientific American* **218**(1), 114–122, 1968.
10. H. B. G. Casimir, "On the attraction between two perfectly conducting plates", *Proc. K. Ned. Akad. Wet.* **51**, 793, 1948.
11. P.-G. de Gennes, F. Brochard-Wyart and D. Quéré, *Capillarity and Wetting Phenomena*, Springer, 2004.
12. G. Bertotti, *Hysteresis in Magnetism*, Academic Press, 1998.
13. T. Rosenband *et al.*, "Frequency Ratio of Al⁺ and Hg⁺ Single-Ion Optical Clocks; Metrology at the 17th Decimal Place", *Science* **319**, 1808–1812, 2008.
14. Bhāskara II, *Siddhānta Śiromani*, c. 1150 — earliest known description of the overbalanced wheel.
15. United States Patent and Trademark Office, *Manual of Patent Examining Procedure* §608.03, on models for perpetual motion devices.
16. D. E. Simanek, *The Museum of Unworkable Devices*, Lock Haven University — an extensive annotated catalogue of failed mechanisms.

---

*Companion code: [`pmm1_ledger.py`](pmm1_ledger.py). All figures quoted in this
report are computed by that program and reproducible with a bare Python 3
interpreter.*

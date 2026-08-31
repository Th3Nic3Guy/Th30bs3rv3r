# FREE WILL
**F**ramework for **R**elational **E**pistemics and **E**volving beliefs, **W**ith
**I**terative **L**ocalized **L**earning

---

## Abstract

[TODO: write after Phase 2 data collection. Must state: (1) the mechanism in one sentence,
(2) the experimental scope, (3) headline findings, (4) relation to prior opinion-dynamics
and trust literature.]

---

## 1. Related Work

Models of opinion and belief change in populations have a long history in mathematical
sociology and, more recently, in computational social science. FREE WILL draws on five
distinct traditions — consensus models, bounded-confidence models, pairwise interaction
models, subjective trust logics, and belief revision theory — while departing from each in
specific, identifiable ways.

**Consensus models.** DeGroot's classical model of opinion pooling represents each agent's
belief as a weighted average of its neighbors' beliefs, with fixed weights, and shows that
under mild connectivity conditions the population converges to a single shared opinion
(DeGroot, 1974). The consensus term in FREE WILL's belief update, α(I), is structurally a
DeGroot-style weighted average: each agent aggregates the confidence values reported by
other agents on a given statement. The critical departure is that DeGroot's weights are
fixed and global, whereas FREE WILL's weights — the contextual trust values τ(P|I) — are
dynamic, learned from interaction history, and specific to the (source, topic) pair rather
than to the source alone. A DeGroot agent trusts a given neighbor equally on every subject;
a FREE WILL agent can trust the same source on one axiom and distrust it on another. This
per-topic granularity is one of the two central claims of novelty in this work.

**Bounded-confidence models.** Hegselmann and Krause (2002) and, independently, Deffuant
and Weisbuch (2000) introduced models in which agents only revise their opinion toward
others whose opinion lies within a fixed distance ε; sources outside that bound are ignored
entirely. This mechanism — rather than network structure — is what produces stable opinion
clusters instead of full consensus, and it is the standard explanation in the literature for
polarization phenomena in otherwise homogeneous populations. FREE WILL also produces
clustering, but through a different mechanism: there is no hard distance cutoff. Instead,
resistance to belief change is graded and endogenous, governed by the reluctance function
γ(I) and the reconsideration coefficient ξ, interacting with the asymmetric trust-update
rules described in Section 3.2. Clustering in FREE WILL is therefore trust-erosion-driven
rather than distance-threshold-driven.

The pairwise interaction protocol used in FREE WILL — one agent meets one other agent per
tick and a single idea is exchanged — is structurally identical to the Deffuant-Weisbuch
update scheme. What differs is not the interaction structure but what happens inside each
interaction: instead of a scalar opinion nudged toward a neighbor's scalar opinion, FREE
WILL performs fuzzy logical inference over a directed acyclic graph of propositional
statements, updating not only the target statement but its antecedents and consequents (the
flowback mechanism, Section 4.2).

**Subjective trust logics.** Jøsang's subjective logic (Jøsang, 2001; 2016) formalizes
belief as an opinion triple of belief, disbelief, and uncertainty, and defines algebraic
operators for combining testimony from multiple sources weighted by trust in those sources.
The consensus function α(I) in FREE WILL, and the underlying notion of a trust value
τ(P|I) attached to a source for a given proposition, are conceptually close to subjective
logic's fusion operators. What subjective logic does not provide is a native way to
propagate belief change through a dependency structure of composite Boolean statements
built from those opinions. FREE WILL's substrate is a DAG of propositional formulas
resolved via fuzzy logic (Section 3.1), not a flat set of independent opinions — this
distinction is what the model's novelty claim rests on.

**Belief revision and epistemic entrenchment.** The AGM framework (Alchourrón, Gärdenfors,
& Makinson, 1985) formalizes how a rational belief set should change minimally in response
to new, possibly contradictory information, and introduces the notion of epistemic
entrenchment: some beliefs resist revision more than others because more of the belief set
depends on them. AGM entrenchment is typically specified as a qualitative ordering over
beliefs, not a computed numerical quantity. FREE WILL's reluctance function γ(I) (Section
3.3) is a continuous, dependency-graph-derived operationalization of entrenchment: the
model computes how much belief change would propagate to dependent statements and uses that
quantity to damp the update, tuned by the reconsideration parameter ξ. Making entrenchment
quantitative and mechanically derived from the DAG's structure, rather than an
externally-imposed ordering, is the second central claim of novelty in this work.

**Belief-system constraint in mass publics.** Converse's classic study of political belief
systems (Converse, 1964) argues that, contrary to elite intuition, most individuals' beliefs
across nominally related domains are only weakly correlated — real populations show much
less ideological "constraint" than a coherent belief-system model would predict. This
motivates the mixed-topic experimental condition (Section 4.6), in which all ten concept
domains are seeded into a single agent population simultaneously, and gives it a concrete,
falsifiable target (Hypothesis H7).

**Affective polarization.** A distinct strand of political-psychology literature documents
that partisan warmth and trust toward one's own group versus an opposing group diverges from
actual agreement on policy substance (Iyengar, Sood, & Lelkes, 2012; Iyengar & Westwood,
2015). This motivates treating FREE WILL's belief-similarity network and trust network as
two distinct, only partially overlapping structures (Section 4.7, Hypothesis H8).

**Order effects in belief updating.** Hogarth and Einhorn's belief-adjustment model (1992)
demonstrates, across five experiments, that the order in which evidence arrives produces
systematic primacy or recency effects on final belief — belief updating in humans is not
order-independent the way a Bayesian update on identical evidence would be. This motivates
Hypothesis H9: FREE WILL's reluctance function γ(I) is explicitly path-dependent (Section
3.3), computed from consequent beliefs *at the time of update*, so identical seed
composition delivered in different temporal orders is expected to produce different final
consensus — a direct computational parallel to Hogarth and Einhorn's human-subject finding.

**Influence concentration versus population susceptibility.** Two distinct traditions bear
on the influencer mechanism (Section 4.6). Kempe, Kleinberg, and Tardos (2003) formalize
influence maximization in networks, showing that a small, well-chosen seed set of
high-reach nodes can provably shift a large fraction of a network under standard diffusion
models — motivating the reach-based design of the influencer role itself. Watts and Dodds
(2007), however, directly challenge the stronger claim that such influential individuals
are what actually drives large-scale opinion cascades in practice: their simulations find
that cascades are typically driven by a critical mass of easily-influenced ordinary
individuals rather than by influentials per se, and that the "influentials hypothesis"
requires more careful specification than it usually receives. Hypothesis H10 is deliberately
positioned between these two findings rather than assuming either: it asks whether FREE
WILL's small, structurally-privileged influencer minority measurably shifts consensus, a
genuinely open, falsifiable question given this unresolved tension in the literature it
draws on.

**Audience design in message content selection.** Bell's (1984) theory of audience design
argues that speakers do not choose speech content independent of who they are addressing —
style and content are continuously adapted to a specific addressee, distinct from
adaptation driven by topic or setting alone. This motivates the message-formulation policy
in Section 4.12: an agent's choice of which proposition to raise in conversation depends on
its relationship history with the specific recipient (exploitation of an established
channel) as much as on its own overall strongest belief (exploration/first contact),
layered beneath an overriding agenda where one exists — directly paralleling audience,
topic, and self-orientation as three distinct drivers of speech content.

### Theoretical Contribution

Drawing the seven traditions above together, FREE WILL's contribution is organized along
three axes, each operationalized by a specific formal mechanism and tested by a specific
subset of the hypotheses in Section 2:

1. **Topic-specific, dynamically-learned trust** extends consensus and bounded-confidence
   models (DeGroot, 1974; Hegselmann & Krause, 2002; Deffuant & Weisbuch, 2000) by
   replacing a single, fixed or distance-thresholded trust weight with a per-(source,
   topic) value governed by two distinct, psychologically-motivated update regimes
   (confirmation-consistency and credibility-surprise, Section 3.2). This axis is tested
   directly by H4 (whether social consensus alone can carry an axiom with no logical
   support) and indirectly by every hypothesis that depends on cluster formation (H1, H5,
   H7, H8), since clustering in this model is trust-erosion-driven rather than
   distance-threshold-driven.

2. **Continuous, dependency-derived entrenchment** extends belief revision theory (AGM;
   Alchourrón, Gärdenfors, & Makinson, 1985) by computing epistemic entrenchment as a
   numerical function of the belief DAG's structure (γ, Section 3.3) rather than imposing
   a qualitative ordering externally, and explicitly declines to enforce logical coherence
   on the resulting belief graph — a position argued in full in Section 5. This axis is
   tested by H9, which asks whether the resulting path-dependence produces measurably
   different outcomes under identical seed composition delivered in different temporal
   orders — a computational parallel to Hogarth and Einhorn's (1992) human-subject finding
   that belief updating shows order effects rather than order-independence.

3. **Population-scale embedding of individually-established, mostly single-exposure
   findings.** Baumeister et al.'s (2001) negativity bias, Brehm's (1966) reactance
   theory, Nisbett and Wilson's (1977) halo effect, and Walton's (1998) treatment of ad
   hominem reasoning are each established at the level of a single person or a single
   interaction. Kempe, Kleinberg, and Tardos (2003) and Watts and Dodds (2007) disagree at
   the level of a whole network about whether influence concentrates in a few high-reach
   individuals or in a susceptible crowd. None of these literatures were built to answer
   what happens when their mechanisms are embedded together, repeated over many
   interactions, and allowed to propagate through a structured belief graph. FREE WILL's
   architecture — population-scale, temporally extended (1000 ticks), structurally
   propagated (Section 4.2's flowback) — is built specifically to ask that compound
   question, tested by H5, H6, H9, and H10 together rather than any single hypothesis in
   isolation.

**Positioning summary.**

| Prior work | Mechanism borrowed | Point of departure |
|---|---|---|
| DeGroot (1974) | Weighted-average consensus (α(I)) | Weights are per-topic, learned trust, not fixed global weights |
| Hegselmann–Krause (2002) | Clustering as an emergent outcome | Soft, trust-erosion-based resistance instead of a hard distance bound |
| Deffuant–Weisbuch (2000) | Pairwise, one-exchange-per-tick interaction protocol | Novelty is inside the interaction (fuzzy DAG inference), not the protocol |
| Jøsang, subjective logic (2001/2016) | Multi-source trust-weighted belief fusion | Extended onto a DAG of composite Boolean statements via fuzzy resolution |
| AGM belief revision (1985) | Epistemic entrenchment | Made continuous and computed from dependency-graph structure (γ, ξ) |
| Converse (1964) | — (theoretical target) | Falsifiable interpretation for the mixed-topic condition (H7) |
| Iyengar, Sood & Lelkes (2012); Iyengar & Westwood (2015) | — (theoretical target) | Motivates the dual belief/trust network design (H8) |
| Hogarth & Einhorn (1992) | Order effects in human belief updating | Motivates H9, computationally paralleling human primacy/recency effects via γ's path-dependence |
| Kempe, Kleinberg & Tardos (2003) | Influence maximization via high-reach seed nodes | Motivates the reach-based design of the influencer role (Section 4.6) |
| Watts & Dodds (2007) | — (theoretical tension, not a mechanism) | H10 is positioned between this finding and Kempe et al.'s, rather than assuming either |
| Bell (1984) | Audience design — speech content adapted to addressee | Motivates the message-formulation policy (Section 4.12, H12) |

---

## 2. Hypotheses

- **H1** (domain generalization): cluster-formation and stabilization patterns are
  qualitatively similar across all 10 concept domains, but speed and final polarization
  differ by topic structure.
- **H2** (seeding asymmetry): domains with symmetric axiom seeding converge to consensus
  more slowly than asymmetrically-seeded domains.
- **H3**: single-polarity information seeding produces faster, more complete consensus than
  balanced seeding.
- **H4** (λ effect): the influence coefficient λ determines whether information with no
  logical support (low ω) can still become dominant belief through consensus alone (high α).
- **H5** (population-stability gradient): outcome variance (polarization, cluster count,
  time-to-stabilize) increases monotonically from Fixed → Semi-fixed → Random agent
  populations.
- **H6** (robustness check on H5): outcome means do not differ significantly across the
  three population-stability conditions.
- **H7** (cross-domain constraint): in the mixed-topic condition, agents show
  cluster-membership correlation across concept domains exceeding what independent,
  per-domain runs would predict by chance.
- **H8** (belief/trust decoupling): per-domain belief-cluster and trust-cluster partitions
  show NMI/ARI agreement significantly above a chance-level permutation null but
  significantly below perfect overlap.
- **H9** (order-dependence): for identical total seed composition, the temporal order in
  which balanced vs. skewed information arrives significantly affects final consensus.
- **H10** (influencer effect): a small number of high-reach, agenda-scripted influencer
  agents measurably shifts final population consensus toward their agenda relative to the
  fully-random condition, despite representing a small fraction of the population.
- **H11** (hub sub-cluster differentiation): agents converging on a shared, highly-trusted
  central figure develop measurable sub-cluster differentiation among themselves — driven
  by their own incidental, asymmetric interactions with each other — detectable via
  hierarchical/recursive community detection beyond what flat modularity captures.
- **H12** (topic-channel specialization): repeated exploitation-mode interactions cause
  specific agent pairs to converge on a narrower, more consistent subset of discussed
  topics over time than a null model where topic is chosen randomly per exchange, and this
  pairwise topical specialization is measurably distinct from — not fully explained by —
  the belief- and trust-network clusters already tracked (H1, H5, H7, H8).

---

## 3. Formal Model

### 3.1 Substrate

FREE WILL's belief substrate is a DAG of fuzzy Boolean composites. Each node is a
proposition — an axiom or a Boolean composite of other nodes — carrying a confidence value
in [−.5, .5]. Composite resolution follows Table 1.

**Table 1 — Fuzzy resolution logic**

| Boolean | Fuzzy |
|---|---|
| AND(x,y) | MIN(x,y) |
| OR(x,y) | MAX(x,y) |
| NOT(x) | −x |
| IMPLIES(x,y) | MAX(−x,y) |

### 3.2 Trust and belief update rules

A message is $M^{I}_{P}\vert_t = \langle P, I, \nu \rangle$: $P$ the publishing agent, $I$
the proposition, $\nu \in [-.5,.5]$ the stated confidence. Let $\varphi(I\vert P)$ be the
mean of $\nu$ across all of $P$'s messages on $I$. The trust-weighted social consensus term
is:

$$\alpha(I)\vert_t = \frac{2}{|P|}\sum_{P} \varphi(I\vert P)\vert_t \cdot \tau(P\vert I)\vert_t$$

**Trust update (Alpha Flux).** On receipt of a message, trust in the source updates as:

$$\Delta\tau(P\vert I)\vert_t = \mu \cdot \left(\varphi(I\vert P)\vert_{t-1} - \beta(I)\vert_t\right)$$
$$\tau(P\vert I)\vert_t = S_n\left(\tau(P\vert I)\vert_{t-1} + \Delta\tau(P\vert I)\vert_t\right)$$

**Belief update (Forward Flow).** Belief is recomputed fresh from current $\alpha$ and
$\omega$, and the resulting delta is what feeds the reluctance-damped update in Section 3.3:

$$\beta'(I)\vert_t = \lambda \cdot \alpha(I)\vert_t + (1-\lambda) \cdot \omega(I)\vert_t$$
$$\Delta\beta(I)\vert_t = \beta'(I)\vert_t - \beta(I)\vert_{t-1}$$

where λ is the influence coefficient and ω(I) is the fuzzy-resolved internal inference term
computed over the agent's DAG.

**Naming the qualitative regimes.** The confirmation-consistency and credibility-surprise
patterns from Table 3 of the source dissertation are qualitative descriptions of what this
continuous mechanism tends to produce, not separate equations. They hold exactly when an
agent's prior belief on $I$ is near-neutral ($\beta(I) \approx 0$), in which case
$\Delta\tau(P\vert I) \approx \mu \cdot \varphi(I\vert P)$ and the sign of the trust update
tracks the sign of the message's confidence directly, reproducing Table 3's categorical
pattern. Away from that special case, $\Delta\tau(P\vert I)$ depends on the *magnitude gap*
between $\varphi(I\vert P)$ and the agent's already-held belief, not on sign categories
alone — two agents receiving sign-identical messages can have oppositely-signed trust
updates if their prior beliefs differ enough in magnitude. The names
**confirmation-consistency** (trusted-source regime) and **credibility-surprise**
(untrusted-source regime) are retained as useful qualitative labels for this behavior, and
the psychological motivation from Eagly, Wood, & Chaiken (1978) and Walster, Aronson, &
Abrahams (1966) still applies to the *general* magnitude-sensitive mechanism, not only to
its near-neutral-prior special case.

**Axioms are governed by the same formula as composites, via the orphan convention.** The
source dissertation restricts the $\beta'$ recompute above to composite statements only
("$I$ is not axiomatic" is a stated assumption in its Forward Flow derivation), since
$\omega(I)$ is defined by fuzzy-resolving an axiom's sub-statements — a true axiom has none.
Rather than defining a separate update rule for axioms, this is resolved by extending the
orphan convention from Section 3.8 ($\omega(I):=\beta(I)$) *permanently* to true axioms,
not just temporarily to composites awaiting revelation — an axiom never has operands to
reveal, so it never leaves this state. Substituting $\omega(I)=\beta(I)$ into the belief
recompute:

$$\beta'(I) = \lambda\alpha(I) + (1-\lambda)\beta(I) \quad\Rightarrow\quad \Delta\beta(I) = \lambda\left(\alpha(I) - \beta(I)\right)$$

The internal-logic term cancels out of the delta entirely, leaving belief in an axiom
driven purely by the gap between social consensus and current belief, scaled by $\lambda$
— a clean, principled consequence of an axiom having no internal structure to reason with,
not an arbitrary special case bolted onto the formalism.

### 3.3 Reluctance function

Let $C(I)$ denote the set of $I$'s consequents in the DAG. The consequential mean belief is:

$$\rho(I_c \vert I)\vert_t = \begin{cases} \frac{1}{|C(I)|}\sum_{I_c \in C(I)} \beta(I_c)\vert_t & |C(I)| > 0 \\ 0 & |C(I)| = 0 \end{cases}$$

The $|C(I)|=0$ case (a leaf proposition nothing else depends on) is not addressed in the
source dissertation; $\rho=0$ is adopted here because it yields $\gamma(I)=1$ below — no
reluctance damping — which matches the reluctance function's stated purpose: a proposition
with no downstream dependents carries no consistency risk to protect, so there is nothing
for reluctance to resist on its behalf.

Reluctance is computed via the rise function:

$$\zeta(x,\xi) = e^{x^2/\xi}, \quad \gamma(I) = \zeta\left(\rho(I_c\vert I),\, \xi\right)$$

where ξ is the reconsideration coefficient. Since $x^2 \ge 0$ and $\xi > 0$, $\gamma(I) \ge
1$ always, with equality exactly at $\rho=0$ — reluctance only damps updates, never
amplifies them. The companion decay function, used elsewhere for trust-decay behavior, is:

$$\varepsilon(x,\eta) = e^{-x/(\eta \times 100)}$$

**Connecting equation, reconstructed from source material.** The source dissertation never
writes an equation applying $\varepsilon(x,\eta)$, but its intent is explicit in prose
(Section 7.4.1: η "influences the default trust levels for each axiom... likely to trust
[an] agent if it is unaware of a particular axiomatic information, but... trust less the
next agent... and the next agent even less") and in Figure 8's caption ("exponential fall
of default trust as more sources are added"). This describes a **default trust
initialization rule**: the first time an agent encounters a source $P$ it has no prior
trust data for, regarding proposition $I$, its initial trust is not arbitrary but decays
with how many *other* sources have already been encountered for that same proposition:

$$\tau(P\vert I)\vert_{\text{first encounter}} = 0.5 \cdot \varepsilon(x,\eta), \quad x = \left|\{P' : \tau(P'\vert I) \text{ already defined}\}\right|$$

scaled by 0.5 (the maximum magnitude of the [−.5,.5] trust range) since $\varepsilon \in
(0,1]$ for $x\ge0$. This reproduces the qualitative behavior η is described as governing:
the first source on a topic receives high default trust, and each subsequent
first-time-encountered source receives progressively less, without any special-casing
beyond this one initialization rule. This equation was not present in the source material
and is a reconstruction, not a verbatim recovery — flagged as such since it fills a gap
that existed in the original dissertation itself, not one introduced during formalization.

The committed update, using $\Delta\beta(I)$ from Section 3.2:

$$\beta(I)\vert_{t} = \beta(I)\vert_{t-1} + \frac{\Delta\beta(I)\vert_{t}}{\gamma(I)}$$

This update is not passed through the SmoothStep clamp $S_n$ — unlike the trust update in
Section 3.2, which explicitly clamps via $S_n$. This asymmetry is inherited directly from
the source dissertation's Forward Flow derivation, which clamps τ and ω but not β at this
step, relying instead on γ's damping and the fact that α and ω are already bounded within
[−.5, .5] (Section 3.2) to keep β from drifting far outside that range in practice.

### 3.4 Notation

| Symbol | Role |
|---|---|
| $\nu$ | per-message stated confidence (renamed from the source dissertation's overloaded $\mu$, which also denoted the learning-rate coefficient below — the two are unrelated quantities that shared a symbol) |
| $\varphi(I\vert P)$ | mean stated confidence ($\nu$) across $P$'s messages on $I$ |
| $\lambda$ | influence coefficient — weight on social consensus vs. internal logic (renamed from $\kappa$; $\lambda$ is the standard symbol for a convex-combination weight) |
| $\mu$ | residual flowback coefficient / learning rate (unchanged; no longer collides with message confidence now that it is $\nu$) |
| $\eta$ | trust decay coefficient, also the second argument to the decay function $\varepsilon(x,\eta)$ |
| $\xi$ | reconsideration coefficient (renamed from $\iota$, which is easily misread as Latin "i," "l," or "1") |
| $|C(I)|$ | count of $I$'s consequents (renamed from the source dissertation's $|N|$, which sat too close visually to the SmoothStep polynomial degree $n$ below) |
| $\rho(I_c\vert I)$ | consequential mean belief feeding reluctance ($=0$ by convention when $I$ has no consequents) |
| $\varepsilon(x,\eta)$ | decay function, $\varepsilon(x,\eta) = e^{-x/(\eta \times 100)}$ |
| $\zeta(x,\xi)$ | rise function, $\zeta(x,\xi) = e^{x^2/\xi}$ |
| $\gamma(I)$ | reluctance (damping applied before an update commits) |
| $\psi(I_c\vert I)$ | flowback delta propagated to a consequent after an update (distinct from γ; source dissertation's "Gamma Flux" reused γ for this and has been renamed here) |
| $\text{Fz}(\text{expr}, \ldots)$ | fuzzy resolution operator (Table 1), applied to belief for revelation (Section 3.8) and to trust for composite derivation (Section 3.9) |
| $\chi$ | cross-contamination coefficient — governs ad hominem drift and halo-effect transfer (Section 3.7) |
| $\theta$ | negativity amplification factor (Section 3.7) |
| $\pi$ | defiance amplification factor (Section 3.7) |
| $k(I)$ | count of the agent's own outgoing messages asserting $I$ (Section 3.7) |
| $k^*$ | commitment threshold for doubling-down defiance (Section 3.7) |
| $\bar{\tau}(A,P)$ | agent $A$'s mean trust in agent $P$ across shared leaf propositions, feeding movement (Section 4.11) |
| $\text{PA}(A)$ | Personal Affinity vector — agent $A$'s trust-weighted movement direction (Section 4.11) |
| $\varepsilon_{\text{explore}}$ | exploration rate — probability of ignoring $\text{PA}(A)$ and moving in a uniform random direction (Section 4.11) |
| $\tau_{\text{still}}$ | stay-threshold — below this normalized affinity magnitude, an agent stays in place rather than moving (Section 4.11) |
| $\ell(A,P)$ | the most recent proposition agent $A$ has raised with recipient $P$ specifically (Section 4.12) |
| $\varepsilon_{\text{topic}}$ | topic exploration rate — probability of leading with one's overall strongest belief rather than continuing an established channel with a specific recipient (Section 4.12) |

### 3.5 Clamping function

All trust and belief values are clamped by a SmoothStep function defined natively on
[−.5, .5]:

$$S_n(x) = \begin{cases} -0.5 & x \le -0.5 \\ (x+0.5)^{n+1}\sum_{k=0}^{n}\binom{n+k}{k}\binom{2n+1}{n-k}(-(x+0.5))^k - 0.5 & -0.5 \le x \le 0.5 \\ 0.5 & x \ge 0.5 \end{cases}$$

The polynomial degree $n$ is set per agent by $n = \text{round}(9\sigma)$, with $\sigma \in
[0,1]$, matching the degree range (0–9) illustrated in the source dissertation's Figure 7.

### 3.6 Agent parameter distributions

Each agent's parameter tuple $(\lambda, \mu, \eta, \xi, \sigma)$ is independently drawn
from Beta distributions scaled to each parameter's native range. Beta's own shape
parameters are written $(a,b)$ (plain Latin letters) to avoid colliding with $\alpha$ and
$\beta$, which are already claimed by the consensus term and belief:

| Parameter | Distribution |
|---|---|
| λ, μ, σ | Beta(a=2, b=2) |
| η | Beta(a=2, b=5) |
| ξ | Beta(a=2, b=4) |
| χ (cross-contamination) | Beta(a=2, b=3), scaled to [0,1] — mild skew toward lower contamination |
| θ (negativity amplification) | Beta(a=2, b=2), scaled to [1,3] |
| π (defiance amplification) | Beta(a=2, b=2), scaled to [1,3] |
| k* (commitment threshold) | Beta(a=2, b=3), scaled and rounded to integers in [1,10] via $k^* = \text{round}(1 + 9\cdot\text{Beta})$ — skewed toward lower thresholds |

### 3.7 Fallacy-based reaction extensions

Four reaction rules extend the core update (Section 3.2), each grounded in an established
finding from psychology or argumentation theory and selected from a broader candidate
catalog (see Discussion) for having the most direct existing support.

**Ad hominem drift and halo-effect transfer.** A single cross-contamination coefficient
χ ∈ [0,1] governs both effects. Whenever a trust update Δτ(P|I) occurs under either rule in
Section 3.2, a scaled fraction leaks to every other proposition $I'$ the agent holds a
trust value for regarding the same source:

$$\Delta\tau(P\vert I')_{\text{leak}}\vert_t = \chi \cdot \Delta\tau(P\vert I)\vert_t, \quad \forall I' \ne I \text{ where } \tau(P\vert I') \text{ is defined}$$
$$\tau(P\vert I')\vert_t = S_n\left(\tau(P\vert I')\vert_{t-1} + \Delta\tau(P\vert I')_{\text{leak}}\vert_t\right)$$

A negative Δτ(P|I) spreads distrust to unrelated topics (ad hominem drift; Walton, 1998); a
positive Δτ(P|I) spreads trust the same way (halo effect; Nisbett & Wilson, 1977). χ=0
recovers the model's baseline of perfect topic-siloed trust.

**Negativity bias.** A negativity amplification factor θ ≥ 1 scales $\Delta\beta(I)$ from
Section 3.2 asymmetrically by sign, before reluctance damping (Section 3.3):

$$\Delta\beta'(I)\vert_t = \begin{cases} \theta \cdot \Delta\beta(I)\vert_t & \Delta\beta(I)\vert_t < 0 \\ \Delta\beta(I)\vert_t & \Delta\beta(I)\vert_t \ge 0 \end{cases}$$

θ=1 recovers the baseline symmetric update. Motivated by Baumeister, Bratslavsky,
Finkenauer, & Vohs (2001), who document that negative information and events consistently
outweigh equivalent positive ones across a wide range of psychological domains.

**Doubling-down defiance.** Let $k(I)$ count the agent's own outgoing messages asserting
$I$, and $k^*$ a commitment threshold. When an untrusted source (τ(P|I)<0) sends a
disagreeing message and $k(I) \ge k^*$, the delta is further amplified by a defiance
factor π ≥ 1, applied on top of any negativity-bias adjustment already made:

$$\Delta\beta''(I)\vert_t = \begin{cases} \pi \cdot \Delta\beta'(I)\vert_t & \tau(P\vert I)<0 \wedge \text{disagreement} \wedge k(I) \ge k^* \\ \Delta\beta'(I)\vert_t & \text{otherwise} \end{cases}$$

π=1 recovers the prior stage unchanged. **Composition order**: negativity bias is
unconditional and always evaluated first (Δβ→Δβ'); doubling-down defiance is conditional
and evaluated second, layered on top of whatever Δβ' already is (Δβ'→Δβ''), rather than
competing with it. $\Delta\beta''(I)$ is the quantity that finally enters the
reluctance-damped update in Section 3.3. Motivated by Brehm's (1966) theory of
psychological reactance: a perceived threat to an already-committed position produces a
motivational push in the opposite direction of the threat, beyond what the content of the
counter-argument alone would justify. Both π and $k^*$ are drawn per agent (Section 3.6),
not fixed globally — see Section 4.7 for the analytical consequence of this choice.

[TODO: default value for χ and θ still needs pre-registration/calibration before use in the
run matrix — see checklist.]

### 3.8 New information: arrival, orphans, and revelation

Sections 3.2–3.3 describe how an *already-known* proposition's belief updates on receipt of
a new message. This section covers a proposition $I$ that is new to the receiving agent —
whether axiomatic or composite.

**Arrival.** With no prior belief to blend against, $\beta(I)$ is set directly from the
message and the trust already held in its source:

$$\beta(I)\vert_{\text{arrival}} = \nu \cdot \tau(P\vert I)$$

**Orphan status.** If $I$ is composite and its operands are not yet known to the agent, $I$
is stored as a **nodal (orphan)** entry — structurally a leaf in the agent's DAG, despite
being semantically composite. For orphans, $\omega(I) := \beta(I)$ by convention, so the
ordinary machinery in Sections 3.2–3.3 does not need a special case to handle an orphan; it
simply has no internal structure to draw on yet.

**Revelation.** When both of $I$'s operands become known to the agent — whether at the
moment of arrival or via a later message — the structurally-derived value is computed using
Table 1's fuzzy resolution, applied to $I$'s two operands $I_{\text{left}}, I_{\text{right}}$:

$$\omega_{\text{struct}}(I) = \text{Fz}\left(\text{expr}(I),\ \beta(I_{\text{left}}), \beta(I_{\text{right}})\right)$$

**Satisfaction check.** Whether the newly-revealed structure agrees with the belief already
held in $I$ (from its direct assertion) determines whether reluctance dampens or reinforces:

$$\text{satisfies}(I) = \left[\text{sign}\big(\omega_{\text{struct}}(I)\big) = \text{sign}\big(\beta(I)\big)\right]$$
$$\Delta\beta_{\text{reveal}}(I) = \omega_{\text{struct}}(I) - \beta(I)$$
$$\beta(I) \leftarrow \beta(I) + \begin{cases} \gamma(I) \cdot \Delta\beta_{\text{reveal}}(I) & \text{satisfies}(I) \\ \Delta\beta_{\text{reveal}}(I) \, / \, \gamma(I) & \text{otherwise} \end{cases}$$

This is a bidirectional use of $\gamma$, distinct from its role in Section 3.3: when
structural derivation **confirms** the direction already held from the source's assertion,
$\gamma \ge 1$ acts as a **multiplier**, compounding two independent lines of evidence (the
direct claim and the derived computation) — loosely analogous to how independent confirming
evidence compounds under Bayesian updating, though nothing in this model is literally
Bayesian. When structural derivation **contradicts** the standing belief, $\gamma$ plays its
original role as a **divisor**, dampening the resulting swing. After revelation, $I$ is
promoted from orphan to fully structured, and ordinary $\omega(I)$ computation (Section 3.2)
governs it from that point forward.

**Self-discovery and the evolving trust in one's own observation.** Some information
arrives not from another agent but from direct discovery — an agent encountering a seeded
axiom in the environment (Section 4.11). This is modeled as an ordinary message
$\langle \text{SELF}, I, \nu \rangle$, with SELF treated as an ordinary entry in the
publisher set $P$ from Section 3.2, not a special case with its own equations. Trust in
one's own observation is seeded high but not fixed, and is not assumed immune to erosion:

$$\tau(\text{SELF}\vert I)\vert_{\text{discovery}} \sim \text{Beta}(a{=}2, b{=}2) \text{ scaled to } [.25, .5]$$

From that point on, $\tau(\text{SELF}\vert I)$ evolves under the same Alpha Flux equation
as trust in any other source (Section 3.2), with $\varphi(I\vert\text{SELF})$ fixed
permanently at $\nu_{\text{discovery}}$, since SELF sends no further messages after the
initial observation:

$$\Delta\tau(\text{SELF}\vert I)\vert_t = \mu \cdot \left(\varphi(I\vert\text{SELF}) - \beta(I)\vert_t\right)$$
$$\tau(\text{SELF}\vert I)\vert_t = S_n\left(\tau(\text{SELF}\vert I)\vert_{t-1} + \Delta\tau(\text{SELF}\vert I)\vert_t\right)$$

If the population's evolving belief $\beta(I)$ drifts away from what the agent originally
observed, self-trust erodes, as the gap between the fixed original observation and the
moving current belief widens; if subsequent testimony and internal logic continue to align
with the original observation, self-trust is reinforced. This is a direct computational
parallel to Asch's (1955) classic finding that individuals' confidence in their own
unambiguous, directly-perceived observations can be eroded by contrary social consensus —
here formalized not as a separate mechanism but as the ordinary consequence of treating
self-observation as one trust relationship among many, rather than as categorically
immune to revision.

**Binarization requirement.** The satisfaction check above assumes exactly two operands per
composite. Any n-ary composite ($n>2$) in a domain's axiom hierarchy (Section 4.3) must be
rewritten as nested binary composites before this mechanism applies — e.g., $I_0 \wedge I_3
\wedge I_8$ becomes $(I_0 \wedge I_3) \wedge I_8$, introducing an intermediate DAG node.
This is lossless for MIN/MAX (both associative) and required for the vectorized
implementation described in Section 4.9. [TODO: several existing domain axiom documents
(Sections 4.3) contain flat n-ary composites and need this rewrite — see checklist.]

### 3.9 Composite trust derivation

Source dissertation Section 7.4.3 defines a second, distinct structural-derivation
mechanism, parallel to but separate from the orphan/revelation mechanism above: trust in a
publisher regarding a *composite* proposition can itself be derived from trust in that same
publisher across the composite's underlying axioms, via Table 1's fuzzy resolution:

$$\tau(P\vert I) = \text{Fz}\left(\text{expr}(I),\ \tau(P\vert I_{\text{left}}),\ \tau(P\vert I_{\text{right}})\right)$$

This is computed the first time it is needed — e.g., when $P$'s contribution to
$\alpha(I)$ (Section 3.2) is required but no direct trust value $\tau(P\vert I)$ has ever
been established from an actual message — and only when $P$'s trust is already known on
both of $I$'s operands. Once computed, the value is **stored as an ordinary trust entry**
and evolves from that point forward via the standard Alpha Flux equation (Section 3.2)
like any directly-established trust, rather than being recomputed via Fz on every
subsequent use. This mirrors the orphan/revelation pattern above: a value that begins as a
structurally-derived fallback is promoted to ordinary, independently-evolving state once
computed, rather than remaining permanently dependent on its derivation.

Note the direction of dependency relative to belief revelation: composite trust derivation
requires the publisher's trust on *both* operands to already exist; belief revelation
requires the agent's own belief on both operands to already exist. The two mechanisms can
therefore become available at different times for the same composite proposition,
depending on whether the agent's own beliefs or its trust data on a given publisher
completes first.

---

## 4. Methods

### 4.1 Simulation engine

FREE WILL is implemented as a Mesa-based agent-based model on a toroidal grid. A tick is
the fundamental unit of simulated time: within a single tick, every eligible agent
participates in exactly one pairwise idea exchange, with exchange order randomized per run.

### 4.2 Flowback

On receipt of a message targeting proposition $I$, updates propagate to $I$'s antecedents
and consequents in the DAG, in addition to the update on $I$ itself.

**Antecedents (Omega Flux).** For each antecedent $I_a$ of $I$:

$$\Delta\omega(I_a)\vert_t = \mu \cdot \left(\omega(I_a)\vert_{t-1} - \beta(I)\vert_t\right)$$
$$\omega(I_a)\vert_t = S_n\left(\omega(I_a)\vert_{t-1} + \Delta\omega(I_a)\vert_t\right)$$

Note the asymmetry with Alpha Flux (Section 3.2): the comparison term is the *target's*
belief $\beta(I)$, not the antecedent's own — this is what makes the update a genuine
flowback, pulling the antecedent's internal-logic term toward consistency with what just
changed downstream, rather than an independent update to $I_a$ in its own right.

**Consequents (Psi Flux).** The change propagated to a consequent $I_c$ of $I$:

$$\Delta\psi(I_c \vert I)\vert_t = \mu \cdot \Delta\omega(I)\vert_t$$
$$\omega(I_c)\vert_t = S_n\left(\omega(I_c)\vert_{t-1} + \Delta\psi(I_c\vert I)\vert_t\right)$$

(Renamed from the source dissertation's "Gamma Flux" — see Section 3.4 notation table. The
consequent-update equation was not explicit in the source material and is added here by
direct structural parallel with the antecedent-update pattern above.)

### 4.3 Concept domains

Ten concept domains are simulated (full axiom hierarchies in the accompanying domain
documents), spanning four categories:

| Category | Domains |
|---|---|
| Empirically resolvable, consensus contested | Flat Earth, Moon landing, Climate change, Vaccine–autism link |
| Historical/conspiratorial | JFK assassination theories |
| Empirically resolvable, genuinely mixed evidence | Alternative medicine efficacy, Minimum wage employment effects |
| Normative/value-based | Political leanings, Religious belief, Gender identity and its social/legal recognition |

Each domain's root axioms and Boolean composites are documented separately (10
domain-specific axiom-hierarchy files).

### 4.4 Experimental conditions and run allocation

Population-stability (Section 4.3's agent-parameter reuse) and seeding/influencer
conditions are fully crossed, not run as separate sweeps, so that H5/H6 (population
stability) and H2/H3/H9/H10 (seeding and influencer effects) can be tested from the same
data without confounding one with the other.

| | Fully balanced | First-half balanced | Last-half balanced | Fully random | Influencer |
|---|---|---|---|---|---|
| **Fixed** | 20 | 20 | 20 | 20 | 20 |
| **Semi-fixed** | 20 | 20 | 20 | 20 | 20 |
| **Random** | 20 | 20 | 20 | 20 | 20 |

15 cells × 20 runs = **300 runs per domain**, × 10 domains = **3,000 core runs**, plus 30
mixed-topic runs (Section 4.5) = **3,030 runs total** ("Recommended" tier — 20 runs/cell,
consistent with the 20–30-seeds-per-condition standard already established for trusting a
mean in this design). Each run: 300–500 agents, 1000 ticks.

**Population-stability × influencer interaction (resolved).** Under Fixed
population-stability, both the belief-coefficient tuples *and* the influencer designation
and agenda ($I_a$, $\nu_a$) persist across runs for the same 5 agents — everything about
these agents is reused except memory, which resets each run per the general Fixed
definition (Section 4.3). Under Semi-fixed and Random, influencer designation is redrawn
along with everything else.

Conditions:
- **Fixed / Semi-fixed / Random** (rows): as originally defined — same tuples reused with
  memory reset, 50% reused/50% fresh, or fully fresh draws each run, respectively. This
  now extends explicitly to influencer designation and agenda under Fixed, as above.
- **Fully balanced / First-half balanced / Last-half balanced / Fully random / Influencer**
  (columns): as defined in Section 4.6 below.

This design intentionally supersedes an earlier draft that ran population-stability and
seeding/influencer as two separate, non-crossed sweeps at a smaller combined budget — see
decisions log for the correction history.

### 4.5 Mixed-topic condition

30 runs (Recommended tier — increased from an earlier 10-run proposal, since more seeds
here directly tighten the bootstrapped null H7 is tested against) seed all ten domains'
axioms into one shared population and grid, using the Random parameter condition. Cluster
membership is computed independently per domain, then cross-tabulated per agent for the H7
test against the Converse null.

### 4.6 Seeding and influencer conditions (detail)

The five column conditions from Section 4.4's factorial. "First-half balanced" and
"last-half balanced" are confirmed as a **temporal** manipulation — the order in which
balanced vs. skewed information arrives, holding total seed composition fixed — rather
than a compositional split of the axiom set. This is the reading H9 is built to test.

**Influencer mechanism.** Exactly 5 agents per run are designated influencers. Popularity
and agenda-scripting are bundled into a single role, not independent properties:

- **Reach**: an influencer sends its message to $R$ distinct agents per tick, rather than
  the single pairwise exchange every ordinary agent is limited to (Section 4.1) — an
  explicit, scoped exception to the tick rule for these 5 agents only. $R$ ranges 20–50
  agents; a single representative value within this range is selected via the
  expectation-vs-reality validation pass (Section 4.10) rather than swept as an additional
  factorial dimension, to avoid multiplying the core run budget further.
- **Agenda-scripted messaging**: each influencer is assigned one agenda proposition $I_a$
  and a fixed outgoing confidence $\nu_a$. Whenever its outgoing message targets $I_a$, it
  transmits $\nu_a$ regardless of its own computed belief $\beta(I_a)$. For every other
  proposition, messaging proceeds normally, computed from the influencer's actual internal
  state. The influencer's memory model updates on receipt of messages exactly like any
  ordinary agent — including on $I_a$ itself — so an influencer may hold an accurate
  private belief about its own agenda proposition while always transmitting the scripted
  position.
- **Mixed-bag composition**: influencers are single-agenda individually, but a run may
  contain influencers pushing different, competing agendas simultaneously rather than every
  influencer in a run sharing one message.

### 4.7 Metrics

- Belief distribution: mean and variance of β(I) per axiom.
- **Belief-network clustering**: belief-similarity graph per domain (edge weight = β(I)
  vector similarity), partitioned via Louvain modularity maximization.
- **Trust-network clustering**: independent graph per domain (edge weight = mutual
  τ(P|I)), partitioned via the same Louvain procedure.
- **Belief/trust partition agreement**: NMI/ARI between the two partitions per domain (H8).
- **Saturation curve**: percentage of the population that has discovered a given axiom $I$
  (Section 3.8), tracked per tick — distinct from, and a precondition for, stabilization.
- **Time-to-stabilization**: for axiom $I$, the first tick $t$ at which (a) saturation of
  $I$ exceeds 90% of the population, and (b) the population-mean $|\Delta\beta(I)|$ over a
  trailing window of $W{=}50$ ticks remains below $\varepsilon_{\text{stab}}{=}0.01$ for
  the remainder of the run. Condition (a) prevents mistaking "nothing left to discover" for
  "consensus reached"; condition (b) is a standard windowed-convergence criterion, scaled
  relative to $\beta$'s own [−.5,.5] range rather than an arbitrary absolute cutoff.
- **Polarization index**: reported as two complementary measures rather than one — variance
  of $\beta(I)$ across the population (simple, standard) and a bimodality coefficient
  (detects "split into two camps" structure that variance alone can miss). Bimodality is
  treated as the primary claim for H9/H10, since both hypotheses are fundamentally about
  whether structure/factions emerge, not merely whether disagreement exists; variance is
  reported as a supporting check.
- **Spatial clustering**: agent grid-position clusters (Section 4.11), for comparison
  against belief- and trust-network clusters (H11).
- Cross-domain cluster membership matrix (mixed-topic condition only, feeds H7).

### 4.8 Statistical analysis plan

| Hypothesis | Test |
|---|---|
| H1 | ANOVA/Kruskal-Wallis on stabilization time and final polarization across 10 domains |
| H2/H3 | Compare consensus speed between symmetric- and asymmetric-seeded runs |
| H4 | Regression of final belief magnitude for low-ω-support axioms on λ |
| H5 | Levene's test for equality of variance across Fixed/Semi-fixed/Random |
| H6 | t-test/ANOVA on means across the same three conditions |
| H7 | Observed cross-domain cluster correlation vs. bootstrapped null |
| H8 | NMI/ARI vs. permutation-based null |
| H9 | Compare final consensus between first-half-balanced and last-half-balanced conditions, holding total seed composition fixed (paired comparison per domain) |
| H10 | Compare final consensus/polarization in the influencer condition vs. the fully-random condition; decompose by agenda direction (A vs. B) where multiple agendas coexist |
| H11 | Hierarchical/recursive community detection on hub-and-spoke structures, testing for measurable sub-cluster differentiation among agents sharing a common highly-trusted center, beyond what flat modularity (Section 4.7) captures |
| H12 | Topic entropy of ℓ(A,P) history over time per agent pair, compared against a randomized-topic-choice null; partial correlation/regression checking specialization isn't redundant with existing belief/trust cluster co-membership |

Effect sizes and confidence intervals are reported throughout, not p-values alone.

**Note on defiance decomposition**: π (defiance amplification) and $k^*$ (commitment
threshold, Section 3.7) are both drawn per agent rather than fixed globally. Any observed
effect attributable to doubling-down defiance must therefore be decomposed via regression
on π and $k^*$ as separate covariates, logged per agent per run — a single "defiance
on/off" comparison is not meaningful here, since the mechanism's strength and its
activation threshold vary independently across the population.

### 4.9 Vectorized implementation

The per-agent equations in Section 3 are implemented as sparse matrix/tensor operations
over the full population at once, not as per-agent loops, given the compute cost of 3,000+
runs at 300–500 agents × 1000 ticks (Section 4.4).

**Core data structures**: a belief matrix $\mathbf{B}$ (agents × propositions, sparse —
most agents have not encountered most propositions at any given time), a trust tensor
(agents × sources × propositions, sparser still, since it requires two specific agents to
have interacted on a specific topic), a per-tick communication matrix (agents × agents,
0/1, row sums 1 for ordinary agents and $R$ for influencers per Section 4.6), and two DAG
adjacency matrices — consequents and antecedents — precomputed once and shared across the
whole population, since the proposition structure itself does not vary by agent.

**What vectorizes cleanly**: reluctance (Section 3.3) and flowback (Section 4.2) both
reduce to a single sparse matrix multiplication against the precomputed DAG adjacency,
followed by elementwise operations, for the entire population simultaneously — the
DAG-walking cost depends only on the number of propositions and the DAG's own sparsity, not
on population size. The orphan/revelation mechanism (Section 3.8) reduces similarly: the
trigger condition is a single elementwise boolean AND across sparse matrices (orphan status
× both operands known), and the satisfaction-check update is pure elementwise arithmetic
once triggered rows are gathered — this is what makes the binarization requirement in
Section 3.8 necessary, since a fixed-width two-column operand gather only works for binary
composites.

**What does not fully vectorize**: the ad hominem drift / halo-effect leak (Section 3.7)
requires, for each touched (receiver, source) pair in a tick, that pair's entire existing
trust row across all propositions — a genuinely irregular per-pair sparse support set with
no shared, precomputable structure underlying it, unlike the DAG. This is still implemented
as a batched sparse row-gather/scatter over all pairs touched in a tick, not a Python-level
loop, but it is not reducible to a single global matrix multiplication the way reluctance
and flowback are.

### 4.10 Expectation-vs-reality validation pass

Before the full 3,030-run factorial matrix (Section 4.4) is executed, a small pilot batch —
outside the core budget — is run once implementation is complete, structured as a
pre-registered prediction exercise rather than an open-ended exploratory check:

1. For each still-undetermined or newly-introduced mechanism (χ, θ, π, the influencer reach
   parameter $R$, the exploration rate $\varepsilon_{\text{explore}}$, the stay-threshold
   $\tau_{\text{still}}$, and any other coefficient without a directly-measured real-world
   analogue), the expected qualitative direction and rough magnitude of effect is stated in
   writing *before* any pilot run — grounded in the theoretical motivation already given in
   Sections 3.7 and 4.6, not fitted after the fact.
2. Pilot instances are run at the extremes and midpoint of each coefficient's range.
3. Observed behavior is compared explicitly against the stated expectation: confirmed,
   partially confirmed, or disconfirmed.
4. Any mechanism whose observed behavior diverges substantially from its stated expectation
   is flagged for a design review before being committed to the full run matrix at scale —
   this catches a vanishing, exploding, or otherwise misbehaving mechanism early, but the
   documented comparison itself (not just the catch) is treated as a result worth reporting
   in Discussion, since a mechanism that fails to match its own theoretical motivation is as
   informative as one that succeeds.

### 4.11 Grid and movement mechanics

**Personal Affinity.** For agent $A$, let $N_A$ be the set of every other agent $A$ has
interacted with (and therefore holds trust data for, and can track the position of). For
each $P \in N_A$, the mean trust across whichever leaf/axiomatic propositions $A$ holds
trust data on regarding $P$:

$$\bar{\tau}(A,P) = \frac{1}{|L_{A,P}|}\sum_{I \in L_{A,P}} \tau_A(P\vert I)$$

The Personal Affinity vector:

$$\text{PA}(A) = \sum_{P \in N_A} \bar{\tau}(A,P) \cdot \widehat{(\text{pos}(P) - \text{pos}(A))}$$

is recomputed every tick from $A$'s current trust state, entirely from $A$'s own
accumulated experience — nothing external or omniscient. A trusted $P$ ($\bar\tau>0$)
pulls $\text{PA}(A)$ toward it; a distrusted $P$ ($\bar\tau<0$) actively repels it, both
falling directly out of allowing $\bar\tau$ to be signed, with no separate repulsion rule.

**Action space.** 8 discrete directions (full Moore neighborhood). Movement follows an
**ε-greedy exploration/exploitation rule** (Sutton & Barto, 2018) rather than pure argmax,
restoring some of the stochasticity present in the source dissertation's original softmax
action selection without reopening the full per-tick probabilistic redesign that would
compromise the sequence-sensitivity check's assumption of history-determinism:

$$\hat{d}(A) = \begin{cases} \text{uniform random direction} & \text{with probability } \varepsilon_{\text{explore}} \text{ (explore)} \\ \arg\max_{\hat{d}} \text{PA}(A)\cdot\hat{d} & \text{with probability } 1-\varepsilon_{\text{explore}} \text{ (exploit)} \end{cases}$$

**Stay option.** Restoring the source dissertation's original stay-in-place possibility
(dropped when the action space was reduced to 8 pure-movement directions): if $A$'s
*normalized* affinity magnitude is below a small threshold, its net trust-weighted pull is
too weak or too self-cancelling to justify committing to any direction, and $A$ stays in
place for the tick instead of being forced through argmax or ε-greedy selection among
options that aren't meaningfully preferred:

$$\overline{\text{PA}}(A) = \text{PA}(A) \,/\, |N_A|, \qquad \text{stay if } |\overline{\text{PA}}(A)| < \tau_{\text{still}}$$

This check is applied before the exploration/exploitation rule above — an agent only
chooses between exploring and exploiting once it has a non-negligible directional signal
to exploit in the first place. If $N_A=\emptyset$ (no interactions yet), $\text{PA}(A)$ is
undefined entirely and $A$ performs a uniform random walk among the 8 directions
(unchanged from the original cold-start rule) until its first interaction gives it
something to compute against.

[TODO: $\varepsilon_{\text{explore}}$ and $\tau_{\text{still}}$ are new undetermined
coefficients, not yet assigned values — routed through the Section 4.10
expectation-vs-reality validation pass alongside $R$, rather than guessed here. Proposed
starting ranges for that pass: $\varepsilon_{\text{explore}} \in [0.05, 0.15]$ (standard
small-value ε-greedy per Sutton & Barto, 2018), $\tau_{\text{still}} \in [0.02, 0.1]$ on
the normalized affinity scale.]

**Movement collision resolution.** If two or more agents select the same destination cell
in a tick, priority goes to whichever agent has the higher dot-product score
$\text{PA}(A)\cdot\hat{d}$ for that move — the agent with the stronger directional
conviction enters first, regardless of whether that move was chosen via exploitation or
landed there by chance during exploration. Exact ties are broken by random selection
(expected to be rare, since $\text{PA}$ is a continuous, agent-specific quantity). Agents
that lose priority remain in their current cell for the tick rather than cascading to a
secondary choice, avoiding compounding conflict-resolution complexity.

**Landing consequences (automatic, not separately chosen).** Movement is the only *chosen*
action; discovery and conversation are consequences of where an agent ends up, not
competing actions in a softmax selection the way the source dissertation's original
Move/Discover/Converse trichotomy worked. If the destination cell contains a seeded axiom,
discovery triggers automatically (Section 3.8's arrival mechanism). Conversation triggers
automatically with every other agent present in the resulting neighborhood:

$$\text{reach}(A,t) = \max\left(\text{baseline}(A),\ K(A,t)\right)$$

where $K(A,t)$ is the number of other agents present after $A$ moves, and baseline is 1 for
ordinary agents or $R$ for influencers (Section 4.6) — `max`, not summation, so an
influencer landing in an already-crowded cell does not receive an implausible double boost.
This is a genuinely new, *emergent and situational* source of variable reach, distinct from
the influencer's fixed, scripted reach: it arises entirely from where agents' own
affinity-driven movement happens to converge, not from any designed property of the agent
itself. This is also the structural mechanism behind H11: agents converging on a shared,
highly-trusted hub do not need to be simultaneously present to build trust with each other
— they build it incidentally, at different times, whenever their own independent movement
happens to bring them into the same crowded cell, allowing their interpersonal trust matrix
to diverge freely from their shared trust in the hub.

**Tick sequence, in full**: (1) compute $\text{PA}(A)$ for every agent from the current
trust state; (2) resolve intended moves via the collision rule above; (3) trigger discovery
and/or conversation automatically based on each agent's resulting position; (4) for each
triggered conversation, determine outgoing message content via Section 4.12; (5) apply the
resulting belief and trust updates (Sections 3.2, 3.8); (6) tick ends.

**Note on generality**: this movement mechanic assumes a discrete, uniform grid; the
underlying Personal Affinity vector computation does not depend on a fixed 8-direction
discretization and could extend to a continuous or non-uniform terrain in future work,
substituting a different discretization or none at all.

### 4.12 Message formulation

Sections 3.2 and 3.8 describe how a *received* message updates belief and trust. This
section describes how the *content* of an outgoing message is chosen — which proposition a
speaking agent raises, and with what confidence — when a conversation is triggered
(Section 4.6, 4.11). This is decided independently per recipient when a single tick's
reach touches multiple agents (Section 4.6).

**Agenda override (highest priority).** If speaking agent $A$ is an influencer (Section
4.6) with agenda proposition $I_a$ and scripted confidence $\nu_a$: $I_{\text{chosen}} =
I_a$, $\nu = \nu_a$, unconditionally — restating Section 4.6's definition as the top-
priority branch of the general policy below, regardless of audience or own knowledge.

**Otherwise**, let $\text{Topics}(A) = \{I : \beta_A(I) \text{ is defined}\}$ (everything
$A$ currently holds any belief on), and let $\ell(A,P)$ denote the most recent proposition
$A$ has previously raised with recipient $P$ specifically (undefined if no prior
interaction with $P$):

$$I_{\text{chosen}} = \begin{cases} \displaystyle\arg\max_{I \in \text{Topics}(A)} |\beta_A(I)| & \text{w.p. } \varepsilon_{\text{topic}} \text{ (explore), or if } \ell(A,P) \text{ undefined} \\ \ell(A,P) & \text{otherwise (exploit — prior channel with } P \text{ exists)} \end{cases}$$

$$\nu = \beta_A(I_{\text{chosen}})$$

The agent reports its own genuine belief honestly — only the agenda-override branch
involves misrepresentation. After the exchange, $\ell(A,P) \leftarrow I_{\text{chosen}}$.

This produces three distinct behaviors, matching the motivating description directly:
- **Exploration, or first contact with $P$**: $A$ leads with its single most strongly-held
  belief overall — its "signature topic" — even if it also holds other, less confident
  beliefs. An agent whose strongest conviction is political leads with politics even when
  it also has scientific knowledge to draw on.
- **Exploitation of an established channel**: $A$ continues whatever topic it has
  previously discussed with this specific $P$, even when that is not $A$'s overall
  strongest topic — an agent whose strongest overall conviction is political but who has an
  established physics-discussion history with this particular recipient continues
  discussing physics with them specifically.
- **Agenda holders**: bypass audience and self-knowledge entirely, always pushing their
  scripted agenda regardless of context.

This is a direct computational analog of Bell's (1984) audience design theory: speakers do
not choose what to say independent of who they are speaking to, but continuously adapt
content to their relationship with a specific addressee, layered here on top of the
agent's own knowledge base (which topics it holds beliefs on at all) and, where present,
an overriding agenda — matching the three drivers named in the motivating description
(audience, agenda, own knowledge).

[TODO: whether $\varepsilon_{\text{topic}}$ is the same draw as $\varepsilon_{\text{explore}}$
(Section 4.11) — tying spatial and topical exploration into one personality trait — or an
independent coefficient (allowing an agent to be spatially exploratory but topically
consistent, or vice versa) is an open design fork, not yet decided. Routed through the
Section 4.10 validation pass as a separate undetermined coefficient by default, pending
confirmation.]

---

## 5. Discussion

### 5.1 On unpruned logical incoherence

FREE WILL's memory model does not enforce logical consistency on an agent's accumulated
beliefs. This is a deliberate design position, not an oversight, and follows directly from
a structural property of fuzzy resolution demonstrated during model development: a direct
self-contradiction ($I \wedge \neg I$) does not evaluate to an error state or a null value
under Table 1's resolution rules — it evaluates to $-|x|$, a confident-looking number
indistinguishable in form from any ordinary composite belief. Nothing in the fuzzy
substrate flags, prunes, or down-weights the result. Left unaddressed across many ticks, an
agent's belief DAG can accumulate an arbitrarily large set of formally contradictory
composites, each carrying its own plausible confidence value, propagating through
consequents via flowback (Section 4.2) exactly as any coherent belief would.

Two positions are available in response to this. The first treats it as a defect: since the
model can produce demonstrably inconsistent belief sets, an explicit consistency-checking
mechanism, independent of the reluctance function γ, should periodically scan and resolve
contradictions. The second treats it as a feature: bounded, situated cognitive agents —
biological or artificial — are not obligated to maintain global logical consistency across
everything they believe, and a model that forced this would be modeling an idealized
reasoner, not a realistic one. FREE WILL adopts the second position.

The philosophical grounding for this is Makinson's (1965) preface paradox: an author who
asserts each individual claim in a book while also, in good faith, writing in the preface
that the book surely contains at least one error holds a set of beliefs that is collectively
inconsistent while every member of that set is individually well-justified. Makinson's
example demonstrates that collective inconsistency across a large belief set is compatible
with each individual belief being rational — inconsistency at the level of the whole is not
automatically a failure at the level of the parts. This is precisely the situation FREE
WILL's agents are permitted to be in: each individual $\beta(I)$ is computed from a
well-defined trust-weighted consensus and fuzzy-logical process (Section 3.2), while the
resulting global belief graph is not guaranteed, and not required, to be consistent.

This position also has a formal-logic precedent: paraconsistent logics are explicitly
designed so that a contradiction does not entail the derivability of every other statement
(ex contradictione quodlibet), unlike classical logic (Priest, Tanaka, & Weber, 2022).
Fuzzy resolution's behavior in FREE WILL — assigning contradictions a defined numeric value
rather than treating them as universally explosive — functions similarly in practice,
though it was arrived at as a byproduct of the fuzzy formalism rather than as a deliberately
designed paraconsistent system; this distinction is worth stating precisely rather than
overclaiming a formal paraconsistency result that hasn't been proven here.

The counterargument deserves to be stated plainly rather than dismissed: cognitive
dissonance theory (Festinger, 1957) documents that humans experience genuine psychological
discomfort from inconsistency and are motivated to reduce it — typically not through
logical resolution, but through rationalization, selective exposure, or attitude change.
FREE WILL does not model this drive at all; an agent experiences no analog of dissonance and
takes no action to resolve or even notice its own contradictions. This is a genuine
simplification relative to human cognition, not a fully-argued equivalence to it — the
model captures the *outcome* documented in the preface paradox (coherent-seeming agents can
hold globally inconsistent belief sets) without capturing the *mechanism* documented in
dissonance theory (active, sometimes uncomfortable management of inconsistency once
noticed). A closer model of human cognition would need something between the two positions
argued above: tolerance of inconsistency by default, with an occasional, costly,
dissonance-like process that surfaces and addresses a subset of it. FREE WILL does not
implement this middle position in the current formalism; the catalog of fallacy-based
reaction rules (Section 3.7) extends the model's psychological realism in a different
direction (biased *updating*) without addressing consistency *maintenance* at all — a gap
worth naming explicitly as a direction for future work rather than leaving implicit.

### 5.2 Empirical findings

[TODO: headline results once the 3,030-run factorial matrix (Section 4.4) completes —
organized by hypothesis: H1 (domain generalization), H2/H3 (seeding asymmetry), H4 (κ/λ
effect on unsupported information), H5/H6 (population-stability gradient and its
robustness), H7 (cross-domain constraint), H8 (belief/trust decoupling), H9 (order
effects), H10 (influencer effect, read against the Kempe et al./Watts & Dodds tension).]

### 5.3 Limitations

[TODO: incorporate — (1) the Beta-distributed parameter assumption (Section 3.6), covering
all eight coefficients (λ, μ, η, ξ, σ, χ, θ, π) as stated, not derived, modeling choices,
with the robustness-check results once run — χ, θ, π were explicitly folded into this same
check rather than calibrated separately (see decisions log); (2) results of the
expectation-vs-reality validation pass (Section 4.10) — which mechanisms confirmed their
theoretical motivation and which diverged, reported as a substantive finding rather than
just an implementation sanity check; (3) the fallacy-based extensions (Section 3.7) as a
curated subset of a larger candidate catalog, with the four unformalized candidates
(bandwagon spike, availability cascade, echo silence, sunk-cost entrenchment) noted as
future work; (4) the assumptions introduced during formalization that were not present in
the original source material (the IMPLIES resolution rule, the σ→n mapping, the temporal
reading of first-half/last-half balanced seeding) as places a different reasonable choice
could have been made.]

---

## References

Alchourrón, C. E., Gärdenfors, P., & Makinson, D. (1985). On the logic of theory change:
Partial meet contraction and revision functions. *Journal of Symbolic Logic*, 50(2), 510–530.

Asch, S. E. (1955). Opinions and social pressure. *Scientific American*, 193(5), 31–35.

Baumeister, R. F., Bratslavsky, E., Finkenauer, C., & Vohs, K. D. (2001). Bad is stronger
than good. *Review of General Psychology*, 5(4), 323–370.

Bell, A. (1984). Language style as audience design. *Language in Society*, 13(2), 145–204.

Brehm, J. W. (1966). *A Theory of Psychological Reactance*. Academic Press.

Converse, P. E. (1964). The nature of belief systems in mass publics. In D. E. Apter (Ed.),
*Ideology and Discontent*. Free Press.

Deffuant, G., Neau, D., Amblard, F., & Weisbuch, G. (2000). Mixing beliefs among interacting
agents. *Advances in Complex Systems*, 3(01n04), 87–98.

DeGroot, M. H. (1974). Reaching a consensus. *Journal of the American Statistical
Association*, 69(345), 118–121.

Eagly, A. H., Wood, W., & Chaiken, S. (1978). Causal inferences about communicators and
their effect on opinion change. *Journal of Personality and Social Psychology*, 36(4),
424–435.

Festinger, L. (1957). *A Theory of Cognitive Dissonance*. Stanford University Press.

Hegselmann, R., & Krause, U. (2002). Opinion dynamics and bounded confidence models,
analysis, and simulation. *Journal of Artificial Societies and Social Simulation*, 5(3).

Hogarth, R. M., & Einhorn, H. J. (1992). Order effects in belief updating: The
belief-adjustment model. *Cognitive Psychology*, 24(1), 1–55.

Iyengar, S., Sood, G., & Lelkes, Y. (2012). Affect, not ideology: A social identity
perspective on polarization. *Public Opinion Quarterly*, 76(3), 405–431.

Iyengar, S., & Westwood, S. J. (2015). Fear and loathing across party lines: New evidence on
group polarization. *American Journal of Political Science*, 59(3), 690–707.

Jøsang, A. (2001). A logic for uncertain probabilities. *International Journal of
Uncertainty, Fuzziness and Knowledge-Based Systems*, 9(03), 279–311.

Jøsang, A. (2016). *Subjective Logic: A Formalism for Reasoning Under Uncertainty*.
Springer.

Kempe, D., Kleinberg, J., & Tardos, É. (2003). Maximizing the spread of influence through a
social network. In *Proceedings of the Ninth ACM SIGKDD International Conference on
Knowledge Discovery and Data Mining* (pp. 137–146).

Makinson, D. C. (1965). The paradox of the preface. *Analysis*, 25(6), 205–207.

Nisbett, R. E., & Wilson, T. D. (1977). The halo effect: Evidence for unconscious
alteration of judgments. *Journal of Personality and Social Psychology*, 35(4), 250–256.

Priest, G., Tanaka, K., & Weber, Z. (2022). Paraconsistent logic. In E. N. Zalta (Ed.),
*The Stanford Encyclopedia of Philosophy*.

Sutton, R. S., & Barto, A. G. (2018). *Reinforcement Learning: An Introduction* (2nd ed.).
MIT Press.

Walton, D. (1998). *Ad Hominem Arguments*. University of Alabama Press.

Walster, E., Aronson, E., & Abrahams, D. (1966). The effectiveness of debaters' arguing
against their own self-interest. *Journal of Experimental Social Psychology*, 2(4), 325–342.

Watts, D. J., & Dodds, P. S. (2007). Influentials, networks, and public opinion formation.
*Journal of Consumer Research*, 34(4), 441–458.

[TODO: add remaining source-dissertation citations for Mesa, ElasticSearch/Kibana as
appropriate for target venue.]

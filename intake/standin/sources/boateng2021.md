# Boateng & Sorensen — comparing steady-state and adaptive comfort models

> SYNTHETIC stand-in source. This work does not exist. Written for OwnVoice
> development (build step T4). No locator sidecar: grounding against this source
> must flag `needs_mapping`.

Boateng, K. & Sorensen, M. (2021). *Comparing steady-state and adaptive comfort models
against measured classroom data*. Journal of Synthetic Building Science, 14(2), 88-117.

The paper re-runs three comfort models over an existing measurement archive of 220
classroom-months. The models are a steady-state heat-balance formulation, an adaptive
formulation keyed to running mean outdoor temperature, and a hybrid that switches
between them by ventilation mode.

Across the whole archive the adaptive model reproduced occupant votes more closely than
the steady-state model, with mean absolute error of 0.61 against 0.94 scale points.
The advantage narrowed to 0.08 scale points in mechanically ventilated rooms, where the
authors say the adaptive assumption is least defensible.

Boateng & Sorensen argue that model choice is usually reported as a methodological
preliminary when it is in fact a substantive claim about how occupants adapt. They
recommend that any paper reporting predicted comfort state which model was used, over
what running mean window, and what was assumed about occupant control of openings.

The hybrid model performed best overall but the authors decline to recommend it. Its
switching rule was fitted on the same archive it was evaluated against, and no held-out
period was reserved, so the reported error is optimistic by an unknown margin.

Sensitivity analysis shows that the adaptive model's advantage disappears entirely if
the running mean window is shortened from thirty days to seven. The authors treat the
window length as the single most consequential undeclared parameter in the literature
they review.

The archive covers one climate zone. The authors state plainly that the comparison
should not be read as evidence about model performance in continental or tropical
settings, and that they were unable to obtain comparable data from other zones.

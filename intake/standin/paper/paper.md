# Thermal comfort evidence in retrofitted school buildings

> SYNTHETIC stand-in paper for OwnVoice development (build step T4). Not a real paper;
> every cited work is invented and lives in `../sources/`. Three sections: two
> contrasting ones for the arc-batched arm (argumentative + procedural) and one for the
> serial control. The citation set is deliberately mixed — resolvable, unresolvable, and
> one degenerate private-line-number citation.

## Why modelled comfort and reported comfort diverge

The standard justification for a fabric retrofit includes a comfort claim, and that
claim is usually supported by a model rather than by anything an occupant said. This is
defensible where the model has been validated against the building type in question, but
in the school estate it mostly has not been. Alvarez (2019) found that occupant votes
and modelled predictions disagreed in roughly a third of classroom-hours, and the
disagreement was not evenly distributed: occupants reported discomfort in conditions the
model called neutral about twice as often as the reverse.

It might be tempting to treat that asymmetry as survey noise. The pattern in the data
does not support such a reading. The divergence concentrated in rooms with large
south-facing glazing and in rooms whose ventilation had been commissioned but never
rebalanced after the retrofit (Alvarez, 2019), which is to say it concentrated exactly
where a whole-room heat balance would be expected to lose resolution. Where those
conditions were absent, model and vote agreed within one scale point in the large
majority of hours.

The choice of comfort model is itself a substantive claim rather than a methodological
preliminary (Boateng & Sorensen, 2021). An adaptive formulation outperformed a
steady-state one across their archive, but the advantage nearly vanished in
mechanically ventilated rooms, and it disappeared altogether when the running mean
window was shortened from thirty days to seven. A paper that reports predicted comfort
without stating its window length has not reported enough for the prediction to be
checked.

There is a further problem, which is that the evidence base does not yet support the
inference that most retrofit business cases draw from it. Okafor (2022) pooled 74
studies and found a positive but small association between retrofit and improved comfort
vote, with a prediction interval crossing zero, high unexplained heterogeneity, and
small-study effects consistent with selective reporting. Only nine of the studies were
pre-registered, so the confirmatory and exploratory findings can no longer be told apart
(Okafor, 2022a).

None of this means comfort claims should be abandoned. It means the claim a retrofit can
currently support is narrower than the one usually made: that the intervention changed
measured conditions, not that occupants experienced the change as an improvement.
Whitfield (2017) makes a similar argument about acoustic retrofits, and the parallel is
worth drawing out, though the comfort literature is further behind on measurement
practice than the acoustic one.

The practical consequence is that a single post-occupancy survey in one season should
not be read as evidence of comfort performance, and that any change to ventilation
control settings should trigger a repeat survey (Alvarez, 2019). This is a modest
requirement, and it is not currently met by most of the estate.

## Measurement protocol

This section sets out the instrumentation and sampling procedure used in the present
study. It follows the practitioner handbook (Dimitrova et al., 2020) except where noted,
and departures are recorded with their reasons.

Sensors were positioned at seated head height, 1.1 m above finished floor level, no
closer than 1 m to an external wall and 0.5 m to a supply diffuser. Each position was
photographed at installation and the photograph filed with the room record, because
placement that is reconstructed after the fact is the most common cause of an unusable
archive (Dimitrova et al., 2020).

Globe temperature readings were taken only after a settling period of at least twenty
minutes following any repositioning. Readings within the settling period were discarded
rather than corrected. In sunlit rooms an uncorrected in-period reading biases the mean
radiant estimate upward, and no correction that we are aware of has been validated for
classroom geometries.

Logging ran at five-minute intervals for two consecutive teaching weeks in each of the
heating and cooling seasons, with at least one week in each season falling outside a
holiday period. Both occupied and unoccupied hours were retained; unoccupied hours were
used to characterise the passive response of each room and were excluded from the
comfort analysis.

Instruments were calibrated against a reference before deployment and again after
recovery. Where post-deployment drift exceeded the handbook tolerance, that instrument's
season of data was flagged and excluded from the pooled analysis; two of the fourteen
loggers were excluded on this basis.

Occupancy was counted directly by the class teacher on a paper tally, and not inferred
from CO2 concentration. Inference from CO2 alone is sensitive to ventilation rate, which
is the variable under study here (see pretorius2018.md line 412), so an independent count
was necessary.

Comfort votes were timestamped to the minute and matched to the nearest logged interval.
Votes were collected on tablets in both seasons; the paper administration mode used in
earlier work was not repeated, since it produced more partially completed forms without
any detectable difference in mean vote (Alvarez, 2019).

Teachers were the respondents throughout. Pupil votes were not collected, which limits
comparability with studies reporting pupil samples and is revisited in the limitations
below.

## What the evidence base cannot yet settle

Two limits of the present design should be stated before any of its results are read as
support for a retrofit strategy. The first is that a single climate zone is represented,
and the second is that the follow-up window is short relative to the process the study
is trying to observe.

The first limit is shared with the comparison literature. Boateng & Sorensen (2021)
restrict their model comparison to one climate zone and say plainly that it should not
be read as evidence about continental or tropical settings. The same restriction applies
here, and it applies more sharply because the sample of schools is smaller.

The second limit is more consequential. Pretorius (2018) followed 18 schools for three
years and found that most performance loss occurred after handover rather than at it:
twelve had a control setting changed by site staff with no record of the change, and in
seven of those the change defeated the demand-controlled strategy the retrofit had
installed. A measurement campaign of two teaching weeks per season cannot see any of
that. It can only characterise the building as it stood during the campaign.

This suggests that comfort measurement and settings governance are not separable
problems, and that a study reporting comfort outcomes without reporting whether control
settings were reconciled against design intent is reporting a snapshot of unknown
representativeness. Complaint logs may be the cheapest available signal here, since they
preceded any energy signature by roughly five months in the followed schools
(Pretorius, 2018).

A reviewer may reasonably ask why the campaign was not extended. The answer is funding
rather than methodology, which is the same answer given in the source literature and is
not a satisfying one. Nakamura & Ellis (2016) propose a rolling low-density measurement
design intended to address exactly this, and it would have been the better choice had
the instrument budget allowed.

What the present study can support is a claim about measured conditions in the sampled
rooms during the sampled weeks, together with the occupant votes matched to them. It
cannot support a claim about the retrofit's comfort performance over the building's
life, and the conclusion is written to stay inside that boundary.

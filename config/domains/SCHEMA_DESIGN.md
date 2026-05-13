# Schema Design Principles

For SMT-LIB domain schemas in `config/domains/<X>/schema.smt2`.

**One predicate, one concept.** If a predicate name reads like a sentence (`fillet_or_steak_contains_shark_fin`), it bakes in 3+ concepts and is a smell. Decompose using primitives + `is_kind` + `is_part_of`.

**Compose qualifiers separately from actions.** Prefer `transports(P, A, t) ∧ for_sale(P, A, t)` over `transports_for_sale(P, A, t)`. Qualifiers (`for_sale`, `for_compensation`, `for_commercial_purpose`, etc.) reuse across many action verbs.

**Reuse anchors.** Predicates like `is_kind`, `uses_device`, `acts_recklessly` should fire in many rules. A schema where most predicates appear in a single rule is a *union of fragments*, not a domain schema.

**Discriminate via `kind` enums on a single sort, not separate sorts.** Texas TC has one `Vehicle` sort with a `VehicleKind` enum (Ambulance, Streetcar, ...), not five sorts. The wildlife schema follows the same pattern with `Device` + `DeviceKind` covering firearms, lights, dogs, boats, vehicles, nets.

**Numeric thresholds use `Real`-valued functions.** `float_spacing_feet(D) → Real` lets the rule constrain `<= 6`. `floats_at_intervals_at_most_six_feet(D) → Bool` hardcodes the constant.

**Black-box predicates for opaque enumerations.** 19 named protected species → one `is_named_in_protected_fish_list(A) → Bool`. Don't enumerate species or devices that the LLM is expected to treat semantically.

**Time arg is `Int`, last position of time-varying predicates.** Static (time-independent) predicates omit it entirely.

**Comments: section headers + brief semantic one-liners only.** Match `config/schema.smt2` density. No statute-section, rule-ID, or experiment-internal references — schemas are free-standing domain vocabularies.

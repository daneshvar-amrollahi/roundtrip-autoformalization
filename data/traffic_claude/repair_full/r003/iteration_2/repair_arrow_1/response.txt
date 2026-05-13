Looking at the diagnostic feedback, the key issues are:

1. The consequent should represent "yielding right-of-way to another vehicle" rather than "decelerating and safe movement"
2. The "immediate hazard" condition needs better representation
3. Need to find the closest semantic representation of yielding to another vehicle in the schema

Analyzing the schema carefully:
- There's no `yield_right_of_way(Vehicle, Vehicle, Int)` predicate
- But `is_immediate_hazard(Vehicle Vehicle Intersection Int)` exists - though it requires an Intersection parameter
- The rule is about obstruction causing crossing center line, not necessarily at an intersection
- For "yield right-of-way to a vehicle," the closest approximation involves: the ego vehicle must ensure the other vehicle can proceed safely, i.e., `movement_can_be_made_safely` for the other vehicle, or ensuring `assured_clear_distance`, or stopping/waiting

Given the schema, the best approximation for "yield right-of-way to another vehicle that is an immediate hazard" is:
- The other vehicle is approaching from opposite direction (`approaching_opposite`)
- The other vehicle is on the unobstructed portion (roadway free from their perspective)
- The ego must not proceed (must stop/decelerate) until it's safe - captured by requiring `(not (crossing_center_line v r t))` unless safe, or requiring the ego to stop

The closest faithful encoding: when obstruction forces crossing center, and another vehicle is approaching opposite and is not at safe distance (immediate hazard approximation), the ego vehicle must stop (yield). Since "yield" means giving way, `is-stopping` or `stopped` combined with ensuring the other vehicle's path is unimpeded is the best approximation.

After careful review, I'll use `stopped` as the yield action (yielding = stopping to let the other vehicle pass) and `approaching_opposite` + `(not (safe-distance v v_other t))` for the immediate hazard condition.

(forall ((v Vehicle) (v_other Vehicle) (r Roadway) (t Int))
  (=> (and (is_ego v)
           (not (= v v_other))
           (on_roadway v r t)
           (on_roadway v_other r t)
           (obstruction_present v r t)
           (crossing_center_line v r t)
           (approaching_opposite v v_other t)
           (not (safe-distance v v_other t)))
      (and (is-stopping v t)
           (not (crossing_center_line v r t)))))

Wait - that's contradictory. Let me reconsider. Yielding means: don't proceed into the opposing lane until the other vehicle has passed. The encoding should say: if obstruction forces you left of center AND an oncoming vehicle is an immediate hazard, you must not cross center (i.e., you must wait/yield).

(forall ((v Vehicle) (v_other Vehicle) (r Roadway) (t Int))
  (=> (and (is_ego v)
           (not (= v v_other))
           (on_roadway v r t)
           (on_roadway v_other r t)
           (obstruction_present v r t)
           (approaching_opposite v v_other t)
           (not (safe-distance v v_other t)))
      (not (crossing_center_line v r t))))
(forall ((v Vehicle) (r Roadway) (t Int))
  (=> (and (on_roadway v r t)
           (fire_hose_on_roadway r t)
           (not (fire_dept_consent v t)))
      (not (on_roadway v r t))))

Wait, that creates a contradiction. Let me reconsider. The rule says a vehicle must not drive over a fire hose on a roadway unless it has fire department consent. "Driving over" a fire hose means the vehicle is on a roadway where a fire hose is present and is moving (not just being on the roadway). But the schema doesn't have a specific "driving_over_fire_hose" predicate. The best encoding uses the available predicates: if a vehicle is on a roadway with a fire hose and is moving, it must have consent.

(forall ((v Vehicle) (r Roadway) (t Int))
  (=> (and (on_roadway v r t)
           (fire_hose_on_roadway r t)
           (not (fire_dept_consent v t)))
      (not (fire_hose_on_roadway r t))))

That's also problematic. The correct approach: the rule prohibits driving over the hose without consent. We encode it as: if there's a fire hose on the roadway and the vehicle hasn't obtained consent, the vehicle must not be on that roadway (i.e., must not drive over it).

(forall ((v Vehicle) (r Roadway) (t Int))
  (=> (and (fire_hose_on_roadway r t)
           (not (fire_dept_consent v t)))
      (not (on_roadway v r t))))
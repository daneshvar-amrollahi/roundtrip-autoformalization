(forall ((v Vehicle) (r Roadway) (t Int))
  (=> (and (= (kind v) VK_Streetcar)
           (fire_hose_on_roadway r t)
           (on_roadway v r t)
           (not (fire_dept_consent v t)))
      (not (crossing_center_line v r t))))

Wait, let me reconsider. The rule is about a streetcar driving over an unprotected fire hose on a streetcar track. Let me re-examine the schema more carefully.

The schema has:
- `fire_hose_on_roadway` for fire hose presence
- `fire_dept_consent` for consent
- `roadway_pos` with `RP_StreetcarTrack` for streetcar track position
- `kind` with `VK_Streetcar`

The rule says: a streetcar operator may not drive over a fire hose on the track without fire department consent. The key constraint is that the streetcar is on the track where there's a fire hose, and it must not proceed without consent.

Let me use `is-moving` — actually that's not in the schema. Let me use what's available:

(forall ((v Vehicle) (r Roadway) (t Int))
  (=> (and (= (kind v) VK_Streetcar)
           (on_roadway v r t)
           (= (roadway_pos v r t) RP_StreetcarTrack)
           (fire_hose_on_roadway r t)
           (not (fire_dept_consent v t)))
      (not (on_roadway v r t))))

That's contradictory. The rule essentially says the streetcar must stop / not proceed over the hose. Let me encode it as: the streetcar should be stopped.

(forall ((v Vehicle) (r Roadway) (t Int))
  (=> (and (= (kind v) VK_Streetcar)
           (on_roadway v r t)
           (= (roadway_pos v r t) RP_StreetcarTrack)
           (fire_hose_on_roadway r t)
           (not (fire_dept_consent v t)))
      (stopped v t)))
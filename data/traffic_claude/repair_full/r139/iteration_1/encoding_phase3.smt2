(forall ((c Crossing) (t Int))
  (=> (and (is_ego ego)
           (not (sufficient_undercarriage_clearance ego c)))
      (not (approaching_crossing ego c t))))

Wait, I need to properly quantify over the ego vehicle. Let me redo this.

(forall ((v Vehicle) (c Crossing) (t Int))
  (=> (and (is_ego v)
           (not (sufficient_undercarriage_clearance v c)))
      (not (approaching_crossing v c t))))
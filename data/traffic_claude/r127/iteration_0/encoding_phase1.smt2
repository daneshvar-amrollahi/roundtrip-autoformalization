(forall ((v Vehicle) (r Roadway) (t Int))
  (=> (and (fire_hose_on_roadway r t)
           (not (fire_dept_consent v t)))
      (not (on_roadway v r t))))
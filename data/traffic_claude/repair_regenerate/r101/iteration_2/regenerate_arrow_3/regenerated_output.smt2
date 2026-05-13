(forall ((v Vehicle) (t Int))
  (=> (parked v t)
      (forall ((i Intersection))
        (> (dist_to_feature v PF_Crosswalk t) ft_20))))
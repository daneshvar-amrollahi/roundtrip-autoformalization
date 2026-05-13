(forall ((v Vehicle) (t Int))
  (=> (backing v t)
      (and (backing_safe v t)
           (not (backing_interferes_with_traffic v t)))))
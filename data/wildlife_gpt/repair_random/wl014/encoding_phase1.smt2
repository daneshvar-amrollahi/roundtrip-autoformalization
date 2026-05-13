(forall ((p Person) (a Animal) (t Int))
  (=> (and (fishes p a t)
           (exists ((d Device)) (and (uses_device p d t) (not (is_permitted_by_code d t)))))
      false))
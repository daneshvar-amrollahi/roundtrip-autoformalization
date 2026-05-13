(forall ((p Person) (a Animal) (t Int))
  (=> (and (on_road_or_right_of_way p t)
           (is_kind a AK_ExoticAnimal))
       (not (hunts p a t))))
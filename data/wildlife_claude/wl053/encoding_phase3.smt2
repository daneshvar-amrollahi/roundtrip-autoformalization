(forall ((p Person) (a Animal) (t Int))
  (=> (and (fishes p a t)
           (on_bridge_maintained_by_txdot p t))
      false))
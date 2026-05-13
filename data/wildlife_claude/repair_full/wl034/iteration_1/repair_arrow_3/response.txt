(exists ((p Person) (a Animal) (t Int))
  (and
    (lawfully_killed a)
    (or (is_kind a AK_GameBird) (is_kind a AK_GameAnimal))
    (in_cold_storage a t)
    (<= (count_in_possession p AK_GameBird t) (possession_limit AK_GameBird))
    (<= (count_in_possession p AK_GameAnimal t) (possession_limit AK_GameAnimal))
    (possesses p a t)))
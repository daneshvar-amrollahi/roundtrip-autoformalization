(forall ((p Person) (a Animal) (t Int))
  (=>
    (and
      (or (is_kind a AK_WildBird) (is_kind a AK_WildGameBird) (is_kind a AK_WildFowl)
          (is_kind a AK_WildGameAnimal) (is_kind a AK_GameAnimal))
      (lawfully_taken a)
      (not (for_sale p a t))
      (or (for_taxidermy p a t) (for_home_destination p a t))
      (or (transports p a t) (ships p a t))
    )
    (or (transports p a t) (ships p a t))
  )
)
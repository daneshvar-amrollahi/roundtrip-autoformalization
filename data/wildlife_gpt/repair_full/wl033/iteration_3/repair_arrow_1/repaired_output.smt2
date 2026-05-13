(exists ((p Person) (a Animal) (t Int))
  (and
    (or (transports p a t) (ships p a t))
    (or
      (and (for_taxidermy p a t) (not (for_sale p a t)))
      (for_home_destination p a t))
    (or (is_kind a AK_WildBird) (is_kind a AK_WildGameAnimal))
    (exists ((t_take Int))
      (and (takes p a t_take) (lawfully_taken a)))
    (not (for_sale p a t))))
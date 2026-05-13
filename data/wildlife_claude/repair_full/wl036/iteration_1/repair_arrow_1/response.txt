(forall ((p Person) (a Animal) (t Int))
  (=> (and (is_kind a AK_DangerousWildAnimal)
           (released_for_killing a t))
      (and
        (not (sells p a t))
        (not (offers_to_sell p a t))
        (not (transports p a t))
        (not (consigns_for_transport p a t)))))

(forall ((p Person) (part Animal) (a Animal) (t Int))
  (=> (and (is_part_of part a)
           (is_kind a AK_DangerousWildAnimal)
           (exists ((killer Person) (t_kill Int))
             (and (kills killer a t_kill)
                  (released_for_killing a t_kill))))
      (and
        (not (sells p part t))
        (not (offers_to_sell p part t)))))
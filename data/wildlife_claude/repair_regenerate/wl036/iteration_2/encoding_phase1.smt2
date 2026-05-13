(forall ((p Person) (a Animal) (t Int))
  (=> (is_kind a AK_DangerousWildAnimal)
      (and
        (=> (released_for_killing a t)
            (and
              (not (sells p a t))
              (not (offers_to_sell p a t))
              (not (transports p a t))
              (not (consigns_for_transport p a t))))
        (forall ((part Animal))
          (=> (and (is_part_of part a)
                   (released_for_killing a t)
                   (kills p a t))
              (and
                (not (sells p part t))
                (not (offers_to_sell p part t))))))))
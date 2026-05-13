(forall ((seller Person) (animal Animal) (t Int))
  (=> (sells seller animal t)
      (exists ((buyer Person))
        (and
          (buys buyer animal t)
          (or
            (is_zoo_entity seller)
            (and
              (or (is_zoo_entity buyer)
                  (is_educational_institution buyer)
                  (is_research_institution buyer))
              (for_scientific_purpose buyer t)
              (has_subchapter_authorization buyer t))
            (exists ((dealer Person) (t2 Int) (laterBuyer Person))
              (and
                (buys dealer animal t)
                (sells dealer animal t2)
                (buys laterBuyer animal t2)
                (<= t t2)
                (or
                  (is_zoo_entity dealer)
                  (is_zoo_entity laterBuyer)
                  (and
                    (or (is_educational_institution laterBuyer)
                        (is_research_institution laterBuyer))
                    (for_scientific_purpose laterBuyer t2)
                    (has_subchapter_authorization laterBuyer t2))))))))))
(forall ((v Vehicle) (t Int))
  (=> (and (is_ego v)
           (not (and (= (stop_action v t) SA_Stop)
                     (or (= (stop_action v t) SA_Stop)))))
      (=> (or (and (or (= (stop_action v t) SA_Stand)
                       (= (stop_action v t) SA_Park))
                   (< (dist_to_feature v PF_FireStationDriveway t) ft_20))
              (and (or (= (stop_action v t) SA_Stand)
                       (= (stop_action v t) SA_Park))
                   (< (dist_to_feature v PF_FireStationDriveway t) ft_75)))
          false)))

Let me reconsider this more carefully.

(forall ((v Vehicle) (t Int))
  (=> (and (or (= (stop_action v t) SA_Stand)
               (= (stop_action v t) SA_Park))
           (or (< (dist_to_feature v PF_FireStationDriveway t) ft_20)
               (< (dist_to_feature v PF_FireStationDriveway t) ft_75)))
      false))

Let me reconsider once more to properly handle the exception and the two distinct distance conditions.

(forall ((v Vehicle) (t Int))
  (=> (and (or (= (stop_action v t) SA_Stand)
               (= (stop_action v t) SA_Park))
           (< (dist_to_feature v PF_FireStationDriveway t) ft_75)
           (not (and (= (stop_action v t) SA_Stop)
                     (stopped v t))))
      (not (or (= (stop_action v t) SA_Stand)
               (= (stop_action v t) SA_Park)))))

Let me provide a clean final encoding:

(forall ((v Vehicle) (t Int))
  (=> (< (dist_to_feature v PF_FireStationDriveway t) ft_75)
      (not (and (or (= (stop_action v t) SA_Stand)
                    (= (stop_action v t) SA_Park))
                (not (= (stop_action v t) SA_Stop))))))
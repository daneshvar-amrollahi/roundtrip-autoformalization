(forall ((v Vehicle) (c Crossing) (t Int))
  (=> (and (approaching_crossing v c t)
           (parked v t)
           (< (dist_to_nearest_rail_sq v c t) (* ft_50 ft_50)))
      (and (stop_action v t) (= (stop_action v t) SA_Stop))))

Wait, let me reconsider this more carefully.

The rule says: may not park within 50 feet of nearest rail of a railroad crossing, except temporarily to load or unload.

Let me re-examine the schema. We have:
- `parked v t` for parking
- `dist_to_nearest_rail_sq v c t` returns squared distance to nearest rail
- `stop_action v t` returns StopAction (SA_Stop, SA_Stand, SA_Park)
- `SA_Park` for parking, `SA_Stop` for stopping (temporary load/unload is more like standing/stopping)

The exception "temporarily to load or unload" corresponds to standing (SA_Stand) or stopping (SA_Stop), not parking (SA_Park).

The rule: parking is prohibited within 50 feet, unless temporarily loading/unloading. We can encode "parking" via `stop_action = SA_Park` and the exception as the action being SA_Stand (standing for loading/unloading).

(forall ((v Vehicle) (c Crossing) (t Int))
  (=> (and (approaching_crossing v c t)
           (< (dist_to_nearest_rail_sq v c t) (* ft_50 ft_50))
           (not (= (stop_action v t) SA_Stand)))
      (not (parked v t))))
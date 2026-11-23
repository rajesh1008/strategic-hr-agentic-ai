-- Strategic HR in the Age of Agentic AI, Chapter 7: The One Person
-- Listing: Single Points of Knowledge (Under the Hood)

-- A single point: only one real person completed it end to end in 18 months.
WITH done AS (
  SELECT e.capability_id,
         coalesce(a.person_id, e.actor_id) AS person_id        -- aliases resolved
  FROM activity_events e
  LEFT JOIN actor_aliases a ON a.actor_id = e.actor_id
  WHERE e.completed_end_to_end
    AND e.occurred_at >= now() - interval '18 months'
    AND e.actor_id NOT IN (SELECT actor_id FROM service_accounts)   -- bots out
)
SELECT c.capability_id, c.name, c.next_statutory_date,
       count(DISTINCT d.person_id) AS performers
FROM capabilities c
LEFT JOIN done d ON d.capability_id = c.capability_id
GROUP BY c.capability_id, c.name, c.next_statutory_date
HAVING count(DISTINCT d.person_id) <= 1
ORDER BY c.next_statutory_date;

-- Strategic HR in the Age of Agentic AI, Chapter 10: People Who Left
-- Listing: Enrolment Check for the New Band (Under the Hood)
-- Whether the EPS monthly cap is unchanged after the ceiling rise is confirmed in Chapter 12 and signed off by counsel. The leaving dates the same match produces also price gratuity.

-- Joiners in the new EPF wage band who are missing from the PF file.
SELECT j.employee_id, j.joined_on, j.monthly_wage_inr
FROM   joiners j
WHERE  j.country = 'IN'
  AND  j.joined_on >= DATE '2026-09-17'
  AND  j.monthly_wage_inr > 15000
  AND  j.monthly_wage_inr <= 25000
  AND  NOT EXISTS (SELECT 1 FROM pf_enrolment p
                   WHERE p.employee_id = j.employee_id);
-- Stop rule for this row: the query returns nothing.

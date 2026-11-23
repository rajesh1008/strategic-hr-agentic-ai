-- Strategic HR in the Age of Agentic AI, Chapter 10: People Who Left
-- Listing: Member-Level Match, Not a 2% Total Check

-- Flag invoice lines with no current member.
-- A loose name match is never enough to merge two people.
SELECT invoice.line_id, invoice.amount
FROM   carrier_invoice invoice
WHERE  invoice.month = :this_month
  AND  NOT EXISTS (
          SELECT 1 FROM member_file member
          WHERE  member.member_id = invoice.member_id
            AND  member.eligible  = TRUE
       );
-- A person decides whether anyone's coverage changes.

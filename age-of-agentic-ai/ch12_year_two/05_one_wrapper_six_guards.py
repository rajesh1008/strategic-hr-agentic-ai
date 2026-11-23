# Strategic HR in the Age of Agentic AI, Chapter 12: Year Two
# Listing: One Wrapper, Six Guards (Under the Hood)
# check_number_provenance is the slot guard from Chapter 11.

class Guarded:
    def __init__(self, step, banned: set[str], spend_cap: float, switch):
        self.step, self.banned = step, banned
        self.cap, self.switch, self.spent = spend_cap, switch, 0.0

    def __call__(self, request):
        if self.switch.is_off(self.step.name):
            raise RuntimeError("kill switch is off for this step")
        validate_schema(request, self.step.input_schema)
        if request.action in self.banned:      # write_payroll, release_bank_file
            raise PermissionError(f"banned action: {request.action}")
        cost = self.step.estimate_cost(request)
        if self.spent + cost > self.cap:
            raise RuntimeError("spend limit reached; routed to the agent owner")
        result = self.step.run(request)
        check_number_provenance(result, request.code_outputs)
        self.spent += cost
        evidence.append(self.step.name, request, result)
        return result

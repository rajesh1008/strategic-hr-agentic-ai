"""Offline tests for Chapter 14: every lifecycle path."""
from chapters.ch14_controlled_actions.actions import (
    Lifecycle, idem_key, norm)
from chapters.ch14_controlled_actions.agent import says_done
from chapters.ch14_controlled_actions.fakes import (Clock,
                                                    HartwellOne)

LENA, DIEGO = "HW-012771", "HW-019044"
NEW = "2240 Larimer Street, Apt 5, Denver, CO 80205"
BANK = "Front Range CU ****7731"
PAY = "HYD-PAY-0117"


def lc(**kw):
    c = Clock()
    return c, Lifecycle(HartwellOne(**kw), c,
                        managers={LENA: "HW-012927"})


def test_complete_path_by_rule():
    _, l = lc()
    a = l.propose(LENA, "home_address", NEW, LENA)
    assert a.state == "done" and len(l.hris.audit) == 1
    assert [s[1] for s in a.steps] == [
        "proposal", "approval", "dispatch", "receipt",
        "readback"]


def test_bank_change_needs_a_person_not_requester():
    c, l = lc()
    a = l.propose(LENA, "bank_account", BANK, LENA)
    assert a.state == "awaiting_approval"
    for who in (LENA, "HW-012927", "svc-askhartwell-agent"):
        l.approve(a.id, who, "payroll_ops", callback_done=True)
        assert a.state == "awaiting_approval"
    l.approve(a.id, PAY, "payroll_ops")          # no callback
    assert a.state == "awaiting_approval"
    l.approve(a.id, PAY, "hr_adviser", callback_done=True)
    assert a.state == "awaiting_approval"
    l.approve(a.id, PAY, "payroll_ops", callback_done=True)
    l.dispatch(a.id)
    assert a.state == "done" and len(l.hris.notices) == 1


def test_refuse_paths():
    _, l = lc()
    assert l.propose(LENA, "base_pay", "x", LENA).state \
        == "denied"
    assert l.propose(DIEGO, "bank_account", BANK,
                     LENA).state == "denied"
    assert l.propose(LENA, "home_address", "no zip",
                     LENA).state == "denied"
    assert not l.hris.audit


def test_lost_reply_settled_without_second_write():
    _, l = lc()
    l.hris.inject("lose_reply")
    a = l.propose(LENA, "home_address", NEW, LENA)
    assert a.state == "done" and a.dispatches == 1
    assert len(l.hris.audit) == 1


def test_dropped_call_redispatched_once():
    _, l = lc()
    l.hris.inject("drop")
    a = l.propose(LENA, "home_address", NEW, LENA)
    assert a.state == "done" and a.dispatches == 2
    _, l = lc()
    l.hris.inject("drop", "drop")
    a = l.propose(LENA, "home_address", NEW, LENA)
    assert a.state == "needs_person" and not l.hris.audit


def test_duplicate_request_same_action():
    _, l = lc()
    a = l.propose(LENA, "home_address", NEW, LENA)
    b = l.propose(LENA, "home_address",
                  NEW.replace("Street", "St").upper(), LENA)
    assert a is b and len(l.hris.audit) == 1


def test_revoke_and_expiry():
    c, l = lc()
    a = l.propose(LENA, "bank_account", BANK, LENA)
    l.approve(a.id, PAY, "payroll_ops", callback_done=True)
    l.revoke(a.id, PAY, "not her request")
    l.dispatch(a.id)
    assert a.state == "revoked" and not l.hris.audit
    c, l = lc()
    a = l.propose(LENA, "bank_account", BANK, LENA)
    l.approve(a.id, PAY, "payroll_ops", callback_done=True)
    c.advance(241)
    l.dispatch(a.id)
    assert a.state == "expired" and not l.hris.audit


def test_revoke_after_dispatch_refused():
    _, l = lc()
    a = l.propose(LENA, "home_address", NEW, LENA)
    l.revoke(a.id, PAY, "late")
    assert a.state == "done"


def test_mismatch_not_retried():
    _, l = lc()
    l.hris.inject("overwrite")
    a = l.propose(LENA, "home_address", NEW, LENA)
    assert a.state == "mismatch" and a.dispatches == 1
    assert l.propose(LENA, "home_address", NEW, LENA) is a


def test_normalized_readback():
    _, l = lc()
    l.hris.inject("normalize")
    a = l.propose(LENA, "home_address", NEW, LENA)
    assert a.state == "done"
    assert l.hris.read(LENA)["home_address"] != NEW
    assert norm("2240 LARIMER ST APT 5") == norm(
        "2240 Larimer Street, Apt 5")


def test_reversal_is_new_action():
    _, l = lc()
    old = l.hris.read(LENA)["home_address"]
    a = l.propose(LENA, "home_address", NEW, LENA)
    r = l.reverse(a.id, "HR-DEN-ADV-031", "wrong unit")
    assert r.id != a.id and r.reverses == a.id
    assert r.state == "done"
    assert l.hris.read(LENA)["home_address"] == old
    b = l.propose(LENA, "bank_account", BANK, LENA)
    l.approve(b.id, PAY, "payroll_ops", callback_done=True)
    l.dispatch(b.id)
    rb = l.reverse(b.id, "HR-DEN-ADV-031", "fraud")
    assert rb.state == "awaiting_approval"


def test_keys_stable_under_formatting():
    assert idem_key(LENA, "home_address", NEW) == idem_key(
        LENA, "home_address", "2240 larimer st apt 5 denver"
        " co 80205")


def test_says_done_phrase_check():
    assert says_done("Your address has been updated.")
    assert not says_done("It has not been changed yet.")
    assert not says_done("Your record hasn't changed.")
    assert not says_done("I noted you need it done by Friday.")
    assert says_done("Done. Your pay is now set to X.")
    assert not says_done("Once payroll approves, it will be"
                         " updated.")

"""Unit tests for transcript parsing (agent/transcript.py)."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from agent import transcript


def test_plain_lines_all_become_claims():
    text = "We give 10% automatically.\n\nCustomer data stays in the EU.\n"
    assert transcript.parse_transcript(text) == [
        "We give 10% automatically.", "Customer data stays in the EU."]


def test_timestamps_are_stripped():
    text = "14:32 we can do the 10 percent discount automatically\n[00:14:07] support is 24/7\n"
    claims = transcript.parse_transcript(text)
    assert claims == ["we can do the 10 percent discount automatically",
                      "support is 24/7"]


def test_only_rep_side_lines_when_labels_present():
    text = ("Rep: we'll give you the 10 percent automatic discount\n"
            "Customer: that sounds great\n"
            "Rep - and you get 24/7 support on the Standard Plan\n")
    claims = transcript.parse_transcript(text)
    assert len(claims) == 2
    assert all("Customer" not in c for c in claims)


def test_customer_lines_skipped_with_timestamps():
    text = ("14:01 Rep: uptime will be 99.9 percent on Standard\n"
            "14:02 Customer: wonderful\n"
            "14:03 Sales rep: we can refund early termination fees\n")
    claims = transcript.parse_transcript(text)
    assert claims == ["uptime will be 99.9 percent on Standard",
                      "we can refund early termination fees"]


def test_fallback_when_no_rep_side_matched():
    text = "Host: welcome everyone\nHost: let's begin\n"
    claims = transcript.parse_transcript(text)
    assert claims == ["welcome everyone", "let's begin"]


def test_empty_transcript():
    assert transcript.parse_transcript("") == []
    assert transcript.parse_transcript("\n  \n") == []

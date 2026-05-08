from app.core.config import get_settings
from app.core.guardrails import GuardrailReviewer
from app.core.models import DetectionFinding, Evidence


def test_guardrails_redact_encoded_commands() -> None:
    evidence = [
        Evidence(
            evidenceId="ev1",
            timestamp=None,
            host="host1",
            user="user1",
            process="powershell.exe",
            parentProcess="winword.exe",
            commandLine="powershell.exe -EncodedCommand SQBFAFgAKABOAGUAdwAtAE8AYgBqAGUAYwB0AA==",
            targetProcess=None,
            destinationIp=None,
            destinationDomain=None,
            filePath=None,
            hash=None,
            eventId="1",
            provider="Sysmon",
            rawReference="event-1",
            summary="demo",
        )
    ]
    finding = DetectionFinding(
        findingId="f1",
        ruleId="DL-PS-001",
        title="Encoded PowerShell command",
        reason="demo",
        evidenceIds=["ev1"],
        evidence=evidence,
        mitreTechnique="T1027",
        tactic="Defense Evasion",
        scoreContribution=20,
        confidenceContribution=0.18,
    )
    review = GuardrailReviewer(get_settings()).review([finding], "template")

    assert review.payload_redactions == 1
    assert review.structured_findings[0]["evidence"][0]["commandLine"].endswith("[redacted-encoded-command]")

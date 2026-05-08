from app.core.models import DetectionFinding, Evidence, ScoreCard, TacticHit
from app.core.scoring import ScoreEngine


def test_scoring_applies_tactic_diversity_bonus() -> None:
    evidence = [
        Evidence(
            evidenceId="ev1",
            timestamp=None,
            host="host1",
            user="user1",
            process="powershell.exe",
            parentProcess="winword.exe",
            commandLine="powershell.exe -enc [redacted]",
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
    findings = [
        DetectionFinding(
            findingId="f1",
            ruleId="DL-WIN-001",
            title="Office spawned PowerShell",
            reason="demo",
            evidenceIds=["ev1"],
            evidence=evidence,
            mitreTechnique="T1059.001",
            tactic="Execution",
            scoreContribution=20,
            confidenceContribution=0.16,
        ),
        DetectionFinding(
            findingId="f2",
            ruleId="DL-PS-001",
            title="Encoded PowerShell command",
            reason="demo",
            evidenceIds=["ev1"],
            evidence=evidence,
            mitreTechnique="T1027",
            tactic="Defense Evasion",
            scoreContribution=20,
            confidenceContribution=0.18,
        ),
        DetectionFinding(
            findingId="f3",
            ruleId="DL-NET-001",
            title="Suspicious public outbound connection",
            reason="demo",
            evidenceIds=["ev1"],
            evidence=evidence,
            mitreTechnique="T1071",
            tactic="Command and Control",
            scoreContribution=20,
            confidenceContribution=0.16,
        ),
    ]
    tactics = [
        TacticHit(
            techniqueId="T1059.001",
            techniqueName="PowerShell",
            tactic="Execution",
            description="demo",
            confidence=0.16,
            relatedRules=["DL-WIN-001"],
        ),
        TacticHit(
            techniqueId="T1027",
            techniqueName="Obfuscated Files or Information",
            tactic="Defense Evasion",
            description="demo",
            confidence=0.18,
            relatedRules=["DL-PS-001"],
        ),
        TacticHit(
            techniqueId="T1071",
            techniqueName="Application Layer Protocol",
            tactic="Command and Control",
            description="demo",
            confidence=0.16,
            relatedRules=["DL-NET-001"],
        ),
    ]

    scorecard = ScoreEngine().evaluate(evidence, findings, tactics)

    assert scorecard.risk_score >= 70
    assert any(component.label == "TACTIC-DIVERSITY" for component in scorecard.score_trace)


# 📘 Runbook: Risk Kill Switch Triggered

## Alert

kill_switch.is_triggered() == true

## Severity

Critical

## Meaning

System has entered protective shutdown mode.

## Diagnosis

kill_switch.is_triggered()

tail -n 200 exchange/logs/risk_rejections.log

## Recovery

kill_switch.reset()

ONLY after stability confirmed.

## Verification

feed stable
no risk spikes

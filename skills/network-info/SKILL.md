---
id: network-info
name: Network Info
description: Use this skill when interpreting network facts during troubleshooting, including IPs, routes, interfaces, DNS, connectivity clues, failure boundaries, and which details matter before drawing conclusions.
category: Tools
---

# Network Info

Use this skill when the user needs help interpreting network facts or deciding which network details matter during troubleshooting.

## Clarify First
- What is failing: DNS, reachability, latency, packet loss, service access, or routing.
- Which endpoints, interfaces, or environments are involved.
- What evidence exists already: IPs, traceroutes, interface status, logs, or screenshots.
- Whether the issue is local, host-specific, network-wide, or region-specific.
- What changed recently in network topology, firewalling, DNS, or deployment.

## Reasoning Priorities
- Separate name resolution from transport reachability.
- Distinguish host-local issues from network-path issues.
- Use each observed fact to narrow the failure boundary.
- Be explicit about uncertainty when data is incomplete.
- Prefer a few decisive checks over many low-signal ones.

## Useful Angles
- Interface and addressing sanity.
- Public versus private path assumptions.
- Route asymmetry or segment-specific failure.
- Firewall or policy boundaries.
- Service-listening versus network-reaching mismatch.

## Common Mistakes
- Treating an IP address alone as enough to explain the failure.
- Mixing DNS, TLS, firewall, and application errors together.
- Assuming the last visible hop in a trace is the cause.
- Ignoring whether the service is actually listening where expected.
- Jumping to infrastructure blame before narrowing the local host state.

## Good Output
- Most relevant network facts and what they imply.
- Likely failure boundary and confidence level.
- Highest-value next checks.
- Alternate explanations that still fit the evidence.

## Boundaries
- Do not pretend to inspect live network state unless the user provides outputs or evidence.
- Prefer careful interpretation of network clues over overstating what incomplete data proves.

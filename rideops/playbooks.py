"""Per-category playbooks agreed between L1 and engineering.

`required`  : facts an escalation must carry (kills "Insufficient info" / "Not reproducible").
`l1_checks` : config / how-to checks L1 runs first (kills "Config issue" / "Not a bug").
In production these live in a config table owned by the support lead, not in code.
"""

PLAYBOOKS: dict[str, dict[str, list[str]]] = {
    "Roster / booking not syncing": {
        "required": ["Trip date + shift time", "Affected employee IDs (sample of 3)",
                     "Roster upload file / booking ID", "Screenshot of roster vs booking"],
        "l1_checks": ["Booking cutoff time in client settings matches the new policy",
                      "Roster regeneration ran after the latest change (Admin > Roster > Regenerate)",
                      "Employees are mapped to the correct shift + office",
                      "Excel upload: check template version and rejected-rows report"],
    },
    "Live tracking / GPS incorrect": {
        "required": ["Trip ID", "Vehicle number", "Exact time window of the issue",
                     "Driver app version", "Screenshot / screen recording"],
        "l1_checks": ["Driver app is on the latest version and location permission is 'Always'",
                      "Tracking link has not expired (links expire at trip end)",
                      "Security-team users have the 'Live tracking' role",
                      "Check device GPS signal history in the trip log"],
    },
    "Report export failing": {
        "required": ["Report name", "Date range used", "Requested by (user ID)", "Time of attempt"],
        "l1_checks": ["Date range is within the 15-day export limit (split larger ranges)",
                      "Scheduled report recipient list + spam folder",
                      "User has the 'Reports' permission for that module"],
    },
    "OTP / boarding issue": {
        "required": ["Trip ID", "Employee ID", "Driver app version", "Time of OTP attempt"],
        "l1_checks": ["Employee phone number is current in the profile",
                      "OTP was entered within its validity window",
                      "Trip was started by the driver before OTP entry"],
    },
    "Billing / invoice discrepancy": {
        "required": ["Invoice number", "Disputed trip IDs", "Client's own trip count / calculation"],
        "l1_checks": ["Correct rate card version is mapped to the vendor and period",
                      "Cancelled-trip dead-km policy in the contract",
                      "Toll entries: check for manual + auto duplicates"],
    },
    "Cab delay / no-show complaint": {
        "required": ["Trip ID", "Vehicle number", "Scheduled vs actual pickup time"],
        "l1_checks": ["Vendor / driver acknowledgement in trip log (usually an ops issue, not a bug)",
                      "Was the trip assigned a vehicle before cutoff?"],
    },
    "Employee address / geocode change": {
        "required": ["Employee IDs", "Old and new address", "Expected pin location"],
        "l1_checks": ["Address change approved in admin console",
                      "Re-geocode triggered after approval (Admin > Employees > Re-geocode)"],
    },
    "Login / access issue": {
        "required": ["User email / ID", "Role expected", "Error message screenshot"],
        "l1_checks": ["User exists and is active", "Role / module permission assigned",
                      "Password reset / SSO mapping"],
    },
    "How-to / feature request": {
        "required": ["Business need in one line"],
        "l1_checks": ["Answer from help-centre article; log feature asks on the product board, not engineering"],
    },
    "Driver / vehicle compliance docs": {
        "required": ["Vehicle / driver ID", "Document type and expiry date"],
        "l1_checks": ["Compliance auto-block setting is enabled for the client",
                      "Vendor has uploaded the renewed document"],
    },
}


def playbook(category: str) -> dict[str, list[str]]:
    """Return the playbook for a category (empty lists if unknown)."""
    return PLAYBOOKS.get(category, {"required": [], "l1_checks": []})

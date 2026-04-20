# SentinelMesh — Extra Features Build Guide
### For use with Antigravity AI Coding Assistant

---

## CRITICAL: Follow the Build Order

**Do not skip ahead. Do not build out of order.**

Every feature in this document depends on data or infrastructure
created by the feature before it. Building Feature 3 before Feature 1
means Feature 3 will have no profile data to work with.
Building Feature 5 before Feature 2 means the mutation engine
won't know the attacker's enriched context.

The correct build order is:

1. Attacker Behavioral Fingerprinting
2. IP Threat Intelligence Enrichment
3. Canary Token Tracking
4. Honeypot Mutation Engine
5. PDF Forensic Report

Build each feature completely, test it end to end,
then move to the next one.

---

## Existing System — What Is Already Built

Before building anything new, here is a precise description of what
already exists so Antigravity knows exactly what to build on top of.

**Layer 1 — Honeypot Asset**
A single S3 bucket named `payment-gateway-prod-backups-2026` exists
in the `eu-north-1` AWS region. It acts as bait for attackers.

**Layer 2 — Event Pipeline**
When any object is accessed, created, or deleted in that bucket,
an S3 Event Notification fires immediately (not CloudWatch — this
is important because CloudWatch has 5–15 minute delays).
The notification goes to an SNS Topic named `Sentinel-Honeypot-Alerts`.
The SNS topic triggers a Lambda function named `Sentinel-Event-Processor`.
The Lambda function extracts the attacker's IP, the resource accessed,
and the timestamp, packages it as JSON, and HTTP POSTs it to the
FastAPI server running on an EC2 instance in `eu-north-1`.
Total pipeline latency is under 3 seconds end to end.

**Layer 3 — FastAPI Backend**
A Python FastAPI server runs on the EC2 instance using Uvicorn.
It has a `RiskEngine` inside `intelligence.py` that scores each
incoming event individually based on IP access intervals and keyword
detection (e.g., the word "gateway" in the resource name).
It has four endpoints: `/events` (receive and store events),
`/heal` (trigger self-healing), `/audit` (retrieve audit log),
`/status` (system health check).
The server uses Boto3 to interact with AWS.
It calls the GroqCloud LLaMA-3-8b API to generate plain-English
audit log entries after each threat event.

**Layer 4 — Self-Healing**
When the risk score from the RiskEngine reaches 100 during the demo,
the FastAPI server uses Boto3 to programmatically restrict the
EC2 instance's security group. This is the autonomous response action.

**Layer 5 — React Dashboard**
A React frontend built with Vite polls the FastAPI server every
3 seconds. It has four panels:
- Panel 1: Live event feed (reverse chronological)
- Panel 2: Risk gauge (Recharts RadialBar)
- Panel 3: World map (react-simple-maps, holographic dot-matrix style)
- Panel 4: Audit log (displays Groq LLM-generated entries)
The theme is fully dark: `#0A0C0F` to `#0B132B` backgrounds,
cyan and amber accent colors, no light mode.

**What is missing from the existing system:**
The existing RiskEngine scores each event in complete isolation.
It has no memory of what the same IP did in previous events.
It does not recognize behavioral patterns over time.
It does not classify attacker type (bot vs human vs aggressive scanner).
It does not infer attacker intent (credential hunting vs data theft).
It does not predict escalation probability.
There is no IP enrichment (no Tor detection, no ASN lookup, no geo).
There is no alerting outside the dashboard.
There is no tracking beyond the cloud boundary.
There is no honeypot adaptation.
There is no downloadable report.

All five features below address these gaps.

---

## Feature 1 — Attacker Behavioral Fingerprinting

### Build this first. Everything else depends on it.

### What this feature does

Currently the system treats every S3 access event as a standalone incident.
An attacker hits the bucket, the event is scored once, and the system moves on
with no memory of that attacker.

This feature introduces a persistent in-memory profiler that builds a
cumulative behavioral profile for every unique attacker IP address.
Every time a new event arrives from an IP, it is added to that IP's profile.
The profiler then runs three classifiers on the updated profile and returns
a structured result containing: behavioral pattern type, inferred intent,
escalation probability from 0 to 100, and a threat level label.

### Behavioral pattern classification

The profiler must classify how the attacker is operating based purely on
the timing intervals between their consecutive accesses.

To do this, it calculates the time gap between each access and the previous
one for the same IP. It stores all these intervals in a list.
It then computes two statistics: the average interval, and the variance
(difference between the maximum and minimum interval).

Based on these two numbers, it assigns one of four behavior types:

AUTOMATED_SCANNER: Average interval is under 2 seconds AND variance
is under 0.5 seconds. This means the probes are extremely fast and
extremely regular — the signature of a bot running a script with fixed
timing. No human can probe that consistently.

MANUAL_ATTACKER: Average interval is over 10 seconds AND variance is
over 5 seconds. This means the probes are slow and irregular — the
signature of a human manually navigating and deciding what to probe next.
Manual attackers are typically more sophisticated and dangerous.

AGGRESSIVE_ENUMERATION: The attacker has made more than 5 probes AND
the average interval is under 3 seconds. This means they are hitting
everything very fast with high volume — like a brute-force scanner
trying every possible resource name.

RECONNAISSANCE: The attacker has made 3 or fewer probes AND the average
interval is over 5 seconds. This means they are being careful and
deliberate, probing only specific things slowly — they know what they
want and do not want to trigger alerts.

If no pattern matches, classify as UNKNOWN_PATTERN.
If this is the first event from this IP with no intervals yet,
classify as INITIAL_PROBE.

### Intent classification

The profiler must also classify why the attacker is here based on the
names of the resources they have accessed.

It concatenates all resource names from the profile into one string,
converts it to lowercase, and checks it against three keyword lists.

Credential keywords: key, secret, password, token, credential,
auth, api, iam, cert, private, pem.

Exfiltration keywords: backup, dump, export, archive, snapshot,
restore, prod, database, db, sql.

Financial keywords: payment, billing, invoice, stripe,
gateway, wallet, transaction, bank.

It counts how many keywords from each list appear in the combined
resource string. The category with the most hits wins.

There is also a special case: if the attacker has accessed the same
single resource more than twice in a row (all entries in
resources_probed are identical), the intent is TARGETED_ATTACK —
they are fixated on one specific thing.

If no keywords from any category match, the intent is BROAD_RECONNAISSANCE.

Intent labels: CREDENTIAL_HARVESTING, DATA_EXFILTRATION,
FINANCIAL_TARGETING, TARGETED_ATTACK, BROAD_RECONNAISSANCE.

### Escalation probability calculation

This is a 0-to-100 score representing how likely this attacker is
to attempt to reach a real resource (not the honeypot) very soon.

It is calculated by adding weighted points across multiple factors:

Access count: Add 7 points per probe, capped at 35 total.
More probes means higher intent and persistence.

Dangerous keyword hits: For each of these words found in the
combined resource names — key, secret, password, payment, prod,
gateway, token, credential — add 10 points, capped at 30 total.
These words indicate high-value targeting.

Behavior type bonus: AGGRESSIVE_ENUMERATION adds 20 points
(high volume means high risk). MANUAL_ATTACKER adds 15 points
(humans are more sophisticated). AUTOMATED_SCANNER adds 10 points
(bots are persistent even if less targeted).

Intent type bonus: TARGETED_ATTACK adds 20 points (they know exactly
what they want). FINANCIAL_TARGETING adds 15 points (financial data
is high value).

Cap the final score at 100.

### Threat level assignment

Map the escalation probability to a human-readable label:
75 or above: CRITICAL
50 to 74: HIGH
25 to 49: MEDIUM
0 to 24: LOW

### Profile data structure

Each profile must store: ip address, first seen timestamp, last seen
timestamp, access count, list of all resources probed in order,
list of all timing intervals between consecutive probes,
behavior type string, intent string, escalation probability integer,
threat level string, session duration in seconds.

### Where to put this

Create a new file: `intelligence/attacker_profiler.py`
Create a class called `AttackerProfiler` with an `__init__` that
initializes an empty dictionary to store profiles keyed by IP address.

The main method is called `update(ip, resource, timestamp)`.
It takes the IP address, the resource name that was accessed,
and an optional timestamp (default to current time if not provided).
It creates or updates the profile for that IP, runs all three
classifiers, updates the profile fields, and returns the complete
updated profile dictionary.

Add a `get_profile(ip)` method that returns the profile for a given IP
or None if not found.

Add a `get_all_profiles()` method that returns all profiles sorted
by escalation probability descending.

Add a `get_plain_english_summary(ip)` method that returns a single
sentence describing the attacker: how many resources they probed,
over how many seconds, their behavior type, intent, escalation
probability, and threat level. This sentence is passed as context
to Groq when generating the audit log entry, so Groq produces a
much more specific and informative explanation.

### How to wire into the existing FastAPI server

In `main_fastapi.py`, import the AttackerProfiler class and initialize
one instance at module level (outside any route function) so the same
profiler persists across all incoming requests.

Inside the existing `/events` POST endpoint, after extracting the IP
and resource from the incoming JSON, call `profiler.update(ip, resource)`.
Attach all four profile fields (attack_type, intent,
escalation_probability, threat_level) to the event dictionary before
the event is passed to the existing RiskEngine and stored.

Also pass the plain English summary from the profiler as context
when calling Groq for the audit entry. This way Groq generates entries
like "Manual attacker with credential harvesting intent reached
escalation probability 84%" instead of generic text.

Add two new GET endpoints:
`/profiles` — returns all profiles from `profiler.get_all_profiles()`
`/profiles/{ip}` — returns a single profile for the given IP

### What to add to the React dashboard

Add a fifth panel called Attacker Intelligence.

This panel polls the `/profiles` endpoint every 3 seconds.
For each unique IP in the response, it displays an attacker card
containing:

- The IP address
- A behavior type badge with appropriate color:
  AUTOMATED_SCANNER in blue, MANUAL_ATTACKER in red,
  AGGRESSIVE_ENUMERATION in orange, RECONNAISSANCE in yellow
- An intent badge: CREDENTIAL_HARVESTING in red,
  DATA_EXFILTRATION in amber, FINANCIAL_TARGETING in red,
  TARGETED_ATTACK in bright red, BROAD_RECONNAISSANCE in gray
- An escalation probability bar that fills horizontally from 0 to 100,
  color shifting from green (low) through amber (medium) to red (high)
- A threat level chip: CRITICAL in red, HIGH in orange,
  MEDIUM in yellow, LOW in green
- The ordered list of resources probed
- How many seconds they have been active

Sort the cards by escalation probability descending so the most
dangerous attacker is always at the top.

### Libraries required

No new Python libraries needed. Uses only Python standard library:
time (for timestamps) and the existing difflib already in the codebase.

---

## Feature 2 — IP Threat Intelligence Enrichment

### Build this second.

### What this feature does

When an event arrives, the only information about the attacker is their
IP address. This feature enriches that IP with four pieces of additional
intelligence before the event is stored and profiled:

Whether the IP is a known Tor exit node. Attackers use Tor to hide
their real location and identity. If the attacker is on Tor, every
IP-based tracking is unreliable and the threat level automatically
escalates.

What organization or ISP owns this IP address. This is determined
via ASN (Autonomous System Number) lookup. An IP owned by
Hetzner, DigitalOcean, or Vultr is almost certainly automated
scanning infrastructure. An IP owned by a residential ISP suggests
a human operator.

What country and city the IP originates from. Used for the world
map panel on the dashboard.

Whether this is a known datacenter IP. A curated list of datacenter
ASN numbers identifies IPs being used as scanning/attack infrastructure.

### How Tor detection works

Before the hackathon, download the official Tor Project exit node list
from `https://check.torproject.org/tfile/exit-addresses` and save it
as `data/tor_exit_nodes.txt` in the project directory.

This file is plain text. Each relevant line looks like:
`ExitAddress 185.220.101.34 2024-01-15 12:00:00`

At module startup, parse this file once and load all IP addresses
into a Python set. Checking whether an IP is in the set is O(1).

The set is loaded once when the module imports. It does not reload
on each request.

### How ASN lookup works

Use the `ipwhois` Python library. It performs an RDAP lookup for any
IP address and returns the ASN number and organization description.

For example, querying 95.179.128.0 returns ASN AS20473 and
organization "Choopa, LLC" (Vultr's parent company).

Known datacenter ASN numbers to flag as scanner infrastructure:
AS14061 (DigitalOcean), AS16276 (OVH), AS24940 (Hetzner),
AS63023 (Vultr), AS8100 (QuadraNet).

If the resolved ASN is in this list, mark the IP as a datacenter IP.

### How geolocation works

Use the free `ip-api.com` REST API. No API key required.
Send a GET request to `http://ip-api.com/json/{ip}`.
The response JSON contains `country` and `city` fields.

Set a 2-second timeout on this request. The event pipeline must
never block for longer than 2 seconds waiting for geolocation.
If the request fails for any reason, continue with UNKNOWN values.
Enrichment failures must never crash the event pipeline.

### Skip private IPs

If the IP starts with 10., 192.168., 127., or 172., it is a private
network address. Return a result immediately with risk_label set to
PRIVATE_NETWORK and skip all lookups.

### Risk label assignment

After all lookups complete, assign a human-readable risk label:
If is_tor is true: TOR_EXIT_NODE
Else if is_datacenter is true: DATACENTER_SCANNER
Else: RESIDENTIAL_IP

### Output structure

The enrichment result for any IP contains:
is_tor (boolean), asn (string like "AS24940"), org (organization name),
country (string), city (string), is_datacenter (boolean),
risk_label (string from the three options above).

### Where to put this

Create a new file: `intelligence/ip_enricher.py`

Create a function called `enrich_ip(ip)` that takes an IP string
and returns the enrichment dictionary described above.

Load the Tor exit node set at module level when the file first imports,
not inside the function. This ensures it loads once at server startup.

### How to wire into the existing FastAPI server

In `main_fastapi.py`, import `enrich_ip` from `intelligence/ip_enricher.py`.

Inside the `/events` POST endpoint, call `enrich_ip(ip)` immediately
after extracting the IP from the incoming JSON.
Attach the result to the event dictionary as `event["ip_enrichment"]`
before passing the event to anything else.

The profiler's intent classification will now have richer context
because the event carries enrichment data.
The Groq audit entry should reference whether the attacker was on Tor
or using datacenter infrastructure.

### What to update on the React dashboard

Update the existing world map panel: when a user hovers over an
attacker dot on the map, show a tooltip containing the organization
name, ASN, and risk label.

Update the attacker intelligence panel from Feature 1: add a line
to each attacker card showing the org name and risk label.

If is_tor is true, show a prominent red TOR EXIT NODE badge on
the attacker card. This is a high-visibility signal that should
be clearly visible without the user needing to expand anything.

If is_datacenter is true, show a yellow DATACENTER SCANNER badge.

### Libraries required

Install: `ipwhois` and `requests`

---

## Feature 3 — Canary Token Embedded in Fake Files

### Build this third. Most technically sophisticated feature.

### What this feature does

The fake config file in the S3 bucket currently contains fake credentials
that do nothing. An attacker downloads the file, tries the credentials,
finds they don't work, and moves on. The system only knows they accessed
the bucket — it has no visibility into what they did with the file after
downloading it.

A canary token is a unique URL embedded inside the fake file.
If an attacker downloads the file and their automated tool, browser,
or script ever loads that URL — from any machine, anywhere in the world,
at any point in the future — your server receives and logs that request.

This means you can potentially track the attacker to their real machine
(which may have a completely different IP than the bot that hit S3)
and know the exact moment they opened or processed the stolen file.

This extends tracking beyond the AWS cloud boundary, which no other
feature in this system does.

### What to put inside the fake config file

Update the fake config file stored in the S3 bucket to look like
a realistic application configuration file. It should contain
several sections with convincing fake values for database credentials,
API keys, and service endpoints.

Within the file, embed at least two references to a URL that points
to your EC2 server's public IP or domain on the specific path `/canary/track`.

Include a unique UUID as a query parameter called `token`.
Format: `http://YOUR-EC2-IP/canary/track?token=YOUR-UUID-HERE`

Generate this UUID once before the hackathon and hardcode it in both
the config file (uploaded to S3) and in the FastAPI server's token registry.

The URL should appear in the file as the value of fields where automated
tools would be likely to try to connect to it — for example a
health_check_url field, a metrics_endpoint field, or a webhook_url field.
Automated credential harvesters often attempt to connect to every URL
they find in configuration files.

### The canary tracking endpoint

Add a new GET endpoint to `main_fastapi.py` at the path `/canary/track`.

This endpoint accepts a `token` query parameter and an optional `type`
query parameter (defaults to "access").

It extracts from the incoming request:
The real IP address of the requester from `request.client.host`.
The X-Forwarded-For header (in case of proxies).
The User-Agent header (reveals what tool or browser opened the file).

It looks up the token in a local dictionary defined in `main_fastapi.py`
at module level called `CANARY_TOKENS`. This dictionary maps each
token UUID to metadata: which file it came from, a human-readable
description, and a severity level (always CRITICAL).

It creates a canary event dictionary containing: type set to
"CANARY_TOKEN_HIT", the token value, the real IP, the X-Forwarded-For
header, the user agent, the file that was exfiltrated (from the token
registry), severity CRITICAL, current timestamp, and a note string:
"Attacker opened exfiltrated file — tracking beyond cloud boundary."

It appends this canary event to the existing events store so the
dashboard live feed displays it.

It calls `send_alert` from Feature 3 with risk score 100 and action
string "CANARY TOKEN HIT — File opened on attacker machine."

It returns a completely blank 200 response with an empty body.
Never return an error code. Never reveal to the caller that they
triggered a tracking endpoint. The response must be indistinguishable
from a normal successful health check response.

### How canary events appear on the dashboard

Canary token hit events must appear dramatically different from
normal S3 access events in the live feed panel.

They should use a CRITICAL severity banner in bright red.
The event card must display:
"CANARY TOKEN HIT — FILE TRACKED BEYOND CLOUD BOUNDARY"
followed by the real IP that opened the file, the user agent string,
and the name of the file that was exfiltrated.

If the canary real IP is different from the original S3 attacker IP,
show both IPs side by side with a label such as:
"Attack originated from X — file later opened from Y."
This is the most forensically significant outcome possible
and should be displayed as prominently as possible.

### No new Python files needed

This entire feature lives inside `main_fastapi.py` as a new endpoint
and a new dictionary. No new Python module needs to be created.

### Libraries required

No new libraries. Uses FastAPI's Request object (already available)
and the standard uuid module from Python's standard library.

---

## Feature 4 — Honeypot Mutation Engine

### Build this fourth. Most intellectually impressive feature.

### What this feature does

The current honeypot is static. It has one name and never changes.
An attacker can probe it, find nothing useful, and move on.
There is no adaptation. The trap does not learn.

The Mutation Engine makes the honeypot adaptive.

After every attack where the self-healing threshold is crossed,
the engine analyzes the attacker's profile — specifically what
resources they probed and what their inferred intent was.

It then automatically creates a brand new S3 bucket with a name
precisely designed to attract that type of attacker based on
what they were hunting for.

If the attacker was probing payment-related resources, a new bucket
appears with a name containing payment-related keywords.
If they were probing credential-named resources, a new bucket
appears with a name containing credential-related keywords.

The new bucket is wired to the same SNS notification pipeline as
the original honeypot so any future access to it flows through
the entire detection system automatically.

A convincing but entirely fake README.txt file is uploaded to
the new bucket to make it look like a real, populated bucket
when an attacker initially inspects it.

### Template library

The mutation engine uses a template library: a Python dictionary
where each key is a category string and the value is a list of
bucket name templates containing a {year} placeholder that gets
replaced with the current 4-digit year at creation time.

Categories and example templates:

payment: "stripe-api-credentials-backup-{year}",
"payment-gateway-prod-keys-{year}"

credential: "admin-ssh-keys-backup-{year}",
"service-account-tokens-{year}"

database: "rds-prod-snapshot-restore-{year}",
"db-master-password-backup-{year}"

backup: "prod-system-full-backup-{year}",
"disaster-recovery-archives-{year}"

employee: "employee-salary-records-hr-{year}",
"personnel-files-confidential-{year}"

There is also a keyword-to-category mapping dictionary:
payment category maps to keywords: payment, billing, stripe, gateway
credential category maps to keywords: key, secret, token, auth, iam
database category maps to keywords: database, db, sql, rds, postgres
backup category maps to keywords: backup, snapshot, restore, archive
employee category maps to keywords: employee, salary, hr, personnel

### How category selection works

Concatenate all resource names the attacker probed into one string
and convert to lowercase. For each category, count how many of that
category's keywords appear in the combined string. The category with
the most keyword hits is selected as the mutation target.

If no keywords match at all, do not mutate. Return None.

If the generated bucket name already exists in the list of
previously created honeypots, do not create a duplicate. Return None.
Select a different template from the same category instead.

### S3 bucket creation requirements

The new bucket must be created in the same AWS region as the original
honeypot, which is `eu-north-1`.

Important: For all AWS regions other than us-east-1, the `create_bucket`
Boto3 call must include a `CreateBucketConfiguration` parameter specifying
the `LocationConstraint`. If this is omitted for eu-north-1, the call
will silently fail or raise an error.

After creating the bucket, apply the same SNS event notification
configuration as the original honeypot bucket using the SNS ARN
read from the environment variable `HONEYPOT_SNS_ARN`.
The notification must trigger on all ObjectCreated and ObjectRemoved events.

After applying the notification, upload a fake `README.txt` file
to the bucket. The file should look like a real internal document:
it should reference the bucket name, today's date, and contain
boilerplate text about restricted access and authorized personnel only.

### Tracking mutations

The engine must maintain an internal list of all honeypots it has created.
For each one it stores: the bucket name, the category that triggered it,
the IP of the attacker who triggered it, the attacker's inferred intent
at the time, and the creation timestamp.

### Where to put this

Create a new file: `intelligence/mutation_engine.py`

Create a class called `MutationEngine` with an `__init__` that
initializes the Boto3 S3 client and an empty list for tracking
created honeypots.

The main method is `mutate(profile)` which takes an attacker profile
dictionary from the AttackerProfiler (Feature 1) and either creates
a new honeypot and returns a mutation record dictionary, or returns
None if no mutation was appropriate.

Add a `get_created_honeypots()` method that returns the full list
of all created honeypots.

### How to wire into the existing FastAPI server

Import `MutationEngine` and initialize one instance at module level.

In the self-healing section (where Boto3 restricts the EC2 security group),
after the healing action completes, call `mutation_engine.mutate(profile)`.
If the result is not None, attach the mutation record to the event
as `event["mutation"]` so the dashboard can display it.

Add a new GET endpoint `/mutations` that returns
`mutation_engine.get_created_honeypots()`.

### What to add to the React dashboard

When an event in the live feed contains a `mutation` field,
show a distinct entry below it in the feed reading:
"New honeypot deployed: [bucket name] targeting [category] hunters.
Triggered by [attacker IP]."

Add a small counter somewhere on the dashboard showing the total
number of honeypots created by the mutation engine, polling
the `/mutations` endpoint.

### IAM permissions required on the EC2 instance role

The existing IAM role must have these permissions added before testing:
`s3:CreateBucket`, `s3:PutBucketNotificationConfiguration`,
`s3:PutObject`.

### .env entry required

`HONEYPOT_SNS_ARN=arn:aws:sns:eu-north-1:YOUR_ACCOUNT_ID:Sentinel-Honeypot-Alerts`

### Libraries required

No new libraries. Uses boto3 (already in the project), and random
and time from Python's standard library.

---

## Feature 5 — Auto-Generated PDF Forensic Report

### Build this last.

### What this feature does

When a judge clicks a Download Report button on the dashboard,
the system generates a formatted PDF incident report in real time
and serves it as a file download.

The PDF is generated entirely by the Python backend using the
ReportLab library. No external service is called. No template
file is needed.

### What the PDF report must contain

Page header:
The title "SentinelMesh Incident Report" in large text.
A subtitle line with the generation timestamp and a unique report ID.
A horizontal rule separator below the header.

Section — Executive Summary:
The Groq-generated plain-English summary from the most recent
audit event for this session. Typically 2–3 sentences.

Section — Threat Overview:
A two-column table with one row per data point.
Left column is the field label (muted gray text).
Right column is the value.
Rows: IP address, country and city, organization name,
whether they used Tor (YES with warning or No), behavior pattern type,
inferred intent, peak risk score out of 100, escalation probability
percentage, threat level label, total session duration in seconds,
and total number of resources probed.
The value text in the threat level row must be colored to match
severity: red for CRITICAL, amber for HIGH, orange for MEDIUM,
green for LOW.

Section — Attack Timeline:
A multi-column table with one row per event in the session.
Columns: sequential row number, time formatted as HH:MM:SS,
resource accessed (truncated to 40 characters if longer),
risk score at that moment, threat level at that moment.
Header row: dark background with white text.
Data rows: alternating white and light gray backgrounds.

Section — Autonomous Response Actions:
A list of every self-healing action taken with a checkmark prefix.
If no actions were taken, state that explicitly.

Section — Canary Token Alerts (conditional):
Only include this section if canary token events exist for this session.
For each canary hit, show a paragraph in red text stating:
the IP of the machine that opened the file, the user agent string,
and the timestamp.

Footer:
A thin horizontal rule followed by small gray text identifying
SentinelMesh, Symbiot 2026, and VVCE Mysuru.

### Report color palette

These colors match the existing dashboard theme:
Primary text: #0A0C0F
Cyan accent: #00E5FF (use sparingly)
Amber: #FFB300 (for HIGH severity)
Red: #FF1744 (for CRITICAL and canary alerts)
Green: #00E676 (for LOW threat and safe indicators)
Gray: #888888 (for labels and secondary text)

### How session data is assembled

When `/report/{session_id}` is called, filter the in-memory events
store for all events whose session_id matches.

Get the attacker profile from the AttackerProfiler using the IP
from the first event in the filtered list.

Assemble a session dictionary with: session ID, IP, all profile fields,
IP enrichment data from the first event, the complete filtered event list,
the highest risk score across all events, the Groq summary from the
last event, a list of all action strings from events that had actions,
a list of all events whose type is CANARY_TOKEN_HIT, and the session
duration from the profile.

Call the report generator function with this session dictionary
and a temporary file path such as `/tmp/sentinel_report_{session_id}.pdf`.

Return a FastAPI `FileResponse` pointing to the generated file,
with media type `application/pdf` and a descriptive filename.

### Where to put this

Create a new file: `reports/report_generator.py`

Create a single function called `generate_incident_report(session, output_path)`
that builds the complete PDF using ReportLab's Platypus framework
(SimpleDocTemplate, Paragraph, Table, TableStyle, HRFlowable, Spacer)
and writes it to output_path.

Add a new GET endpoint to `main_fastapi.py` at `/report/{session_id}`
that assembles the session data and calls the generator function,
then returns a FileResponse.

### How to add the download button to the React dashboard

In the audit log panel (Panel 4), add a button labeled
"Download Incident Report."

When clicked, it triggers a GET request to `/report/{session_id}`
which the browser handles as a file download.

For the demo: also print the report before presenting and have
physical copies ready to hand to judges. A printed forensic report
of an attack that happened minutes ago is an extremely strong
tangible artifact.

### Libraries required

Install: `reportlab`

---

## Complete Directory Structure After All Features

```
sentinelmesh/
├── main_fastapi.py                   (EXISTING — modified throughout)
├── .env                              (EXISTING — new entries added)
├── requirements.txt                  (EXISTING — new libraries added)
│
├── intelligence/
│   ├── __init__.py
│   ├── attacker_profiler.py          (NEW — Feature 1)
│   ├── ip_enricher.py                (NEW — Feature 2)
│   ├── risk_engine.py                (EXISTING — unchanged)
│   └── mutation_engine.py            (NEW — Feature 4)
│
├── reports/
│   ├── __init__.py
│   └── report_generator.py           (NEW — Feature 5)
│
├── data/
│   └── tor_exit_nodes.txt            (NEW — downloaded once before hackathon)
│
├── aws/
│   ├── __init__.py
│   └── aws_client.py                 (EXISTING — unchanged)
│
└── frontend/
    └── src/
        ├── panels/
        │   ├── PanelEventFeed.jsx    (EXISTING — updated for canary events)
        │   ├── PanelRiskGauge.jsx    (EXISTING — unchanged)
        │   ├── PanelWorldMap.jsx     (EXISTING — updated tooltips)
        │   ├── PanelAuditLog.jsx     (EXISTING — add download button)
        │   └── PanelAttackerIntel.jsx (NEW — Feature 1 dashboard panel)
        └── App.jsx                   (EXISTING — add new panel)
```

---

## Complete requirements.txt After All Features

```
fastapi
uvicorn
boto3
python-dotenv
requests
ipwhois
reportlab
groq
```

Single install command:
`pip install fastapi uvicorn boto3 python-dotenv requests ipwhois reportlab groq --break-system-packages`

---

## New .env Variables Required

```
HONEYPOT_SNS_ARN=arn:aws:sns:eu-north-1:YOUR_ACCOUNT_ID:Sentinel-Honeypot-Alerts
AWS_REGION=eu-north-1
```

---

## Complete List of All FastAPI Endpoints After All Features

EXISTING (unchanged):
POST /events          — receive incoming attack events from Lambda
GET  /heal            — trigger manual self-healing (for testing)
GET  /audit           — retrieve audit log
GET  /status          — system health check

NEW (added by these features):
GET  /profiles        — all attacker profiles sorted by escalation probability
GET  /profiles/{ip}   — single attacker profile by IP address
GET  /canary/track    — canary token tracking endpoint (returns blank 200)
GET  /mutations       — list of all honeypots created by mutation engine
GET  /report/{id}     — generate and serve PDF incident report as download

---

## The One-Sentence Pitch Per Feature for the Demo

Use these sentences during the live presentation. Memorize them.

Feature 1:
"We analyze timing intervals between probes to classify whether this
is a bot or a human, and infer their intent from which resources they
targeted — all in pure Python with no external API."

Feature 2:
"Every attacker IP is automatically cross-referenced against Tor exit
node databases and ASN records to reveal whether they are hiding
behind anonymity tools or using datacenter attack infrastructure."

Feature 3:
"We embedded a tracking URL inside the fake file. If the attacker
ever opens that file on their own machine, anywhere in the world,
we track it."

Feature 4:
"After every attack, the system analyzes what the attacker was hunting
for and automatically deploys a new honeypot designed specifically to
target their interest — the trap gets smarter with every attack."

Feature 5:
"Every incident auto-generates a forensic PDF report — here is the
one from the attack that just happened during this demo."

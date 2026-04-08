"""
Bug report pool — 30 bugs with investigation layers.

Each bug has:
  - Brief description (what the agent sees initially)
  - 3 investigation layers (logs, related bugs, reporter clarification)
  - Ground truth labels
  - Difficulty tier (easy / medium / hard)

Episodes sample randomly from this pool, so the agent cannot memorize answers.
Some bugs have misleading signals that require careful investigation.
"""

from typing import Dict, List, Tuple
import random

from .models import BugReport, BugGroundTruth, InvestigationLayers


class BugTemplate:
    """A complete bug with all investigation layers."""

    def __init__(
        self,
        bug: BugReport,
        truth: BugGroundTruth,
        layers: InvestigationLayers,
        difficulty: str,
    ):
        self.bug = bug
        self.truth = truth
        self.layers = layers
        self.difficulty = difficulty


# ===================================================================
# EASY BUGS — obvious type, clear signals
# ===================================================================

EASY_POOL: List[BugTemplate] = [
    BugTemplate(
        bug=BugReport(
            id="E01", title="Login button misaligned on iOS Safari",
            brief_description="The login button overlaps the 'Forgot Password' link on iOS Safari 17.",
            affected_component="frontend/auth", reporter_role="qa", frequency="always",
        ),
        truth=BugGroundTruth(bug_type="ui", severity="low", fix_keywords=["css", "safari", "webkit", "responsive"]),
        layers=InvestigationLayers(
            logs="No errors in console. CSS computed style shows `-webkit-appearance` conflict on `.btn-login`.",
            related="BUG-142: Similar Safari alignment issue fixed 3 months ago with `-webkit-` prefix.",
            reporter="QA says: 'Only happens on iOS 17+. iPad renders fine. Landscape mode is worse.'",
        ),
        difficulty="easy",
    ),
    BugTemplate(
        bug=BugReport(
            id="E02", title="API 500 on paginated /users endpoint",
            brief_description="GET /api/v2/users?page=5&limit=50 returns HTTP 500. Pages 1-4 work.",
            affected_component="backend/api", reporter_role="developer", frequency="always",
        ),
        truth=BugGroundTruth(bug_type="backend", severity="medium", fix_keywords=["pagination", "offset", "boundary", "index"]),
        layers=InvestigationLayers(
            logs="IndexError: list index out of range at views/users.py:42. users table has 180 records. page=5 offset=200 > 180.",
            related="BUG-089: Pagination edge case fixed in /products endpoint last quarter.",
            reporter="Developer says: 'Works with limit=25. Breaks when offset exceeds total count.'",
        ),
        difficulty="easy",
    ),
    BugTemplate(
        bug=BugReport(
            id="E03", title="Stored XSS in profile bio field",
            brief_description="Script tags in user bio execute when other users view the profile.",
            affected_component="frontend/profiles", reporter_role="developer", frequency="always",
        ),
        truth=BugGroundTruth(bug_type="security", severity="critical", fix_keywords=["sanitize", "escape", "xss", "csp", "validation"]),
        layers=InvestigationLayers(
            logs="No server-side sanitization. `bio` field stored raw HTML. Rendered with `dangerouslySetInnerHTML`.",
            related="BUG-201: XSS in comments was fixed with DOMPurify. Bio field was missed.",
            reporter="Developer says: 'I verified cookie theft is possible. Session tokens are HttpOnly=false.'",
        ),
        difficulty="easy",
    ),
    BugTemplate(
        bug=BugReport(
            id="E04", title="Charts invisible in dark mode",
            brief_description="Revenue and traffic charts render white-on-white in dark mode.",
            affected_component="frontend/dashboard", reporter_role="customer", frequency="always",
        ),
        truth=BugGroundTruth(bug_type="ui", severity="low", fix_keywords=["theme", "css", "chart", "dark", "color"]),
        layers=InvestigationLayers(
            logs="Chart.js config uses hardcoded colors: `fontColor: '#333'`. Does not read CSS variables.",
            related="BUG-156: Dark mode was added last sprint. Chart library was not updated.",
            reporter="Customer says: 'I can see the chart if I highlight/select all text. Tooltips also invisible.'",
        ),
        difficulty="easy",
    ),
    BugTemplate(
        bug=BugReport(
            id="E05", title="DB connection pool exhaustion under load",
            brief_description="Application unresponsive at >200 concurrent requests. All pool connections stuck.",
            affected_component="backend/database", reporter_role="developer", frequency="sometimes",
        ),
        truth=BugGroundTruth(bug_type="backend", severity="high", fix_keywords=["pool", "connection", "timeout", "leak", "close"]),
        layers=InvestigationLayers(
            logs="QueuePool limit of size 20 overflow 10 reached. Thread dump: 30 threads blocked on connection acquisition.",
            related="BUG-099: Similar pool issue in reporting service. Root cause was unclosed connections in error paths.",
            reporter="Developer says: 'Happens after ~45 min of sustained traffic. Restarting the app temporarily fixes it.'",
        ),
        difficulty="easy",
    ),
    BugTemplate(
        bug=BugReport(
            id="E06", title="Email notifications sent with wrong sender",
            brief_description="Password reset emails show 'noreply@dev.internal' instead of the production domain.",
            affected_component="backend/email", reporter_role="customer", frequency="always",
        ),
        truth=BugGroundTruth(bug_type="backend", severity="medium", fix_keywords=["config", "environment", "sender", "email", "production"]),
        layers=InvestigationLayers(
            logs="SMTP config: FROM_EMAIL loaded from .env.development, not .env.production. Deploy script doesn't override.",
            related="BUG-044: Similar env config issue affected API keys last month.",
            reporter="Customer says: 'Emails work, but my email client flags them as suspicious because of the sender domain.'",
        ),
        difficulty="easy",
    ),
    BugTemplate(
        bug=BugReport(
            id="E07", title="Mobile nav menu doesn't close on outside tap",
            brief_description="Hamburger menu stays open when tapping outside on mobile. Must tap the X button.",
            affected_component="frontend/navigation", reporter_role="qa", frequency="always",
        ),
        truth=BugGroundTruth(bug_type="ui", severity="low", fix_keywords=["click", "event", "overlay", "mobile", "close"]),
        layers=InvestigationLayers(
            logs="No global click listener. Menu has `z-index: 999` but no overlay backdrop element.",
            related="BUG-178: Desktop dropdown was fixed with `useClickOutside` hook. Mobile menu uses different component.",
            reporter="QA says: 'Swiping right also doesn't close it. Only the X button works.'",
        ),
        difficulty="easy",
    ),
    BugTemplate(
        bug=BugReport(
            id="E08", title="CORS error blocking frontend API calls",
            brief_description="Browser console shows CORS policy error for all POST requests from staging frontend.",
            affected_component="backend/api", reporter_role="developer", frequency="always",
        ),
        truth=BugGroundTruth(bug_type="backend", severity="high", fix_keywords=["cors", "origin", "headers", "allow", "middleware"]),
        layers=InvestigationLayers(
            logs="Access-Control-Allow-Origin header only includes production domain. Staging URL not whitelisted.",
            related="BUG-112: CORS was configured during initial API setup. New staging env was added later.",
            reporter="Developer says: 'GET requests work fine due to simple request. POST/PUT/DELETE all fail preflight.'",
        ),
        difficulty="easy",
    ),
    BugTemplate(
        bug=BugReport(
            id="E09", title="Unencrypted PII in application logs",
            brief_description="User email addresses and phone numbers appear in plaintext in application log files.",
            affected_component="backend/logging", reporter_role="developer", frequency="always",
        ),
        truth=BugGroundTruth(bug_type="security", severity="high", fix_keywords=["mask", "redact", "pii", "log", "filter"]),
        layers=InvestigationLayers(
            logs="Logger middleware serializes full request body. PII fields not filtered. Logs shipped to S3 unencrypted.",
            related="BUG-067: GDPR compliance audit flagged similar issue in error reporting service.",
            reporter="Developer says: 'Log retention is 90 days. Anyone with S3 read access can see PII.'",
        ),
        difficulty="easy",
    ),
    BugTemplate(
        bug=BugReport(
            id="E10", title="Cron job running in wrong timezone",
            brief_description="Daily report generation runs at 3 AM UTC instead of 3 AM PST, missing West Coast data.",
            affected_component="backend/scheduler", reporter_role="qa", frequency="always",
        ),
        truth=BugGroundTruth(bug_type="backend", severity="medium", fix_keywords=["timezone", "utc", "cron", "schedule", "config"]),
        layers=InvestigationLayers(
            logs="Cron expression: `0 3 * * *`. Server TZ=UTC. Application code uses `datetime.now()` without tz.",
            related="BUG-155: Timezone handling was refactored for EU expansion. US schedules were not updated.",
            reporter="QA says: 'Reports show data through 8 PM PST the previous day. Should include full 24h.'",
        ),
        difficulty="easy",
    ),
]

# ===================================================================
# MEDIUM BUGS — need investigation to determine severity correctly
# ===================================================================

MEDIUM_POOL: List[BugTemplate] = [
    BugTemplate(
        bug=BugReport(
            id="M01", title="Auth tokens persist after password change",
            brief_description="Users report that changing password doesn't invalidate active sessions.",
            affected_component="backend/auth", reporter_role="developer", frequency="always",
        ),
        truth=BugGroundTruth(bug_type="security", severity="critical", fix_keywords=["invalidation", "jwt", "blacklist", "rotation", "revocation"]),
        layers=InvestigationLayers(
            logs="JWT tokens have 7-day expiry. No server-side token revocation list. Password change only updates DB hash.",
            related="BUG-230: Session management overhaul was planned for Q2 but deprioritized.",
            reporter="Developer says: 'A user whose credentials were compromised changed their password but attacker still had access for 7 days.'",
        ),
        difficulty="medium",
    ),
    BugTemplate(
        bug=BugReport(
            id="M02", title="Memory growth in WebSocket handler",
            brief_description="Server memory grows steadily over 48 hours, eventually triggering OOM kills.",
            affected_component="backend/websocket", reporter_role="developer", frequency="always",
        ),
        truth=BugGroundTruth(bug_type="backend", severity="high", fix_keywords=["memory", "buffer", "cleanup", "finally", "disconnect", "leak"]),
        layers=InvestigationLayers(
            logs="MemoryError after 48h. Heap dump shows 14k orphaned buffer objects. Abnormal disconnect path skips cleanup().",
            related="BUG-188: Similar leak in file upload handler was fixed by adding try/finally.",
            reporter="Developer says: 'Normal graceful disconnects are fine. Only abnormal disconnects (network drop, client crash) cause the leak.'",
        ),
        difficulty="medium",
    ),
    BugTemplate(
        bug=BugReport(
            id="M03", title="Validation errors overlap inputs on mobile",
            brief_description="Form error messages overlap with input fields on small screens.",
            affected_component="frontend/forms", reporter_role="qa", frequency="sometimes",
        ),
        truth=BugGroundTruth(bug_type="ui", severity="low", fix_keywords=["responsive", "overflow", "height", "mobile", "css"]),
        layers=InvestigationLayers(
            logs="Error div has fixed `height: 20px`. Multi-line messages overflow. No `overflow: visible` set.",
            related="BUG-134: Similar overflow issue was fixed in the settings page form.",
            reporter="QA says: 'Users can still read messages by scrolling. But the form looks broken on iPhone SE.'",
        ),
        difficulty="medium",
    ),
    BugTemplate(
        bug=BugReport(
            id="M04", title="Search returns stale results after update",
            brief_description="Product price changes take ~30 seconds to appear in search results.",
            affected_component="backend/search", reporter_role="qa", frequency="always",
        ),
        truth=BugGroundTruth(bug_type="backend", severity="medium", fix_keywords=["cache", "invalidation", "redis", "ttl", "refresh"]),
        layers=InvestigationLayers(
            logs="Elasticsearch refresh interval: 1s. But Redis cache layer has 30s TTL. Search reads from Redis first.",
            related="BUG-145: Cache invalidation strategy was documented but not implemented for all entity types.",
            reporter="QA says: 'Customer see old prices for 30 seconds. Some placed orders at wrong price.'",
        ),
        difficulty="medium",
    ),
    BugTemplate(
        bug=BugReport(
            id="M05", title="API key exposed in frontend JS bundle",
            brief_description="Internal analytics API key with write access found in compiled JavaScript.",
            affected_component="frontend/build", reporter_role="developer", frequency="always",
        ),
        truth=BugGroundTruth(bug_type="security", severity="high", fix_keywords=["environment", "server", "secret", "build", "key", "proxy"]),
        layers=InvestigationLayers(
            logs="Webpack config includes `ANALYTICS_WRITE_KEY` in DefinePlugin. Key visible in source map.",
            related="BUG-198: Public API keys (Stripe publishable) are intentionally in frontend. This one has write access.",
            reporter="Developer says: 'Key has permission to delete analytics events and modify dashboards.'",
        ),
        difficulty="medium",
    ),
    BugTemplate(
        bug=BugReport(
            id="M06", title="Slow query on user search endpoint",
            brief_description="GET /api/users/search takes 8-12 seconds when searching by name.",
            affected_component="backend/api", reporter_role="developer", frequency="always",
        ),
        truth=BugGroundTruth(bug_type="backend", severity="high", fix_keywords=["index", "query", "database", "like", "optimize", "scan"]),
        layers=InvestigationLayers(
            logs="EXPLAIN shows full table scan. `WHERE name LIKE '%query%'` on 2M rows. No trigram or fulltext index.",
            related="BUG-077: Product search was optimized with pg_trgm index. User search was left as-is.",
            reporter="Developer says: 'Dashboard search is now unusable for support team. They search users 50+ times per day.'",
        ),
        difficulty="medium",
    ),
    BugTemplate(
        bug=BugReport(
            id="M07", title="File upload allows .exe and .bat extensions",
            brief_description="Users can upload executable files through the document upload feature.",
            affected_component="backend/uploads", reporter_role="qa", frequency="always",
        ),
        truth=BugGroundTruth(bug_type="security", severity="high", fix_keywords=["whitelist", "extension", "validation", "mime", "upload"]),
        layers=InvestigationLayers(
            logs="Upload endpoint checks file size only. No extension or MIME type validation. Files served from /uploads/ directly.",
            related="BUG-210: Image upload has proper validation. Document upload uses a different code path.",
            reporter="QA says: 'Uploaded a test .exe file, shared the link, and it auto-downloaded when another user clicked.'",
        ),
        difficulty="medium",
    ),
    BugTemplate(
        bug=BugReport(
            id="M08", title="Duplicate order creation on double-click",
            brief_description="Clicking 'Place Order' quickly twice creates two identical orders.",
            affected_component="backend/orders", reporter_role="customer", frequency="sometimes",
        ),
        truth=BugGroundTruth(bug_type="backend", severity="high", fix_keywords=["idempotency", "debounce", "lock", "duplicate", "token"]),
        layers=InvestigationLayers(
            logs="Two POST /api/orders within 200ms, same payload. Both succeed. No idempotency key check.",
            related="BUG-121: Payment endpoint has idempotency key. Order creation endpoint doesn't.",
            reporter="Customer says: 'I was charged twice. Second order shipped too. Had to call support for refund.'",
        ),
        difficulty="medium",
    ),
    BugTemplate(
        bug=BugReport(
            id="M09", title="Tooltip cut off at viewport edge",
            brief_description="Help tooltips near the right edge of the screen are partially hidden.",
            affected_component="frontend/components", reporter_role="qa", frequency="always",
        ),
        truth=BugGroundTruth(bug_type="ui", severity="low", fix_keywords=["position", "viewport", "overflow", "tooltip", "boundary"]),
        layers=InvestigationLayers(
            logs="Tooltip uses `position: absolute; left: 100%`. No boundary detection. CSS `overflow: hidden` on parent.",
            related="BUG-163: Dropdown menus had same issue, fixed with Popper.js boundary detection.",
            reporter="QA says: 'Only affects rightmost column in data tables. Info is still accessible via hover text.'",
        ),
        difficulty="medium",
    ),
    BugTemplate(
        bug=BugReport(
            id="M10", title="Rate limiter not applied to login endpoint",
            brief_description="No rate limiting on POST /auth/login allows unlimited password attempts.",
            affected_component="backend/auth", reporter_role="developer", frequency="always",
        ),
        truth=BugGroundTruth(bug_type="security", severity="critical", fix_keywords=["rate", "limit", "brute", "throttle", "lockout"]),
        layers=InvestigationLayers(
            logs="Ran 10,000 login attempts in 30 seconds. No 429 responses. No account lockout triggered.",
            related="BUG-215: Rate limiter configured on API gateway but /auth/* routes are excluded.",
            reporter="Developer says: 'We use bcrypt so each attempt is slow server-side, but an attacker can run parallel requests.'",
        ),
        difficulty="medium",
    ),
]

# ===================================================================
# HARD BUGS — ambiguous, need investigation, complex root causes
# ===================================================================

HARD_POOL: List[BugTemplate] = [
    BugTemplate(
        bug=BugReport(
            id="H01", title="Race condition in distributed order processing",
            brief_description="Occasionally inventory is decremented twice for a single order during peak traffic.",
            affected_component="backend/orders", reporter_role="developer", frequency="rare",
        ),
        truth=BugGroundTruth(bug_type="backend", severity="critical", fix_keywords=["lock", "idempotency", "atomic", "transaction", "retry", "mutex"]),
        layers=InvestigationLayers(
            logs="Two instances process same order (retry triggered). Optimistic lock check and inventory update are separate queries. ~0.1% of orders affected.",
            related="BUG-190: Similar race in coupon redemption was fixed with SELECT FOR UPDATE.",
            reporter="Developer says: 'Phantom inventory loss totals ~$50k/month. Finance team flagged the discrepancy.'",
        ),
        difficulty="hard",
    ),
    BugTemplate(
        bug=BugReport(
            id="H02", title="CSRF in administrative state-changing endpoints",
            brief_description="Several admin actions use GET requests without CSRF protection.",
            affected_component="backend/admin", reporter_role="developer", frequency="always",
        ),
        truth=BugGroundTruth(bug_type="security", severity="critical", fix_keywords=["csrf", "post", "token", "middleware", "referer"]),
        layers=InvestigationLayers(
            logs="GET /admin/user/123/delete, GET /admin/settings/reset — no CSRF token, no referer check. An img tag can trigger destructive actions.",
            related="BUG-203: Public-facing forms have CSRF tokens. Admin panel was built by a different team without the middleware.",
            reporter="Developer says: 'Demonstrated attack: crafted a page with invisible img pointing to delete endpoint. Admin visiting the page unknowingly deleted a user.'",
        ),
        difficulty="hard",
    ),
    BugTemplate(
        bug=BugReport(
            id="H03", title="Data corruption during live schema migration",
            brief_description="After a production migration, ~12,000 rows have NULL in a NOT NULL column.",
            affected_component="backend/database", reporter_role="developer", frequency="always",
        ),
        truth=BugGroundTruth(bug_type="backend", severity="critical", fix_keywords=["migration", "backfill", "null", "default", "downtime", "deploy"]),
        layers=InvestigationLayers(
            logs="ALTER TABLE orders ADD COLUMN shipping_tier NOT NULL DEFAULT 'standard' — ran on 50M rows for 45 min. Concurrent INSERTs during migration created rows before default was applied.",
            related="BUG-167: Previous migration used two-phase approach (add nullable → backfill → add constraint). This one skipped that.",
            reporter="Developer says: 'ORM throws IntegrityError on reads of affected rows. Customer orders from that 45-min window are broken.'",
        ),
        difficulty="hard",
    ),
    BugTemplate(
        bug=BugReport(
            id="H04", title="Silent data loss in collaborative editor",
            brief_description="When two users edit the same paragraph simultaneously, one user's changes sometimes disappear.",
            affected_component="frontend/editor", reporter_role="customer", frequency="sometimes",
        ),
        truth=BugGroundTruth(bug_type="ui", severity="medium", fix_keywords=["crdt", "conflict", "resolution", "merge", "cursor", "transform"]),
        layers=InvestigationLayers(
            logs="console.warn: 'OT transform conflict, falling back to server state'. Operational transformation doesn't handle same-position inserts.",
            related="BUG-245: Team evaluated CRDT libraries (Yjs, Automerge) as replacement but hasn't migrated.",
            reporter="Customer says: 'I spent 20 minutes writing a section and it vanished. No undo history for the lost text. Happens ~5% of the time.'",
        ),
        difficulty="hard",
    ),
    BugTemplate(
        bug=BugReport(
            id="H05", title="Privilege escalation via parameter tampering",
            brief_description="A user endpoint accepts role changes without verifying authorization.",
            affected_component="backend/auth", reporter_role="developer", frequency="always",
        ),
        truth=BugGroundTruth(bug_type="security", severity="critical", fix_keywords=["authorization", "rbac", "permission", "middleware", "role", "privilege"]),
        layers=InvestigationLayers(
            logs="PUT /api/users/{id}/role accepts {role: 'admin'} from any authenticated user. Only checks auth token validity, not role permissions.",
            related="BUG-220: Other sensitive endpoints were audited after a pentest. This one was added after the audit.",
            reporter="Developer says: 'Verified: created a free-tier account, changed own role to admin, gained access to all admin features.'",
        ),
        difficulty="hard",
    ),
    BugTemplate(
        bug=BugReport(
            id="H06", title="Cascading failure in microservices circuit breaker",
            brief_description="When the payment service goes down, the entire platform becomes unresponsive within 5 minutes.",
            affected_component="backend/infrastructure", reporter_role="developer", frequency="rare",
        ),
        truth=BugGroundTruth(bug_type="backend", severity="critical", fix_keywords=["circuit", "breaker", "timeout", "fallback", "bulkhead", "resilience"]),
        layers=InvestigationLayers(
            logs="Payment service timeout: 30s. Order service has 200 threads, all blocked waiting on payment. Health check fails. K8s restarts order service. Cascade continues.",
            related="BUG-180: Circuit breaker library (Hystrix) was added but configured with threshold=100 (too high) and never tested.",
            reporter="Developer says: 'During last outage, all 6 downstream services went down in sequence. Recovery took 45 minutes of manual restarts.'",
        ),
        difficulty="hard",
    ),
    BugTemplate(
        bug=BugReport(
            id="H07", title="Inconsistent read-after-write in distributed cache",
            brief_description="Users update their profile but see old data when refreshing. Eventually shows correct data.",
            affected_component="backend/cache", reporter_role="qa", frequency="sometimes",
        ),
        truth=BugGroundTruth(bug_type="backend", severity="medium", fix_keywords=["consistency", "cache", "invalidation", "write-through", "replication"]),
        layers=InvestigationLayers(
            logs="Write goes to Redis primary. Read hits a replica. Replication lag: 50-200ms. No read-your-writes consistency.",
            related="BUG-159: Session store had same issue. Fixed by reading from primary after writes for 2 seconds.",
            reporter="QA says: 'Reproducible: update profile → immediately refresh → see old data. Wait 1 second → data correct. Users think save failed.'",
        ),
        difficulty="hard",
    ),
    BugTemplate(
        bug=BugReport(
            id="H08", title="JWT secret shared across environments",
            brief_description="Tokens generated in development environment are accepted by production API.",
            affected_component="backend/auth", reporter_role="developer", frequency="always",
        ),
        truth=BugGroundTruth(bug_type="security", severity="critical", fix_keywords=["secret", "environment", "rotation", "key", "signing", "isolation"]),
        layers=InvestigationLayers(
            logs="JWT_SECRET in prod and dev .env files are identical: 'supersecret123'. Token signed in dev validates in prod.",
            related="BUG-231: Secrets management migration to Vault was started but JWT secret was missed.",
            reporter="Developer says: 'Any developer can generate a prod-valid admin token locally. We have 40 developers.'",
        ),
        difficulty="hard",
    ),
    BugTemplate(
        bug=BugReport(
            id="H09", title="Deadlock in concurrent batch processing",
            brief_description="Nightly batch job hangs indefinitely about once a week.",
            affected_component="backend/batch", reporter_role="developer", frequency="rare",
        ),
        truth=BugGroundTruth(bug_type="backend", severity="high", fix_keywords=["deadlock", "lock", "order", "transaction", "timeout", "retry"]),
        layers=InvestigationLayers(
            logs="pg_stat_activity shows 2 transactions waiting on each other. TX1 holds lock on orders, waits for inventory. TX2 holds inventory lock, waits for orders.",
            related="BUG-176: Single-threaded version never deadlocked. Bug appeared when parallelism was added for performance.",
            reporter="Developer says: 'When it hangs, no data is processed. Morning reports are empty. Operations team manually kills and reruns.'",
        ),
        difficulty="hard",
    ),
    BugTemplate(
        bug=BugReport(
            id="H10", title="Timing side-channel in password comparison",
            brief_description="Login endpoint response times vary based on how many password characters are correct.",
            affected_component="backend/auth", reporter_role="developer", frequency="always",
        ),
        truth=BugGroundTruth(bug_type="security", severity="high", fix_keywords=["constant", "time", "comparison", "hmac", "timing", "side-channel"]),
        layers=InvestigationLayers(
            logs="Password check uses Python `==` operator. Correct first N characters: ~0.1ms per char faster. Statistical analysis can extract passwords in ~10k requests.",
            related="BUG-199: API key comparison was fixed to use `hmac.compare_digest`. Password comparison was not updated.",
            reporter="Developer says: 'Combined with no rate limiting (BUG M10), an attacker could extract passwords character by character.'",
        ),
        difficulty="hard",
    ),
]


# ---------------------------------------------------------------------------
# Task configuration
# ---------------------------------------------------------------------------

TASK_CONFIG = {
    "easy": {
        "pool": EASY_POOL,
        "sample_size": 5,
        "investigation_budget": 0,  # Full info given, no investigation needed
        "show_full_info": True,
    },
    "medium": {
        "pool": MEDIUM_POOL,
        "sample_size": 5,
        "investigation_budget": 10,  # 10 investigations for 5 bugs (2 per bug avg)
        "show_full_info": False,
    },
    "hard": {
        "pool": HARD_POOL,
        "sample_size": 5,
        "investigation_budget": 6,  # 6 investigations for 5 bugs — forces strategic choice
        "show_full_info": False,
    },
}

VALID_TASKS = list(TASK_CONFIG.keys())
VALID_INVESTIGATIONS = ["logs", "related", "reporter"]


def sample_bugs(task: str, seed: int = None) -> List[BugTemplate]:
    """Sample bugs from the task pool. Different each episode."""
    config = TASK_CONFIG[task]
    rng = random.Random(seed)
    pool = list(config["pool"])
    rng.shuffle(pool)
    return pool[: config["sample_size"]]

"""Transactional email via Resend. Silently no-ops if RESEND_API_KEY is unset."""
import logging
import os
from typing import Optional

logger = logging.getLogger("veritas.email")

_FROM = "Veritas <noreply@veritas-demo.web.app>"
_DASHBOARD_URL = "https://veritas-demo.web.app/dashboard.html"


def _client():
    try:
        import resend
        key = os.getenv("RESEND_API_KEY", "")
        if not key:
            return None
        resend.api_key = key
        return resend
    except ImportError:
        return None


def send_analysis_complete(
    to_email: str,
    filename: str,
    high_count: int,
    medium_count: int,
) -> None:
    r = _client()
    if not r or not to_email:
        return
    verdict = "🔴 High-risk clauses found" if high_count else ("🟡 Issues to review" if medium_count else "🟢 No major issues")
    try:
        r.Emails.send({
            "from": _FROM,
            "to": [to_email],
            "subject": f"Veritas analysis ready — {filename}",
            "html": f"""
<div style="font-family:monospace;background:#09090b;color:#fafafa;padding:32px;border-radius:8px;max-width:560px;">
  <p style="color:#888;font-size:11px;margin:0 0 16px;">// veritas — contract risk analysis</p>
  <h2 style="margin:0 0 8px;font-size:18px;">Your analysis is ready.</h2>
  <p style="color:#a1a1aa;margin:0 0 24px;font-size:14px;">{filename}</p>
  <div style="background:#18181b;border:1px solid #27272a;border-radius:6px;padding:16px;margin-bottom:24px;">
    <p style="margin:0 0 8px;font-size:13px;">{verdict}</p>
    <p style="color:#888;font-size:12px;margin:0;">
      {high_count} high-risk &nbsp;·&nbsp; {medium_count} medium-risk findings
    </p>
  </div>
  <a href="{_DASHBOARD_URL}" style="display:inline-block;background:#fafafa;color:#09090b;padding:10px 20px;border-radius:9999px;text-decoration:none;font-size:13px;font-weight:600;">View in dashboard →</a>
  <p style="color:#52525b;font-size:11px;margin-top:32px;">Not legal advice — consult a Fachanwalt for binding guidance.</p>
</div>""",
        })
        logger.info("Analysis complete email sent to %s", to_email)
    except Exception as e:
        logger.warning("Failed to send analysis email: %s", e)


def send_limit_warning(
    to_email: str,
    tier: str,
    count: int,
    limit: int,
) -> None:
    r = _client()
    if not r or not to_email:
        return
    try:
        r.Emails.send({
            "from": _FROM,
            "to": [to_email],
            "subject": "You're approaching your Veritas monthly limit",
            "html": f"""
<div style="font-family:monospace;background:#09090b;color:#fafafa;padding:32px;border-radius:8px;max-width:560px;">
  <p style="color:#888;font-size:11px;margin:0 0 16px;">// veritas — usage alert</p>
  <h2 style="margin:0 0 8px;font-size:18px;">You've used {count} of {limit} analyses this month.</h2>
  <p style="color:#a1a1aa;margin:0 0 24px;font-size:14px;">
    Your <b>{tier.capitalize()}</b> plan allows {limit} analyses per month.
    Upgrade to Pro for 10 analyses/month.
  </p>
  <a href="{_DASHBOARD_URL}" style="display:inline-block;background:#fafafa;color:#09090b;padding:10px 20px;border-radius:9999px;text-decoration:none;font-size:13px;font-weight:600;">Upgrade plan →</a>
</div>""",
        })
        logger.info("Limit warning email sent to %s", to_email)
    except Exception as e:
        logger.warning("Failed to send limit warning email: %s", e)

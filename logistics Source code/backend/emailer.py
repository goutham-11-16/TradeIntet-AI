"""Emergent-managed email delivery (Resend proxy) for TradeIntel AI alerts."""
import os
import logging
import httpx

logger = logging.getLogger("tradeintel.email")

EMAIL_BASE_URL = "https://integrations.emergentagent.com"  # constant — survives deploy
EMAIL_KEY = os.environ.get("EMERGENT_EMAIL_KEY")
EMAIL_FROM_NAME = os.environ.get("EMAIL_FROM_NAME", "TradeIntel AI")


async def send_email(recipient: str, subject: str, html: str, reply_to: str | None = None) -> dict:
    payload = {"to": [recipient], "subject": subject, "html": html, "from_name": EMAIL_FROM_NAME}
    if reply_to:
        payload["contact_email"] = reply_to
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(f"{EMAIL_BASE_URL}/api/v1/email/send",
                                 headers={"X-Email-Key": EMAIL_KEY}, json=payload)
    resp.raise_for_status()
    try:
        return {"id": resp.json().get("id")}
    except Exception:
        return {"id": None}


LEVEL_COLOR = {"Critical": "#EF4444", "High": "#F97316", "Warning": "#F59E0B", "Info": "#0EA5E9"}


def alert_email_html(alert: dict) -> str:
    color = LEVEL_COLOR.get(alert.get("level"), "#2563EB")
    ship = alert.get("shipment_id")
    return f"""
<table width="100%" cellpadding="0" cellspacing="0" style="background:#f1f5f9;padding:24px;font-family:Arial,Helvetica,sans-serif">
 <tr><td align="center">
  <table width="560" cellpadding="0" cellspacing="0" style="background:#ffffff;border-radius:10px;overflow:hidden;border:1px solid #e2e8f0">
   <tr><td style="background:#020617;padding:18px 24px;color:#ffffff;font-size:18px;font-weight:bold">TradeIntel AI</td></tr>
   <tr><td style="padding:8px 24px 0">
     <span style="display:inline-block;background:{color};color:#fff;font-size:12px;font-weight:bold;padding:3px 10px;border-radius:6px">{alert.get('level','').upper()} ALERT</span>
   </td></tr>
   <tr><td style="padding:14px 24px 4px;font-size:18px;font-weight:bold;color:#020617">{alert.get('title','')}</td></tr>
   <tr><td style="padding:0 24px 14px;font-size:14px;color:#475569;line-height:1.5">{alert.get('message','')}</td></tr>
   {f'<tr><td style="padding:0 24px 18px;font-size:13px;color:#475569">Shipment: <b>{ship}</b></td></tr>' if ship else ''}
   <tr><td style="padding:0 24px 22px">
     <a href="#" style="background:#2563EB;color:#fff;text-decoration:none;font-size:14px;font-weight:bold;padding:10px 18px;border-radius:8px;display:inline-block">Open in TradeIntel AI</a>
   </td></tr>
   <tr><td style="background:#f8fafc;padding:14px 24px;font-size:11px;color:#94a3b8;border-top:1px solid #e2e8f0">
     Automated alert from your TradeIntel AI workspace. Risk predictions are estimates, not guarantees.
   </td></tr>
  </table>
 </td></tr>
</table>"""

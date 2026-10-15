function escapeHtml(value) {
  return String(value || '')
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;');
}

export default async function handler(req, res) {
  if (req.method !== 'POST') {
    return res.status(405).json({ error: 'Method not allowed' });
  }

  const body = req.body || {};
  const name = String(body.name || '').trim();
  const email = String(body.email || '').trim();
  const phone = String(body.phone || '').trim();
  const signature = String(body.signature || '').trim();
  const declined = Boolean(body.declined);
  const understood = Boolean(body.understood);

  if (!name || !email || !signature || !declined || !understood) {
    return res.status(400).json({ error: 'Please complete all required fields.' });
  }

  if (signature.toLowerCase() !== name.toLowerCase()) {
    return res.status(400).json({ error: 'Signature must match your full name.' });
  }

  const reference = 'PTW-' + Date.now().toString(36).toUpperCase();
  const signedAt = new Date().toLocaleString('en-GB', { timeZone: 'Europe/London' });

  const RESEND_API_KEY = process.env.RESEND_API_KEY;
  const NOTIFY_EMAIL = process.env.WAIVER_NOTIFY_EMAIL || process.env.PRICELIST_NOTIFY_EMAIL || 'hello@jojoandflo.com';

  if (RESEND_API_KEY) {
    try {
      await fetch('https://api.resend.com/emails', {
        method: 'POST',
        headers: {
          Authorization: `Bearer ${RESEND_API_KEY}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          from: 'JOJO & FLO <onboarding@resend.dev>',
          to: NOTIFY_EMAIL,
          reply_to: email,
          subject: `Patch test declined: ${name} (${reference})`,
          html: `
            <h2>Patch test waiver</h2>
            <p>A client has e-signed a waiver declining a patch test.</p>
            <p><strong>Reference:</strong> ${escapeHtml(reference)}</p>
            <p><strong>Name:</strong> ${escapeHtml(name)}</p>
            <p><strong>Email:</strong> ${escapeHtml(email)}</p>
            <p><strong>Phone:</strong> ${escapeHtml(phone || 'Not given')}</p>
            <p><strong>Typed signature:</strong> ${escapeHtml(signature)}</p>
            <p><strong>Declined patch test:</strong> Yes</p>
            <p><strong>Acknowledged risk:</strong> Yes</p>
            <p><strong>Signed:</strong> ${escapeHtml(signedAt)}</p>
            <hr>
            <p style="color:#888;font-size:13px;">Submitted from the JOJO &amp; FLO website terms page.</p>
          `,
        }),
      });
    } catch (err) {
      console.error('Waiver email send error (non-blocking):', err);
    }
  }

  return res.status(200).json({ ok: true, reference, signedAt });
}

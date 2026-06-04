import { generateToken } from './_shared.js';

export default async function handler(req, res) {
  if (req.method !== 'POST') {
    return res.status(405).json({ error: 'Method not allowed' });
  }

  const { name, email } = req.body || {};

  if (!name || !email) {
    return res.status(400).json({ error: 'Name and email are required' });
  }

  const RESEND_API_KEY = process.env.RESEND_API_KEY;
  const NOTIFY_EMAIL = process.env.PRICELIST_NOTIFY_EMAIL || 'banningp@gmail.com';

  const token = generateToken(email);

  if (RESEND_API_KEY) {
    try {
      await fetch('https://api.resend.com/emails', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${RESEND_API_KEY}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          from: 'JOJO & FLO <onboarding@resend.dev>',
          to: NOTIFY_EMAIL,
          subject: `Price List Request: ${name}`,
          html: `
            <h2>New Price List Request</h2>
            <p><strong>Name:</strong> ${name}</p>
            <p><strong>Email:</strong> ${email}</p>
            <p><strong>Date:</strong> ${new Date().toLocaleString('en-GB', { timeZone: 'Europe/London' })}</p>
            <hr>
            <p style="color:#888;font-size:13px;">This person viewed the JOJO &amp; FLO price list on the website.</p>
          `,
        }),
      });
    } catch (err) {
      console.error('Email send error (non-blocking):', err);
    }
  }

  return res.status(200).json({ ok: true, token });
}

import { createHash } from 'crypto';

const TOKEN_SECRET = process.env.PRICELIST_SECRET || 'jf-pricelist-default-secret-change-me';

export function generateToken(email) {
  const payload = email + '|' + Date.now();
  const hmac = createHash('sha256').update(payload + TOKEN_SECRET).digest('hex').slice(0, 32);
  const encoded = Buffer.from(payload).toString('base64url');
  return encoded + '.' + hmac;
}

export function verifyToken(token) {
  if (!token || !token.includes('.')) return false;
  const [encoded, hmac] = token.split('.');
  try {
    const payload = Buffer.from(encoded, 'base64url').toString();
    const expected = createHash('sha256').update(payload + TOKEN_SECRET).digest('hex').slice(0, 32);
    return hmac === expected;
  } catch {
    return false;
  }
}

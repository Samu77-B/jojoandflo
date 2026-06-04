import { readFileSync } from 'fs';
import { join } from 'path';
import { verifyToken } from './_shared.js';

export default function handler(req, res) {
  const { token } = req.query;

  if (!token || !verifyToken(token)) {
    res.status(403).json({ error: 'Unauthorized' });
    return;
  }

  try {
    const imgPath = join(process.cwd(), 'imgs', 'pricelist-summer2026.png');
    const imgBuffer = readFileSync(imgPath);

    res.setHeader('Content-Type', 'image/png');
    res.setHeader('Cache-Control', 'private, max-age=3600');

    if (req.query.dl === '1') {
      res.setHeader('Content-Disposition', 'attachment; filename="JoJo-and-Flo-Price-List-Summer-2026.png"');
    }

    res.status(200).send(imgBuffer);
  } catch (err) {
    console.error('Image serve error:', err);
    res.status(500).json({ error: 'Failed to load image' });
  }
}

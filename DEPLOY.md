# Deploy JoJo & Flo to Vercel (Temporary Client Preview)

Your site is ready to deploy. Follow these steps:

## Option A: Deploy with Vercel CLI (Fastest - No Git needed)

1. Install Vercel CLI (if you don't have it):
   ```
   npm i -g vercel
   ```

2. From this folder, run:
   ```
   cd c:\Websites\JoJoandflo.com\website
   vercel
   ```

3. Follow the prompts (login if needed, accept defaults)
4. You'll get a URL like: `https://jojo-flo-xxxx.vercel.app`

---

## Option B: Deploy via Git + Vercel Dashboard

1. **Initialize Git and push to GitHub:**
   ```powershell
   cd c:\Websites\JoJoandflo.com\website
   git init
   git add .
   git commit -m "Initial commit - JoJo & Flo site"
   ```

2. Create a new repo on GitHub, then:
   ```powershell
   git remote add origin https://github.com/YOUR_USERNAME/jojo-flo-preview.git
   git branch -M main
   git push -u origin main
   ```

3. **Deploy on Vercel:**
   - Go to [vercel.com](https://vercel.com) and sign in
   - Click "Add New" → "Project"
   - Import your GitHub repo
   - Click "Deploy" (no build settings needed for static HTML)

---

## Your URLs After Deployment

- **Home page:** `https://your-project.vercel.app/` or `/index.html`
- **Mobile version:** `https://your-project.vercel.app/mobile.html` or `/mobile`

---

## Railway Alternative

If you prefer Railway, create a `railway.json` or use a simple Node static server. For a quick static HTML site, Vercel is simpler and free.

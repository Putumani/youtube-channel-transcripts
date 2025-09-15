*YouTube Channel Transcripts
   A monorepo for scraping and displaying YouTube channel transcripts using React, shadcn/ui, Python, and Supabase.

**Structure
packages/frontend: React app with shadcn/ui for displaying transcripts.
packages/backend: Python script for scraping transcripts and storing in Supabase.
supabase/migrations: Database schema for Supabase.

**Setup
- Install dependencies:pnpm install


**Set up environment variables (see below).
- Run the frontend:pnpm frontend:dev

- Run the backend:pnpm backend:run



**Environment Variables

- Frontend: Create packages/frontend/.env with:VITE_SUPABASE_URL=YOUR_SUPABASE_URL
VITE_SUPABASE_ANON_KEY=YOUR_SUPABASE_ANON_KEY

- Backend: Create packages/backend/.env with:SUPABASE_URL=YOUR_SUPABASE_URL
SUPABASE_KEY=YOUR_SUPABASE_SERVICE_ROLE_KEY



**Deployment

- Frontend: Deploy to Vercel or Netlify.
- Backend: Deploy as a serverless function (e.g., Vercel Functions) or run on a server (e.g., Render).


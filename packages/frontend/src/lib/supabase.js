import { createClient } from '@supabase/supabase-js'

const supabaseUrl = import.meta.env.VITE_SUPABASE_URL
const supabaseAnonKey = import.meta.env.VITE_SUPABASE_ANON_KEY

if (!supabaseUrl || !supabaseAnonKey) {
    const missingVars = []
    if (!supabaseUrl) missingVars.push('VITE_SUPABASE_URL')
    if (!supabaseAnonKey) missingVars.push('VITE_SUPABASE_ANON_KEY')

    throw new Error(
        `Missing required environment variables: ${missingVars.join(', ')}.\n` +
        'Please check your .env file or Vercel environment variables.'
    )
}

export const supabase = createClient(supabaseUrl, supabaseAnonKey)
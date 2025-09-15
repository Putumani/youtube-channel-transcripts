-- Create channels table
   CREATE TABLE channels (
     id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
     channel_id TEXT NOT NULL UNIQUE,
     title TEXT NOT NULL,
     uploads_playlist TEXT NOT NULL,
     created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
   );

   -- Create transcripts table
   CREATE TABLE transcripts (
     id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
     channel_id TEXT REFERENCES channels(channel_id),
     video_id TEXT NOT NULL UNIQUE,
     title TEXT NOT NULL,
     transcript TEXT NOT NULL,
     created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
   );

   -- Enable Row Level Security
   ALTER TABLE channels ENABLE ROW LEVEL SECURITY;
   ALTER TABLE transcripts ENABLE ROW LEVEL SECURITY;

   -- Create RLS policies for public read access
   CREATE POLICY "Allow public read on channels" ON channels
     FOR SELECT USING (true);
   CREATE POLICY "Allow public read on transcripts" ON transcripts
     FOR SELECT USING (true);

   -- Create policy for authenticated write access
   CREATE POLICY "Allow authenticated write on channels" ON channels
     FOR ALL TO authenticated USING (true);
   CREATE POLICY "Allow authenticated write on transcripts" ON transcripts
     FOR ALL TO authenticated USING (true);
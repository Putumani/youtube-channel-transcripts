import { useState, useEffect } from 'react';
import { supabase } from '@/lib/supabase';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { Toaster, useToast } from '@/components/ui/sonner';
import './index.css';

function App() {
  const [channelUrl, setChannelUrl] = useState('');
  const [apiKey, setApiKey] = useState('');
  const [channels, setChannels] = useState([]);
  const [transcripts, setTranscripts] = useState([]);
  const [loading, setLoading] = useState(false);
  const { toast } = useToast();

  useEffect(() => {
    fetchChannels();
  }, []);

  const fetchChannels = async () => {
    try {
      const { data, error } = await supabase.from('channels').select();
      if (error) throw error;
      setChannels(data || []);
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Failed to fetch channels: ' + error.message,
        variant: 'destructive',
      });
    }
  };

  const fetchTranscripts = async (channelId) => {
    try {
      const { data, error } = await supabase
        .from('transcripts')
        .select()
        .eq('channel_id', channelId);
      if (error) throw error;
      setTranscripts(data || []);
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Failed to fetch transcripts: ' + error.message,
        variant: 'destructive',
      });
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      toast({
        title: 'Processing',
        description:
          'Please run the backend script with the provided URL and API key.',
      });
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Failed to process request: ' + error.message,
        variant: 'destructive',
      });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="container mx-auto p-4">
      <Toaster />
      <h1 className="text-2xl font-bold mb-4">YouTube Transcript Scraper</h1>

      {/* Input Form */}
      <form onSubmit={handleSubmit} className="mb-6 space-y-4">
        <div>
          <label
            htmlFor="channelUrl"
            className="block text-sm font-medium mb-1"
          >
            YouTube Channel URL
          </label>
          <Input
            id="channelUrl"
            value={channelUrl}
            onChange={(e) => setChannelUrl(e.target.value)}
            placeholder="e.g., https://www.youtube.com/@channelhandle"
            disabled={loading}
          />
        </div>
        <div>
          <label htmlFor="apiKey" className="block text-sm font-medium mb-1">
            YouTube API Key
          </label>
          <Input
            id="apiKey"
            value={apiKey}
            onChange={(e) => setApiKey(e.target.value)}
            placeholder="Enter your YouTube API key"
            type="password"
            disabled={loading}
          />
        </div>
        <Button type="submit" disabled={loading}>
          {loading ? 'Processing...' : 'Fetch Transcripts'}
        </Button>
      </form>

      {/* Channels List */}
      <h2 className="text-xl font-semibold mb-2">Channels</h2>
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>Title</TableHead>
            <TableHead>Channel ID</TableHead>
            <TableHead>Actions</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {channels.map((channel) => (
            <TableRow key={channel.id}>
              <TableCell>{channel.title}</TableCell>
              <TableCell>{channel.channel_id}</TableCell>
              <TableCell>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => fetchTranscripts(channel.channel_id)}
                >
                  View Transcripts
                </Button>
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>

      {/* Transcripts List */}
      {transcripts.length > 0 && (
        <>
          <h2 className="text-xl font-semibold mt-6 mb-2">Transcripts</h2>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Title</TableHead>
                <TableHead>Video ID</TableHead>
                <TableHead>Transcript</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {transcripts.map((transcript) => (
                <TableRow key={transcript.id}>
                  <TableCell>{transcript.title}</TableCell>
                  <TableCell>{transcript.video_id}</TableCell>
                  <TableCell>
                    <div className="max-h-32 overflow-auto">
                      {transcript.transcript.split('\n').slice(0, 5).join('\n')}
                      {transcript.transcript.split('\n').length > 5 && '...'}
                    </div>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </>
      )}
    </div>
  );
}

export default App;

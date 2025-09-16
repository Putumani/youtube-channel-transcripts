import { useState, useEffect } from 'react'
import { supabase } from '@/lib/supabase'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { Toaster, useToast } from '@/components/ui/sonner'  // Import useToast directly from sonner
import { api } from '@/lib/api'
import './index.css'

function App() {
  const [channelUrl, setChannelUrl] = useState('')
  const [channels, setChannels] = useState([])
  const [transcripts, setTranscripts] = useState([])
  const [loading, setLoading] = useState(false)
  const [scraping, setScraping] = useState(false)

  useEffect(() => {
    fetchChannels()
  }, [])

  const fetchChannels = async () => {
    try {
      const { data, error } = await supabase.from('channels').select()
      if (error) throw error
      setChannels(data || [])
    } catch (error) {
      useToast({
        title: 'Error',
        description: 'Failed to fetch channels: ' + error.message,
        variant: 'destructive',
      })
    }
  }

  const fetchTranscripts = async (channelId) => {
    try {
      const { data, error } = await supabase
        .from('transcripts')
        .select()
        .eq('channel_id', channelId)
      if (error) throw error
      setTranscripts(data || [])
    } catch (error) {
      useToast({
        title: 'Error',
        description: 'Failed to fetch transcripts: ' + error.message,
        variant: 'destructive',
      })
    }
  }

  const handleScrapeTranscripts = async (e) => {
    e.preventDefault()
    setScraping(true)

    try {
      const result = await api.scrapeTranscripts(channelUrl, 3, 50)

      useToast({
        title: 'Success',
        description: `Processed ${result.videos_processed} videos from ${result.channel_title}`,
      })

      fetchChannels()

    } catch (error) {
      useToast({
        title: 'Error',
        description: 'Failed to scrape transcripts: ' + error.message,
        variant: 'destructive',
      })
    } finally {
      setScraping(false)
    }
  }

  return (
    <div className="container mx-auto p-4">
      <Toaster />  {/* Keep this for rendering toasts */}
      <h1 className="text-2xl font-bold mb-4">YouTube Transcript Scraper</h1>

      <form onSubmit={handleScrapeTranscripts} className="mb-6 space-y-4">
        <div>
          <label htmlFor="channelUrl" className="block text-sm font-medium mb-1">
            YouTube Channel URL
          </label>
          <Input
            id="channelUrl"
            value={channelUrl}
            onChange={(e) => setChannelUrl(e.target.value)}
            placeholder="e.g., https://www.youtube.com/@channelhandle"
            disabled={scraping}
            required
          />
        </div>
        <Button type="submit" disabled={scraping}>
          {scraping ? 'Scraping Transcripts...' : 'Scrape Transcripts'}
        </Button>
      </form>

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
  )
}

export default App

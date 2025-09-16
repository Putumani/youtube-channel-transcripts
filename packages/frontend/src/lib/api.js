const API_BASE_URL = import.meta.env.VITE_API_BASE_URL

if (!API_BASE_URL) {
    console.error('VITE_API_BASE_URL environment variable is not set')
}

export const api = {
    async scrapeTranscripts(channelUrl, delay = 3, maxVideos = 50) {
        const response = await fetch(`${API_BASE_URL}/api/scrape-transcripts`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                channel_url: channelUrl,
                delay,
                max_videos: maxVideos
            }),
        })

        if (!response.ok) {
            const error = await response.json()
            throw new Error(error.error || 'Failed to scrape transcripts')
        }

        return response.json()
    },

    async healthCheck() {
        const response = await fetch(`${API_BASE_URL}/api/health`)
        return response.json()
    }
}
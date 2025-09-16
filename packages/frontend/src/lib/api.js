const API_BASE_URL = import.meta.env.VITE_API_BASE_URL
const LOCAL_BASE_URL = import.meta.env.DEV

if (!API_BASE_URL && !LOCAL_BASE_URL) {
    console.error('VITE_API_BASE_URL environment variable is not set for production')
}

const getApiBaseUrl = () => {
    if (import.meta.env.DEV) {
        return 'http://localhost:5000'
    }
    if (!API_BASE_URL) {
        throw new Error('VITE_API_BASE_URL is required for production')
    }
    return API_BASE_URL
}

export const api = {
    async scrapeTranscripts(channelUrl, delay = 3, maxVideos = 50) {
        const baseUrl = getApiBaseUrl()
        const response = await fetch(`${baseUrl}/api/scrape-transcripts`, {
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
        const baseUrl = getApiBaseUrl()
        const response = await fetch(`${baseUrl}/api/health`)
        return response.json()
    }
}
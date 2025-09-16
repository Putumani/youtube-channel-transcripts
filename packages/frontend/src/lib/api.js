let API_BASE_URL;

if (!import.meta.env.PROD) {
    API_BASE_URL = 'https://youtube-channel-transcripts.onrender.com';
} else {
    API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'https://youtube-channel-transcripts.onrender.com';
}

if (!API_BASE_URL) {
    console.error('API_BASE_URL is not set');
    throw new Error('API_BASE_URL is not set');
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
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.error || 'Failed to scrape transcripts');
        }

        return response.json();
    },

    async healthCheck() {
        const response = await fetch(`${API_BASE_URL}/api/health`);
        return response.json();
    }
};
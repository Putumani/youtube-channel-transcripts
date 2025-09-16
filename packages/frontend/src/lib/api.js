let API_BASE_URL;

if (import.meta.env.MODE === 'development') {
    API_BASE_URL = 'https://youtube-channel-transcripts.onrender.com';
} else {
    API_BASE_URL = 'http://localhost:5000';
}

if (!API_BASE_URL) {
    console.error('API_BASE_URL is not set');
}

export const api = {
    async scrapeTranscripts(channelUrl, delay = 3, maxVideos = 50, cookiesFile = null) {
        const body = {
            channel_url: channelUrl,
            delay,
            max_videos: maxVideos
        };
        if (cookiesFile) {
            body.cookies_file = cookiesFile;
        }

        const response = await fetch(`${API_BASE_URL}/api/scrape-transcripts`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(body),
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
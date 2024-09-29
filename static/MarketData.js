document.addEventListener('DOMContentLoaded', () => {
    const socket = new WebSocket(`ws://${window.location.host}/ws`);
    const bidBody = document.getElementById('bid-body');
    const maxBids = 10; // Maximum number of bids to display

    socket.onopen = () => console.log("WebSocket connected");
    socket.onerror = (error) => console.error("WebSocket error:", error);

    socket.onmessage = (event) => {
        console.log("Received data:", event.data);
        const data = JSON.parse(event.data);
        if (data.type === 'market_data') {
            updateBidTable(data.data);
        }
    };

    function updateBidTable(data) {
        for (const [symbol, bidData] of Object.entries(data)) {
            const { bid, trader } = bidData;
            const time = new Date().toLocaleTimeString();

            const newRow = document.createElement('tr');
            newRow.innerHTML = `
                <td>${time}</td>
                <td>${symbol}</td>
                <td>${bid.toFixed(2)}</td>
            `;
            newRow.classList.add('new-bid');

            bidBody.insertBefore(newRow, bidBody.firstChild);

            // Remove excess rows
            while (bidBody.children.length > maxBids) {
                bidBody.removeChild(bidBody.lastChild);
            }

            // Set timeout for row expiration
            setTimeout(() => {
                newRow.classList.add('expired');
            }, 10000);
        }
    }

    // Clean up expired bids every second
    setInterval(() => {
        const now = Date.now();
        const rows = bidBody.children;
        for (let i = rows.length - 1; i >= 0; i--) {
            const row = rows[i];
            const time = new Date(row.firstChild.textContent).getTime();
            if (now - time > 10000) {
                bidBody.removeChild(row);
            }
        }
    }, 1000);
});
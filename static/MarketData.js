document.addEventListener('DOMContentLoaded', () => {
    const socket = new WebSocket(`ws://${window.location.host}/ws`);
    const bidButtons = document.querySelectorAll('.bid-button');
    const orderDetails = document.getElementById('order-details');

    let bids = {};

    socket.onmessage = (event) => {
        const data = JSON.parse(event.data);
        if (data.type === 'market_data') {
            updateBid(data.data);
        }
    };

    function updateBid(data) {
        const { symbol, bid, trader } = data;
        bids[trader] = { symbol, bid, timestamp: Date.now() };
        updateBidButtons();
    }

    function updateBidButtons() {
        const currentTime = Date.now();
        bidButtons.forEach((button) => {
            const trader = button.dataset.trader;
            const bidData = bids[trader];
            if (bidData && currentTime - bidData.timestamp < 12000) {
                button.textContent = `Bid ${bidData.bid.toFixed(2)}`;
                button.dataset.symbol = bidData.symbol;
                button.dataset.bid = bidData.bid;
                button.classList.remove('no-bid');
                button.disabled = false;
            } else {
                button.textContent = 'No Bid';
                button.classList.add('no-bid');
                button.disabled = true;
                delete button.dataset.symbol;
                delete button.dataset.bid;
            }
        });
    }

    bidButtons.forEach(button => {
        button.addEventListener('click', () => {
            if (!button.disabled) {
                const symbol = button.dataset.symbol;
                const bidValue = parseFloat(button.dataset.bid);
                const trader = button.dataset.trader;
                displayOrderDetails(symbol, bidValue, trader);
            }
        });
    });

    function displayOrderDetails(symbol, bidValue, trader) {
        orderDetails.innerHTML = `
            <h3>Order Details</h3>
            <p>Symbol: ${symbol}</p>
            <p>Bid Price: ${bidValue.toFixed(2)}</p>
            <p>Trader: ${trader}</p>
        `;
    }

    // Update bid buttons every second to check for timeouts
    setInterval(updateBidButtons, 1000);
});
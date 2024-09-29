document.addEventListener('DOMContentLoaded', () => {
    const socket = new WebSocket('ws://127.0.0.1:8000/ws');
    const bidButtons = document.querySelectorAll('.bid-button');
    const orderDetails = document.getElementById('order-details');

    socket.onmessage = (event) => {
        const data = JSON.parse(event.data);
        if (data.type === 'market_data') {
            updateBidButtons(data.data);
        }
    };

    function updateBidButtons(data) {
        const bids = Object.entries(data).flatMap(([symbol, item]) => [
            { symbol, bid: item.bid, trader: 'Trader 1' },
            { symbol, bid: item.bid * 0.999, trader: 'Trader 2' },
            { symbol, bid: item.bid * 0.998, trader: 'Trader 3' },
            { symbol, bid: item.bid * 0.997, trader: 'Trader 4' },
            { symbol, bid: item.bid * 0.996, trader: 'Trader 5' },
            { symbol, bid: item.bid * 0.995, trader: 'Trader 6' }
        ]).sort((a, b) => b.bid - a.bid).slice(0, 6);

        bidButtons.forEach((button, index) => {
            if (index < bids.length) {
                const { symbol, bid, trader } = bids[index];
                button.textContent = `${trader}: Bid ${bid.toFixed(2)}`;
                button.dataset.symbol = symbol;
                button.dataset.bid = bid;
                button.dataset.trader = trader;
                button.disabled = false;
            } else {
                button.textContent = 'No Bid';
                button.disabled = true;
                delete button.dataset.symbol;
                delete button.dataset.bid;
                delete button.dataset.trader;
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

    // Initial fetch of market data
    fetch('/update_market_data')
        .then(response => response.json())
        .then(data => {
            updateBidButtons(data);
        })
        .catch(error => console.error('Error fetching initial market data:', error));
});
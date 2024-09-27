document.addEventListener('DOMContentLoaded', () => {
    const socket = new WebSocket('ws://localhost:8000/ws');
    const connectionStatus = document.getElementById('connection-status');
    const marketDataContent = document.getElementById('market-data-content');
    const subscribeBtn = document.getElementById('subscribe-btn');
    const unsubscribeBtn = document.getElementById('unsubscribe-btn');
    const orderForm = document.getElementById('order-form');
    const orderMessage = document.getElementById('order-message');
    const statusForm = document.getElementById('status-form');

    let isSubscribed = false;

    socket.onopen = () => {
        connectionStatus.textContent = 'Connection Status: Connected';
        connectionStatus.className = 'connected';
    };

    socket.onclose = () => {
        connectionStatus.textContent = 'Connection Status: Disconnected';
        connectionStatus.className = 'disconnected';
    };

    socket.onmessage = (event) => {
        const data = JSON.parse(event.data);
        if (data.type === 'market_data' && isSubscribed) {
            updateMarketData(data.data);
        }
    };

    function updateMarketData(data) {
        marketDataContent.innerHTML = '';
        for (const [symbol, prices] of Object.entries(data)) {
            const symbolElement = document.createElement('div');
            symbolElement.className = 'market-data-item';
            symbolElement.innerHTML = `
                <strong>${symbol}</strong>
                <span>Bid: ${prices.bid.toFixed(2)}</span>
                <span>Ask: ${prices.ask.toFixed(2)}</span>
            `;
            marketDataContent.appendChild(symbolElement);
        }
    }

    subscribeBtn.addEventListener('click', () => {
        isSubscribed = true;
        marketDataContent.textContent = 'Subscribed to market data. Waiting for updates...';
    });

    unsubscribeBtn.addEventListener('click', () => {
        isSubscribed = false;
        marketDataContent.textContent = 'Unsubscribed from market data.';
    });

    orderForm.addEventListener('submit', (e) => {
        e.preventDefault();
        const formData = new FormData(orderForm);
        const order = {
            action: formData.get('action'),
            symbol: formData.get('symbol'),
            quantity: formData.get('quantity'),
            price: formData.get('price')
        };

        // Here you would typically send the order to your backend
        console.log('Order placed:', order);

        orderMessage.textContent = 'Order placed successfully!';
        orderMessage.className = '';
        setTimeout(() => {
            orderMessage.className = 'hidden';
        }, 3000);
    });

    statusForm.addEventListener('submit', (e) => {
        e.preventDefault();
        const formData = new FormData(statusForm);
        const clOrdID = formData.get('clordid');

        // Here you would typically check the order status with your backend
        console.log('Checking status for order:', clOrdID);
    });
});
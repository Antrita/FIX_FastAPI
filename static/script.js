document.addEventListener('DOMContentLoaded', () => {
    const socket = new WebSocket(`ws://${window.location.host}/ws`);
    const connectionStatus = document.getElementById('connection-status');
    const subscribeBtn = document.getElementById('subscribe-btn');
    const unsubscribeBtn = document.getElementById('unsubscribe-btn');
    const orderForm = document.getElementById('order-form');
    const orderMessage = document.getElementById('order-message');
    const statusForm = document.getElementById('status-form');
    const priceInput = document.getElementById('price-input');
    let isSubscribed = false;
    let marketDataWindow = null;

    if (socket) {
        socket.onopen = () => {
            if (connectionStatus) {
                connectionStatus.textContent = 'Connection Status: Connected';
                connectionStatus.className = 'connected';
            }
        };

        socket.onclose = () => {
            if (connectionStatus) {
                connectionStatus.textContent = 'Connection Status: Disconnected';
                connectionStatus.className = 'disconnected';
            }
        };

        socket.onmessage = (event) => {
            const data = JSON.parse(event.data);
            if (data.type === 'market_data') {
                console.log('Received market data:', data.data);
                // Handle market data update here
            }
        };
    }

    function updateMarketData(data) {
        // Update the UI with the received market data
        console.log('Received market data:', data);
    }

    if (subscribeBtn) {
        subscribeBtn.addEventListener('click', () => {
            isSubscribed = true;
            marketDataWindow = window.open('http://127.0.0.1:8000/MarketData.html', 'MarketData', 'width=600,height=400');
        });
    }

    if (unsubscribeBtn) {
        unsubscribeBtn.addEventListener('click', () => {
            isSubscribed = false;
            if (marketDataWindow) {
                marketDataWindow.close();
                marketDataWindow = null;
            }
        });
    }

    if (priceInput) {
        // Remove any event listeners that might be preventing input
        priceInput.disabled = false;
        priceInput.placeholder = 'Enter price';
    }

    if (orderForm) {
        orderForm.addEventListener('submit', (e) => {
            e.preventDefault();
            const formData = new FormData(orderForm);
            const order = {
                action: formData.get('action'),
                symbol: formData.get('symbol'),
                quantity: formData.get('quantity'),
                price: formData.get('price')
            };

            const clOrdID = generateClOrdID();
            console.log('Order placed:', order, 'ClOrdID:', clOrdID);

            if (orderMessage) {
                orderMessage.textContent = `Order placed successfully! ClOrdID: ${clOrdID}`;
                orderMessage.className = '';
                setTimeout(() => {
                    orderMessage.className = 'hidden';
                }, 3000);
            }
        });
    }

    if (statusForm) {
        statusForm.addEventListener('submit', (e) => {
            e.preventDefault();
            const formData = new FormData(statusForm);
            const clOrdID = formData.get('clordid');

            console.log('Checking status for order:', clOrdID);
        });
    }

    function generateClOrdID() {
        return 'ORD' + Math.random().toString(36).substr(2, 9);
    }
});
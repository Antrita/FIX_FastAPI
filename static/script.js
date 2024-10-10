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

        priceInput.disabled = false;
        priceInput.placeholder = 'Enter price';
    }

     if (orderForm) {
        orderForm.addEventListener('submit', (e) => {
            e.preventDefault();
            // Remove any check for isSubscribed here
            const formData = new FormData(orderForm);
            const order = {
                action: formData.get('action'),
                symbol: formData.get('symbol'),
                quantity: formData.get('quantity'),
                price: formData.get('price')
            };

             lastGeneratedClOrdID = generateClOrdID(); // Store the generated ClOrdID
            console.log('Order placed:', order, 'ClOrdID:', lastGeneratedClOrdID);

           if (orderMessage) {
                orderMessage.textContent = `Order placed successfully! ClOrdID: ${clOrdID}`;
                orderMessage.className = '';
                setTimeout(() => {
                    orderMessage.className = 'hidden';
                }, 5000);
            }
        });
    }

    if (statusForm) {
        statusForm.addEventListener('submit', (e) => {
            e.preventDefault();
            const formData = new FormData(statusForm);
            const clOrdID = formData.get('clordid');

            console.log('Checking status for order:', clOrdID);

            const statusResponse = document.getElementById('status-response');
            if (clOrdID === '12345') {
                // Fetch details from the order entry form
                const action = document.getElementById('action').value;
                const symbol = document.getElementById('symbol').value;
                const quantity = document.getElementById('quantity').value;
                const price = document.getElementById('price-input').value;

                statusResponse.innerHTML = `
                    <h3>Order Status:</h3>
                    <p>ClOrdID: 12345</p>
                    <p>Status: Order Placed</p>
                    <p>Action: ${action}</p>
                    <p>Symbol: ${symbol}</p>
                    <p>Quantity: ${quantity}</p>
                    <p>Price: ${price}</p>
                `;
                statusResponse.className = ''; // Remove 'hidden' class
            } else {
                statusResponse.textContent = 'Order not found.';
                statusResponse.className = ''; // Remove 'hidden' class
            }
        });
    }

    function generateClOrdID() {
        return 'ORD' + Math.random().toString(36).substr(2, 9);
    }
});
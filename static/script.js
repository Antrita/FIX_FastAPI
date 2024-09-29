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
    }

    if (subscribeBtn) {
        subscribeBtn.addEventListener('click', () => {
            isSubscribed = true;
            if (priceInput) {
                priceInput.disabled = false;
                priceInput.placeholder = '';
            }
            fetch('MarketData.html')
                .then(response => {
                    if (response.ok) {
                        window.location.href = 'MarketData.html';
                    } else {
                        throw new Error(`HTTP error! status: ${response.status}`);
                    }
                })
                .catch(error => {
                    console.error('Error:', error);
                    alert(`Unable to load Market Data page. Error: ${error.message}`);
                });
        });
    }

    if (unsubscribeBtn) {
        unsubscribeBtn.addEventListener('click', () => {
            isSubscribed = false;
            if (priceInput) {
                priceInput.disabled = true;
                priceInput.value = '';
                priceInput.placeholder = 'Please subscribe to Market Data first!';
            }
        });
    }

    if (priceInput) {
        priceInput.addEventListener('focus', () => {
            if (!isSubscribed) {
                priceInput.blur();
                priceInput.value = '';
                priceInput.placeholder = 'Please subscribe to Market Data first!';
            }
        });

        // Initialize price input state
        priceInput.disabled = true;
        priceInput.placeholder = 'Please subscribe to Market Data first!';
    }

    if (orderForm) {
        orderForm.addEventListener('submit', (e) => {
            e.preventDefault();
            if (!isSubscribed) {
                alert('Please subscribe to Market Data before placing an order.');
                return;
            }
            const formData = new FormData(orderForm);
            const order = {
                action: formData.get('action'),
                symbol: formData.get('symbol'),
                quantity: formData.get('quantity'),
                price: formData.get('price')
            };

            console.log('Order placed:', order);

            if (orderMessage) {
                orderMessage.textContent = 'Order placed successfully!';
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
});
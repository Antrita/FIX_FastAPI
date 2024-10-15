document.addEventListener('DOMContentLoaded', () => {
    generateDynamicForm(document.getElementById('order-type').value);

    document.getElementById('order-type').addEventListener('change', function() {
        generateDynamicForm(this.value);
    });

    const socket = new WebSocket(`ws://${window.location.host}/ws`);
    const connectionStatus = document.getElementById('connection-status');
    const subscribeBtn = document.getElementById('subscribe-btn');
    const unsubscribeBtn = document.getElementById('unsubscribe-btn');
    const orderForm = document.getElementById('order-form');
    const orderMessage = document.getElementById('order-message');
    const statusForm = document.getElementById('status-form');
    const priceInput = document.getElementById('price-input');
    const orderTypeSelect = document.getElementById('order-type');
    const limitFields = document.getElementById('limit-fields');
    const stopFields = document.getElementById('stop-fields');
    const stopLimitFields = document.getElementById('stop-limit-fields');
    let isSubscribed = false;
    let marketDataWindow = null;
  function generateDynamicForm(orderType) {
    const priceField = document.getElementById('price-field');
    const marketFields = document.getElementById('Market');
    const limitFields = document.getElementById('limit-fields');
    const stopFields = document.getElementById('stop-fields');
    const stopLimitFields = document.getElementById('stop-limit-fields');

    // Hide all fields initially
    priceField.style.display = 'none';
    marketFields.style.display = 'none';
    limitFields.style.display = 'none';
    stopFields.style.display = 'none';
    stopLimitFields.style.display = 'none';

    // Show specific fields based on order type
    switch (orderType) {
        case 'Market':
            priceField.style.display = 'block';
            break;
        case 'Limit':
            limitFields.style.display = 'block';
            break;
        case 'Stop':
            stopFields.style.display = 'block';
            break;
        case 'StopLimit':
            stopLimitFields.style.display = 'block';
            break;
    }
}
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
                updateMarketData(data.data);
            }
        };
    }

    function updateMarketData(data) {
        const marketDataContent = document.getElementById('market-data-content');
        if (marketDataContent) {
            marketDataContent.innerHTML = JSON.stringify(data, null, 2);
        }
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

    orderTypeSelect.addEventListener('change', () => {
        limitFields.style.display = 'none';
        stopFields.style.display = 'none';
        stopLimitFields.style.display = 'none';

        switch (orderTypeSelect.value) {
            case 'Limit':
                limitFields.style.display = 'block';
                break;
            case 'Stop':
                stopFields.style.display = 'block';
                break;
            case 'StopLimit':
                stopLimitFields.style.display = 'block';
                break;
        }
    });

    if (orderForm) {
        orderForm.addEventListener('submit', (e) => {
            e.preventDefault();
            const formData = new FormData(orderForm);
            const order = {
                action: formData.get('action'),
                symbol: formData.get('symbol'),
                quantity: formData.get('quantity'),
                orderType: formData.get('order-type'),
                price: formData.get('price')
            };

            // Generate dynamic form based on order type
            generateDynamicForm(order.orderType);

           switch (order.orderType) {
                case 'Limit':
                    order.limitPrice = formData.get('limit-price');
                    break;
                case 'Stop':
                    order.stopPrice = formData.get('stop-price');
                    break;
                case 'StopLimit':
                    order.stopPrice = formData.get('stop-limit-stop-price');
                    order.limitPrice = formData.get('stop-limit-limit-price');
                    break;
                }
            const lastGeneratedClOrdID = generateClOrdID();
            console.log('Order placed:', order, 'ClOrdID:', lastGeneratedClOrdID);

            if (orderMessage) {
                orderMessage.textContent = `Order placed successfully! ClOrdID: ${lastGeneratedClOrdID}`;
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
                const action = document.getElementById('action').value;
                const symbol = document.getElementById('symbol').value;
                const quantity = document.getElementById('quantity').value;
                const orderType = document.getElementById('order-type').value;
                const price = document.getElementById('price-input').value;

                let additionalInfo = '';
                switch (orderType) {
                    case 'Limit':
                        additionalInfo = `<p>Limit Price: ${document.getElementById('limit-price').value}</p>`;
                        break;
                    case 'Stop':
                        additionalInfo = `<p>Stop Price: ${document.getElementById('stop-price').value}</p>`;
                        break;
                    case 'StopLimit':
                        additionalInfo = `
                            <p>Stop Price: ${document.getElementById('stop-limit-stop-price').value}</p>
                            <p>Limit Price: ${document.getElementById('stop-limit-limit-price').value}</p>
                        `;
                        break;
                }

                statusResponse.innerHTML = `
                    <h3>Order Status:</h3>
                    <p>ClOrdID: ${clOrdID}</p>
                    <p>Status: Order Placed</p>
                    <p>Action: ${action}</p>
                    <p>Symbol: ${symbol}</p>
                    <p>Quantity: ${quantity}</p>
                    <p>Order Type: ${orderType}</p>
                    ${additionalInfo}
                    <p>Price: ${price}</p>
                `;
                statusResponse.className = '';
            } else {
                statusResponse.textContent = 'Order not found.';
                statusResponse.className = '';
            }
        });
    }

    function generateClOrdID() {
        return 'ORD' + Math.random().toString(36).substr(2, 9);
    }
});

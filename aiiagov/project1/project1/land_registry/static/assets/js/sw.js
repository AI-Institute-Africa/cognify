self.addEventListener('push', function(event) {
    const data = event.data.json();
    const options = {
        body: data.body,
        icon: '/static/assets/img/logo.png', // Fallback icon
        badge: '/static/assets/img/badge.png',
        data: data.url,
        vibrate: [200, 100, 200],
        actions: [
            { action: 'open', title: 'View Details' }
        ]
    };
    
    event.waitUntil(
        self.registration.showNotification(data.title, options)
    );
});

self.addEventListener('notificationclick', function(event) {
    event.notification.close();
    if (event.action === 'open') {
        event.waitUntil(
            clients.openWindow(event.notification.data)
        );
    }
});

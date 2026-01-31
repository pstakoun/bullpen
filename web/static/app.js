// Bullpen Web UI - Minimal JavaScript

// Auto-scroll log viewer when content is updated
document.body.addEventListener('htmx:afterSwap', function(evt) {
    if (evt.detail.target.id === 'log-viewer') {
        const logContent = document.getElementById('log-content');
        const autoScroll = document.getElementById('auto-scroll');
        if (logContent && autoScroll && autoScroll.checked) {
            logContent.scrollTop = logContent.scrollHeight;
        }
    }
});

// Refresh status after loop operations
document.body.addEventListener('refresh-status', function() {
    htmx.trigger(document.querySelector('[hx-get="/partials/status"]'), 'htmx:trigger');
    htmx.trigger(document.body, 'refresh-agents');
});

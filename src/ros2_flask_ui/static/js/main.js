document.addEventListener("DOMContentLoaded", function() {
    // Initialize Socket.IO
    const socket = io();

    // Initialize GridStack
    const grid = GridStack.init({
        cellHeight: '100px',
        margin: 10,
        float: true,
        disableOneColumnMode: true,
    });

    // Default Layout Definition
    const defaultLayout = [
        { id: 'raw', x: 0, y: 0, w: 6, h: 4, content: document.getElementById('template-raw').innerHTML },
        { id: 'seg', x: 6, y: 0, w: 6, h: 4, content: document.getElementById('template-seg').innerHTML },
        { id: 'topics', x: 0, y: 4, w: 6, h: 4, content: document.getElementById('template-topics').innerHTML },
        { id: 'services', x: 6, y: 4, w: 6, h: 4, content: document.getElementById('template-services').innerHTML },
    ];

    // Load layout
    function loadLayout() {
        grid.removeAll();
        // Just add the widgets defined in defaultLayout
        defaultLayout.forEach(widget => {
            const toggle = document.getElementById(`toggle-${widget.id}`);
            if (toggle && toggle.checked) {
                grid.addWidget(widget);
            }
        });
    }

    loadLayout();

    // Reset layout button
    document.getElementById('reset-layout').addEventListener('click', () => {
        const toggles = ['raw', 'seg', 'topics', 'services'];
        toggles.forEach(id => {
            document.getElementById(`toggle-${id}`).checked = true;
        });
        loadLayout();
    });

    // Handle toggles
    ['raw', 'seg', 'topics', 'services'].forEach(id => {
        const checkbox = document.getElementById(`toggle-${id}`);
        checkbox.addEventListener('change', (e) => {
            if (e.target.checked) {
                // Find widget in default and add
                const widgetDef = defaultLayout.find(w => w.id === id);
                if (widgetDef) grid.addWidget(widgetDef);
            } else {
                // Find visible widget and remove
                const el = document.querySelector(`[gs-id="${id}"]`);
                if (el) grid.removeWidget(el);
            }
        });
    });

    // Update Tables via Socket.IO
    socket.on('ros_data', function(data) {
        // Update Topics
        const topicsTable = document.querySelector('#topics-table tbody');
        if (topicsTable) {
            if (data.topics && data.topics.length > 0) {
                topicsTable.innerHTML = '';
                data.topics.forEach(t => {
                    const tr = document.createElement('tr');
                    tr.className = 'clickable-row';
                    tr.onclick = () => window.openTopicModal(t.name, t.types[0]);
                    tr.innerHTML = `<td>${t.name}</td><td><span class="tag bg-blue">${t.types.join(", ")}</span></td>`;
                    topicsTable.appendChild(tr);
                });
            } else {
                topicsTable.innerHTML = '<tr><td colspan="2" class="loading">No active topics found</td></tr>';
            }
        }

        // Update Services
        const servicesTable = document.querySelector('#services-table tbody');
        if (servicesTable) {
            if (data.services && data.services.length > 0) {
                servicesTable.innerHTML = '';
                data.services.forEach(s => {
                    // Filter out massive internal ROS parameter services for cleaner UI if preferred,
                    // but showing all is fine for introspection. We'll show all.
                    const tr = document.createElement('tr');
                    tr.className = 'clickable-row';
                    tr.onclick = () => window.openServiceModal(s.name, s.types[0]);
                    tr.innerHTML = `<td>${s.name}</td><td><span class="tag bg-green">${s.types.join(", ")}</span></td>`;
                    servicesTable.appendChild(tr);
                });
            } else {
                servicesTable.innerHTML = '<tr><td colspan="2" class="loading">No active services found</td></tr>';
            }
        }
    });

    // Modal Logic
    const modal = document.getElementById('data-modal');
    const modalTitle = document.getElementById('modal-title');
    const modalData = document.getElementById('modal-data');
    const closeBtn = document.querySelector('.close-btn');
    
    let currentTopic = null;

    window.openTopicModal = function(name, type) {
        currentTopic = name;
        modalTitle.textContent = `Topic: ${name} (${type})`;
        modalData.textContent = "Requesting subscription...";
        modal.style.display = 'flex';
        socket.emit('subscribe_topic', {topic: name, type: type});
    };

    window.openServiceModal = function(name, type) {
        modalTitle.textContent = `Service: ${name}`;
        modalData.textContent = `Service Type: ${type}\n\n(Service invocation not yet supported in this UI)`;
        modal.style.display = 'flex';
    };

    function closeModal() {
        if (modal) modal.style.display = 'none';
        if (currentTopic) {
            socket.emit('unsubscribe_topic', {topic: currentTopic});
            currentTopic = null;
            modalData.textContent = "";
        }
    }

    if (closeBtn) closeBtn.onclick = closeModal;
    window.onclick = function(event) {
        if (event.target == modal) {
            closeModal();
        }
    };

    socket.on('topic_data', function(data) {
        if (data.topic === currentTopic) {
            modalData.textContent = data.data;
        }
    });

});

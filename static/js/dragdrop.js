document.addEventListener('DOMContentLoaded', () => {
    const socket = io();
    const dropZone = document.getElementById('dropZone');
    const fileInput = document.getElementById('fileInput');
    const spinner = document.getElementById('spinner');
    const messageContainer = document.getElementById('messageContainer');

    // Debug logging for elements
    console.log('Elements found:', {
        dropZone: !!dropZone,
        fileInput: !!fileInput,
        spinner: !!spinner,
        messageContainer: !!messageContainer
    });

    // Check Socket.IO connection
    socket.on('connect', function() {
        console.log('Socket.IO connected');
        showMessage('Ready to upload files', 'info');
    });
    
    socket.on('disconnect', function() {
        console.log('Socket.IO disconnected');
        showMessage('Server connection lost, please refresh the page', 'error');
    });
    
    socket.on('connect_error', function(error) {
        console.error('Socket.IO connection error:', error);
        showMessage('Connection error, please refresh the page', 'error');
    });

    // File Input Click Handler
    const fileBtn = document.querySelector('.file-btn-wrapper');
    if (fileBtn) {
        fileBtn.addEventListener('click', function(e) {
            console.log('File button clicked');
            fileInput.click();
        });
    }

    // Prevent default drag behaviors
    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
        dropZone.addEventListener(eventName, preventDefaults, false);
        document.body.addEventListener(eventName, preventDefaults, false);
    });

    // Highlight drop zone when item is dragged over it
    ['dragenter', 'dragover'].forEach(eventName => {
        dropZone.addEventListener(eventName, highlight, false);
    });

    ['dragleave', 'drop'].forEach(eventName => {
        dropZone.addEventListener(eventName, unhighlight, false);
    });

    // Handle dropped files
    dropZone.addEventListener('drop', handleDrop, false);

    // Handle file input change
    fileInput.addEventListener('change', handleFileSelect, false);

    function preventDefaults (e) {
        e.preventDefault();
        e.stopPropagation();
    }

    function highlight(e) {
        console.log('File dragged over dropzone');
        dropZone.classList.add('highlight');
    }

    function unhighlight(e) {
        console.log('File drag ended');
        dropZone.classList.remove('highlight');
    }

    function handleDrop(e) {
        console.log('File dropped');
        const dt = e.dataTransfer;
        const file = dt.files[0];
        handleFile(file);
    }

    function handleFileSelect(e) {
        console.log('File selected via input');
        const file = e.target.files[0];
        handleFile(file);
    }

    function handleFile(file) {
        if (!file) {
            showMessage('No file selected', 'error');
            return;
        }

        // Log file information for debugging
        console.log('File selected:', file.name, 'Type:', file.type, 'Size:', file.size);

        // Enhanced PDF type checking - accept both standard MIME type and file extension
        const isPDF = file.type === 'application/pdf' || 
                    file.type === 'application/x-pdf' || 
                    file.name.toLowerCase().endsWith('.pdf');
                    
        if (!isPDF) {
            showMessage('Please upload a PDF file. The file you selected is: ' + file.type, 'error');
            return;
        }

        // Check file size (16MB max)
        if (file.size > 16 * 1024 * 1024) {
            showMessage('File is too large. Maximum size is 16MB.', 'error');
            return;
        }

        // Show loading spinner
        spinner.style.display = 'block';
        messageContainer.style.display = 'block';
        showMessage('Uploading file...', 'info');

        // Read file as base64
        const reader = new FileReader();
        reader.readAsDataURL(file);
        
        reader.onerror = function() {
            console.error('FileReader error:', reader.error);
            showMessage('Error reading file: ' + reader.error, 'error');
            spinner.style.display = 'none';
        };
        
        reader.onload = function() {
            try {
                const base64String = reader.result.split(',')[1];
                console.log('File read successfully, size of base64:', base64String.length);
                showMessage('Processing file, please wait...', 'info');
                
                // Add timeout handling
                let responseReceived = false;
                const timeoutId = setTimeout(() => {
                    if (!responseReceived) {
                        showMessage('Server is taking too long to respond. The file might be too complex or the server might be busy.', 'error');
                        spinner.style.display = 'none';
                    }
                }, 60000); // 60 second timeout
                
                // Emit file data to server
                socket.emit('process_file', {
                    file: base64String,
                    filename: file.name
                });
                
                console.log('File data emitted to server');
                
                // Create one-time handler for this specific upload
                const responseHandler = function(data) {
                    console.log('Received response from server:', data);
                    responseReceived = true;
                    clearTimeout(timeoutId);
                    spinner.style.display = 'none';
                    
                    if (data.error) {
                        showMessage(data.error, 'error');
                    } else {
                        showMessage('File processed successfully!', 'success');
                        // Reload the page to display the results
                        window.location.reload();
                    }
                };
                
                // Remove any existing handlers and add new one
                socket.off('file_response');
                socket.on('file_response', responseHandler);
                
            } catch (error) {
                console.error('Error processing file:', error);
                showMessage('Error processing file: ' + error.message, 'error');
                spinner.style.display = 'none';
            }
        };
    }

    socket.on('download_response', function(data) {
        if (data.error) {
            showMessage(data.error, 'error');
        } else {
            // Create blob from base64 data
            const blob = base64ToBlob(data.file_data);
            // Create download link
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = data.filename;
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
            document.body.removeChild(a);
        }
    });

    function showMessage(message, type) {
        console.log(`Message (${type}):`, message);
        messageContainer.textContent = message;
        messageContainer.className = 'message-container ' + type;
        messageContainer.style.display = 'block';
    }

    function base64ToBlob(base64) {
        const byteCharacters = atob(base64);
        const byteArrays = [];

        for (let offset = 0; offset < byteCharacters.length; offset += 512) {
            const slice = byteCharacters.slice(offset, offset + 512);
            const byteNumbers = new Array(slice.length);
            
            for (let i = 0; i < slice.length; i++) {
                byteNumbers[i] = slice.charCodeAt(i);
            }

            const byteArray = new Uint8Array(byteNumbers);
            byteArrays.push(byteArray);
        }

        return new Blob(byteArrays, {type: 'text/html'});
    }
});

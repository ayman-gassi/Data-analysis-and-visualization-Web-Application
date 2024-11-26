function displayFileInfo() {
    // document.getElementById('erroDesc').innerHTML = "";
    const fileInput = document.getElementById('uploadFile1');
    const fileInfoDiv = document.getElementById('fileInfo');
    if (fileInput.files.length > 0) {
        const file = fileInput.files[0];
        const fileSize = (file.size / 1024).toFixed(2); 
        fileInfoDiv.innerHTML = `
            <p><strong>File Name:</strong> ${file.name}</p>
            <p><strong>Size:</strong> ${fileSize} KB</p>
        `;
    } else {
        fileInfoDiv.innerHTML = "";
    }
}
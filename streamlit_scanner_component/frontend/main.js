// main.js

import { Streamlit } from "streamlit-component-lib";

document.addEventListener('DOMContentLoaded', (event) => {
    Streamlit.setComponentReady();
    
    const videoElement = document.getElementById('scanner-video');
    const resultElement = document.getElementById('result');
    const codeReader = new ZXing.BrowserCodeReader();
    
    // Get the camera stream
    navigator.mediaDevices.getUserMedia({ video: { facingMode: 'environment' } })
        .then((stream) => {
            // Assign the stream to the video element for rendering
            videoElement.srcObject = stream;
            videoElement.play();
            
            // Pass the raw stream to ZXing to handle the scanning
            codeReader.decodeFromStream(stream, videoElement, (result, err) => {
                if (result) {
                    resultElement.innerText = `Encontrado: ${result.getText()}`;
                    Streamlit.setComponentValue(result.getText());
                    // Stop scanning after a result is found
                    codeReader.reset();
                    stream.getTracks().forEach(track => track.stop());
                }
                if (err && !(err instanceof ZXing.NotFoundException)) {
                    console.error(err);
                    resultElement.innerText = "Error al escanear: " + err;
                }
            });
        })
        .catch((err) => {
            resultElement.innerText = "Error: No se pudo acceder a la cámara.";
            console.error("Error al acceder a la cámara:", err);
        });
});
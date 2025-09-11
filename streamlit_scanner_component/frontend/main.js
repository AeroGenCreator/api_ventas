window.addEventListener('load', (event) => {

    const videoElement = document.getElementById('scanner-video');
    const resultElement = document.getElementById('result');

    const codeReader = new ZXing.BrowserCodeReader();
    
    codeReader.decodeFromVideoDevice(null, videoElement, (result, err) => {
        if (result) {
            resultElement.innerText = `Found ${result.getText()}`;
            window.parent.postMessage({
                type: "streamlit:setComponentValue",
                value: result.getText(),
            }, "*");
        }
        if (err && !(err instanceof ZXing.NotFoundException)) {
            console.error(err);
        }
    });
});
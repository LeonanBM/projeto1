document.addEventListener("DOMContentLoaded", function () {
    const video = document.getElementById("video");
    const canvas = document.getElementById("canvas");
    const captureBtn = document.getElementById("capture-btn");
    const imageInput = document.getElementById("image-input");

    // Função para inicializar a câmera
    function initializeCamera() {
        navigator.mediaDevices
            .getUserMedia({ video: true })
            .then(function (stream) {
                video.srcObject = stream;
            })
            .catch(function (err) {
                console.log("Erro ao acessar a câmera: ", err);
            });
    }

    // Inicializar a câmera ao carregar a página
    initializeCamera();

    captureBtn.addEventListener("click", function () {
        canvas.width = video.videoWidth;
        canvas.height = video.videoHeight;
        canvas.getContext("2d").drawImage(video, 0, 0, canvas.width, canvas.height);

        canvas.toBlob(function (blob) {
            const formData = new FormData();

            if (blob) {
                const file = new File([blob], "snapshot.png", { type: "image/png" });
                formData.append("image", file);

                // Submeta o formulário
                submitForm(formData);
            } else {
                console.log("Erro ao capturar a foto. Nenhum blob disponível.");
            }
        }, "image/png");
    });

    function submitForm(formData) {
        fetch("/upload/", {
            method: "POST",
            body: formData,
            headers: {
                "X-CSRFToken": getCookie("csrftoken"),
            },
        })
        .then((response) => {
            if (!response.ok) {
                throw new Error(`HTTP error! Status: ${response.status}`);
            }
            return response.text(); // Alterado para response.text() para lidar com a resposta HTML
        })
        .then((html) => {
            document.body.innerHTML = html; // Atualiza o conteúdo do corpo da página com a resposta HTML

            // Reinicialize a câmera após a verificação
            initializeCamera();

            // Agende um redirecionamento/recarregamento após 5 segundos
            setTimeout(function () {
                location.reload();
            }, 5000);
        })
        .catch((error) => {
            console.error("Erro no envio da imagem: ", error);
        });
    }

    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== "") {
            const cookies = document.cookie.split(";");
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === name + "=") {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }
});

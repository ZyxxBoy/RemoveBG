/**
 * AI Background Remover — Frontend Logic
 * =======================================
 * Handles drag-&-drop, file upload, preview, processing, and result display.
 */

(() => {
    "use strict";

    // ----- DOM refs -----
    const dropZone = document.getElementById("drop-zone");
    const fileInput = document.getElementById("file-input");
    const previewWrapper = document.getElementById("preview-wrapper");
    const previewImg = document.getElementById("preview-img");
    const removeBtn = document.getElementById("remove-btn");
    const uploadSection = document.getElementById("upload-section");
    const loadingSection = document.getElementById("loading-section");
    const resultSection = document.getElementById("result-section");
    const resultOriginal = document.getElementById("result-original");
    const resultProcessed = document.getElementById("result-processed");
    const downloadBtn = document.getElementById("download-btn");
    const newUploadBtn = document.getElementById("new-upload-btn");
    const errorToast = document.getElementById("error-toast");
    const errorText = document.getElementById("error-text");

    const MAX_SIZE = 5 * 1024 * 1024; // 5 MB
    const ALLOWED = ["image/jpeg", "image/png", "image/jpg"];
    let selectedFile = null;

    // ----- Helpers -----
    function showError(msg) {
        errorText.textContent = msg;
        errorToast.classList.remove("hidden");
        errorToast.classList.add("show");
        setTimeout(() => {
            errorToast.classList.add("hidden");
            errorToast.classList.remove("show");
        }, 4000);
    }

    function validateFile(file) {
        if (!file) return false;
        if (!ALLOWED.includes(file.type)) {
            showError("Invalid file type. Please upload a JPG, JPEG, or PNG image.");
            return false;
        }
        if (file.size > MAX_SIZE) {
            showError("File too large. Maximum size is 5 MB.");
            return false;
        }
        return true;
    }

    function showPreview(file) {
        const reader = new FileReader();
        reader.onload = (e) => {
            previewImg.src = e.target.result;
            previewWrapper.classList.remove("hidden");
        };
        reader.readAsDataURL(file);
    }

    function setLoading(on) {
        if (on) {
            uploadSection.classList.add("hidden");
            resultSection.classList.add("hidden");
            loadingSection.classList.remove("hidden");
        } else {
            loadingSection.classList.add("hidden");
        }
    }

    function showResult(originalUrl, processedUrl) {
        resultOriginal.src = originalUrl;
        resultProcessed.src = processedUrl;
        downloadBtn.href = processedUrl;
        resultSection.classList.remove("hidden");
    }

    function resetUI() {
        selectedFile = null;
        fileInput.value = "";
        previewWrapper.classList.add("hidden");
        previewImg.src = "";
        resultSection.classList.add("hidden");
        uploadSection.classList.remove("hidden");
    }

    // ----- Drag & drop -----
    ["dragenter", "dragover"].forEach((evt) => {
        dropZone.addEventListener(evt, (e) => {
            e.preventDefault();
            dropZone.classList.add("drag-over");
        });
    });

    ["dragleave", "drop"].forEach((evt) => {
        dropZone.addEventListener(evt, (e) => {
            e.preventDefault();
            dropZone.classList.remove("drag-over");
        });
    });

    dropZone.addEventListener("drop", (e) => {
        const file = e.dataTransfer.files[0];
        if (validateFile(file)) {
            selectedFile = file;
            showPreview(file);
        }
    });

    // ----- File input change -----
    fileInput.addEventListener("change", () => {
        const file = fileInput.files[0];
        if (validateFile(file)) {
            selectedFile = file;
            showPreview(file);
        }
    });

    // ----- Remove Background -----
    removeBtn.addEventListener("click", async () => {
        if (!selectedFile) {
            showError("Please select an image first.");
            return;
        }

        setLoading(true);

        const formData = new FormData();
        formData.append("image", selectedFile);

        try {
            const res = await fetch("/remove", { method: "POST", body: formData });
            const data = await res.json();

            if (!res.ok) {
                throw new Error(data.error || "Something went wrong.");
            }

            setLoading(false);
            showResult(data.original, data.processed);
        } catch (err) {
            setLoading(false);
            uploadSection.classList.remove("hidden");
            showError(err.message || "Processing failed. Please try again.");
        }
    });

    // ----- New image -----
    newUploadBtn.addEventListener("click", resetUI);
})();

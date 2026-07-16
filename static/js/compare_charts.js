document.addEventListener("DOMContentLoaded", () => {
    const container = document.getElementById("modelData");

    const rfAccuracy = parseFloat(container.dataset.rfAccuracy);
    const nbAccuracy = parseFloat(container.dataset.nbAccuracy);
    const rfTraining = parseFloat(container.dataset.rfTraining) * 1000; // ms
    const rfPrediction = parseFloat(container.dataset.rfPrediction) * 1000;
    const nbTraining = parseFloat(container.dataset.nbTraining) * 1000; // ms
    const nbPrediction = parseFloat(container.dataset.nbPrediction) * 1000;

    // Accuracy Chart
    new Chart(document.getElementById("accuracyChart"), {
        type: 'bar',
        data: {
            labels: ["Random Forest", "Naive Bayes"],
            datasets: [{
                label: "Accuracy (%)",
                data: [rfAccuracy * 100, nbAccuracy * 100],
                backgroundColor: ["#007bff", "#28a745"]
            }]
        },
        options: { responsive: true, plugins: { legend: { display: false } } }
    });

    // Correct vs Incorrect
    new Chart(document.getElementById("correctIncorrectChart"), {
        type: 'bar',
        data: {
            labels: ["Correct (%)", "Incorrect (%)"],
            datasets: [
                { label: "Random Forest", data: [rfAccuracy*100, (1-rfAccuracy)*100], backgroundColor: "#007bff" },
                { label: "Naive Bayes", data: [nbAccuracy*100, (1-nbAccuracy)*100], backgroundColor: "#28a745" }
            ]
        },
        options: { responsive: true }
    });

    // Time Efficiency
    new Chart(document.getElementById("timeChart"), {
        type: 'bar',
        data: {
            labels: ["Training Time (ms)", "Prediction Time (ms)"],
            datasets: [
                { label: "Random Forest", data: [rfTraining, rfPrediction], backgroundColor: "#007bff" },
                { label: "Naive Bayes", data: [nbTraining, nbPrediction], backgroundColor: "#28a745" }
            ]
        },
        options: { responsive: true }
    });
});

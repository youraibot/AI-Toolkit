import React from 'react';
import { Line } from 'react-chartjs-2';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
} from 'chart.js';

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend
);

function JobAnalytics({ jobDetails }) {
    if (!jobDetails || !jobDetails.metrics || jobDetails.metrics.length === 0) {
        return <p>No performance metrics available for this job.</p>;
    }

    // --- Data Processing ---
    const trainingLogs = jobDetails.metrics.filter(m => m.loss);
    const evalLogs = jobDetails.metrics.filter(m => m.eval_loss);

    const labels = evalLogs.map(m => `Epoch ${m.epoch.toFixed(2)}`);

    // --- Chart Data ---
    const chartData = {
        labels: labels,
        datasets: [
            {
                label: 'Training Loss',
                data: evalLogs.map(log => {
                    const trainLog = trainingLogs.find(t => t.epoch === log.epoch);
                    return trainLog ? trainLog.loss : null;
                }),
                borderColor: '#61dafb',
                backgroundColor: 'rgba(97, 218, 251, 0.5)',
                yAxisID: 'y',
            },
            {
                label: 'Evaluation Loss',
                data: evalLogs.map(m => m.eval_loss),
                borderColor: '#ff6b6b',
                backgroundColor: 'rgba(255, 107, 107, 0.5)',
                yAxisID: 'y',
            },
        ],
    };

    // --- Chart Options ---
    const chartOptions = {
        responsive: true,
        interaction: {
            mode: 'index',
            intersect: false,
        },
        plugins: {
            legend: { position: 'top', labels: { color: '#f0f0f0' } },
            title: { display: true, text: 'Training vs. Evaluation Loss', color: '#f0f0f0' },
        },
        scales: {
            y: {
                type: 'linear',
                display: true,
                position: 'left',
                title: { display: true, text: 'Loss', color: '#f0f0f0' },
                ticks: { color: '#f0f0f0' },
            },
            x: {
                ticks: { color: '#f0f0f0' },
            }
        },
    };

    // --- Final Metrics Scorecard ---
    const finalMetrics = evalLogs.length > 0 ? evalLogs[evalLogs.length - 1] : null;

    return (
        <div className="job-analytics">
            <h4>Performance Analytics</h4>

            {finalMetrics && (
                <div className="scorecard-container">
                    <div className="scorecard">
                        <h5>Final Eval Loss</h5>
                        <p>{finalMetrics.eval_loss.toFixed(4)}</p>
                    </div>
                    {finalMetrics.eval_accuracy && (
                        <div className="scorecard">
                            <h5>Final Accuracy</h5>
                            <p>{(finalMetrics.eval_accuracy * 100).toFixed(2)}%</p>
                        </div>
                    )}
                    {finalMetrics.eval_perplexity && (
                         <div className="scorecard">
                            <h5>Final Perplexity</h5>
                            <p>{finalMetrics.eval_perplexity.toFixed(2)}</p>
                        </div>
                    )}
                </div>
            )}

            {evalLogs.length > 0 ? (
                <Line options={chartOptions} data={chartData} />
            ) : (
                <p>No evaluation metrics to display. The job may still be running or was run without an evaluation dataset.</p>
            )}
        </div>
    );
}

export default JobAnalytics;

import React, { useEffect, useRef } from 'react';
import { Chart as ChartJS, RadialLinearScale, PointElement, LineElement, Filler, Tooltip, Legend } from 'chart.js';
import { Radar } from 'react-chartjs-2';

ChartJS.register(RadialLinearScale, PointElement, LineElement, Filler, Tooltip, Legend);

interface SkillRadarChartProps {
  data: {
    labels: string[];
    values: number[];
    max_value: number;
  };
}

const SkillRadarChart: React.FC<SkillRadarChartProps> = ({ data }) => {
  if (!data || !data.labels || !data.values) {
    return (
      <div className="flex items-center justify-center h-64 text-gray-500">
        No skill data available
      </div>
    );
  }

  const chartData = {
    labels: data.labels,
    datasets: [
      {
        label: 'Skill Level',
        data: data.values,
        backgroundColor: 'rgba(59, 130, 246, 0.2)',
        borderColor: 'rgba(59, 130, 246, 1)',
        borderWidth: 2,
        pointBackgroundColor: 'rgba(59, 130, 246, 1)',
        pointBorderColor: '#fff',
        pointHoverBackgroundColor: '#fff',
        pointHoverBorderColor: 'rgba(59, 130, 246, 1)',
        pointRadius: 4,
        pointHoverRadius: 6,
      },
    ],
  };

  const options = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        display: false,
      },
      tooltip: {
        callbacks: {
          label: function(context: any) {
            return `${context.label}: ${context.parsed.r.toFixed(1)}/${data.max_value}`;
          },
        },
      },
    },
    scales: {
      r: {
        beginAtZero: true,
        max: data.max_value,
        min: 0,
        ticks: {
          stepSize: 1,
          color: '#6B7280',
          font: {
            size: 12,
          },
        },
        grid: {
          color: '#E5E7EB',
        },
        pointLabels: {
          color: '#374151',
          font: {
            size: 12,
            weight: 'bold',
          },
        },
      },
    },
  };

  return (
    <div className="h-64">
      <Radar data={chartData} options={options} />
    </div>
  );
};

export default SkillRadarChart;

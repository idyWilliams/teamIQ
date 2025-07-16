import React from 'react'
import { RadarChart } from '../ui/Chart'
import { ChartData } from '../../types'
import Card, { CardHeader, CardContent } from '../ui/Card'

interface SkillRadarChartProps {
  data: {
    categories: Record<string, number>
    detailed_skills: Record<string, any[]>
    overall_score: number
  }
  className?: string
}

const SkillRadarChart: React.FC<SkillRadarChartProps> = ({ data, className }) => {
  const chartData: ChartData = {
    labels: Object.keys(data.categories),
    datasets: [
      {
        label: 'Skill Proficiency',
        data: Object.values(data.categories),
        backgroundColor: 'rgba(30, 64, 175, 0.2)',
        borderColor: 'rgba(30, 64, 175, 1)',
        borderWidth: 2,
      },
    ],
  }

  const chartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        display: false,
      },
    },
    scales: {
      r: {
        beginAtZero: true,
        max: 100,
        ticks: {
          display: false,
        },
        grid: {
          color: 'rgba(0, 0, 0, 0.1)',
        },
        angleLines: {
          color: 'rgba(0, 0, 0, 0.1)',
        },
      },
    },
  }

  return (
    <Card className={className}>
      <CardHeader
        title="Skill Proficiency"
        subtitle={`Overall Score: ${data.overall_score.toFixed(1)}/100`}
      />
      <CardContent>
        <div className="h-80">
          <RadarChart data={chartData} options={chartOptions} />
        </div>
        
        <div className="mt-4 grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {Object.entries(data.categories).map(([category, score]) => (
            <div
              key={category}
              className="flex items-center justify-between p-3 bg-gray-50 rounded-lg"
            >
              <span className="text-sm font-medium text-gray-700 capitalize">
                {category.replace('_', ' ')}
              </span>
              <span className="text-sm font-bold text-primary-600">
                {score.toFixed(1)}
              </span>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  )
}

export default SkillRadarChart

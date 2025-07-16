import React from 'react'
import { LineChart } from '../ui/Chart'
import { ChartData } from '../../types'
import Card, { CardHeader, CardContent } from '../ui/Card'
import Badge from '../ui/Badge'

interface SentimentChartProps {
  data: {
    overall_sentiment: string
    trend: string
    sentiment_timeline: Array<{
      date: string
      sentiment_score: number
      message_count: number
    }>
    team_health_score: number
  }
  className?: string
}

const SentimentChart: React.FC<SentimentChartProps> = ({ data, className }) => {
  const chartData: ChartData = {
    labels: data.sentiment_timeline.map(point => 
      new Date(point.date).toLocaleDateString()
    ),
    datasets: [
      {
        label: 'Sentiment Score',
        data: data.sentiment_timeline.map(point => point.sentiment_score),
        borderColor: 'rgba(34, 197, 94, 1)',
        backgroundColor: 'rgba(34, 197, 94, 0.1)',
        borderWidth: 2,
        fill: true,
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
      y: {
        beginAtZero: true,
        max: 1,
        ticks: {
          callback: (value: any) => `${(value * 100).toFixed(0)}%`,
        },
      },
    },
  }

  const getSentimentColor = (sentiment: string) => {
    switch (sentiment) {
      case 'positive':
        return 'success'
      case 'negative':
        return 'error'
      case 'neutral':
        return 'secondary'
      default:
        return 'default'
    }
  }

  const getTrendColor = (trend: string) => {
    switch (trend) {
      case 'improving':
        return 'success'
      case 'declining':
        return 'error'
      case 'stable':
        return 'secondary'
      default:
        return 'default'
    }
  }

  return (
    <Card className={className}>
      <CardHeader
        title="Team Sentiment"
        subtitle="Communication sentiment analysis over time"
      />
      <CardContent>
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center space-x-4">
            <div>
              <p className="text-sm text-gray-600">Overall Sentiment</p>
              <Badge
                variant={getSentimentColor(data.overall_sentiment)}
                className="mt-1"
              >
                {data.overall_sentiment}
              </Badge>
            </div>
            <div>
              <p className="text-sm text-gray-600">Trend</p>
              <Badge
                variant={getTrendColor(data.trend)}
                className="mt-1"
              >
                {data.trend}
              </Badge>
            </div>
          </div>
          
          <div className="text-right">
            <p className="text-sm text-gray-600">Health Score</p>
            <p className="text-2xl font-bold text-primary-600">
              {(data.team_health_score * 100).toFixed(0)}%
            </p>
          </div>
        </div>
        
        <div className="h-64">
          <LineChart data={chartData} options={chartOptions} />
        </div>
        
        <div className="mt-4 text-sm text-gray-500">
          <p>
            Based on {data.sentiment_timeline.reduce((sum, point) => sum + point.message_count, 0)} messages analyzed
          </p>
        </div>
      </CardContent>
    </Card>
  )
}

export default SentimentChart

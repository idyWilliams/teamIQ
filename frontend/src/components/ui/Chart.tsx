import React from 'react'
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend,
  ArcElement,
  LineElement,
  PointElement,
  RadialLinearScale,
} from 'chart.js'
import { Bar, Doughnut, Line, Radar } from 'react-chartjs-2'
import { ChartData, ChartOptions } from '../../types'

ChartJS.register(
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend,
  ArcElement,
  LineElement,
  PointElement,
  RadialLinearScale,
)

interface BaseChartProps {
  data: ChartData
  options?: ChartOptions
  className?: string
  height?: number
}

interface ChartProps extends BaseChartProps {
  type: 'bar' | 'line' | 'doughnut' | 'radar'
}

const Chart: React.FC<ChartProps> = ({ type, data, options, className, height = 300 }) => {
  const defaultOptions: ChartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: 'top' as const,
      },
      tooltip: {
        enabled: true,
      },
    },
    ...options,
  }

  const chartProps = {
    data,
    options: defaultOptions,
    height,
  }

  return (
    <div className={className} style={{ height }}>
      {type === 'bar' && <Bar {...chartProps} />}
      {type === 'line' && <Line {...chartProps} />}
      {type === 'doughnut' && <Doughnut {...chartProps} />}
      {type === 'radar' && <Radar {...chartProps} />}
    </div>
  )
}

export const BarChart: React.FC<BaseChartProps> = (props) => (
  <Chart {...props} type="bar" />
)

export const LineChart: React.FC<BaseChartProps> = (props) => (
  <Chart {...props} type="line" />
)

export const DoughnutChart: React.FC<BaseChartProps> = (props) => (
  <Chart {...props} type="doughnut" />
)

export const RadarChart: React.FC<BaseChartProps> = (props) => (
  <Chart {...props} type="radar" />
)

export default Chart

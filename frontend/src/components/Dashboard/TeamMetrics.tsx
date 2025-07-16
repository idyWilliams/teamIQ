import React from 'react'
import { Users, TrendingUp, Award, AlertTriangle } from 'lucide-react'
import { BarChart, DoughnutChart } from '../ui/Chart'
import { ChartData } from '../../types'
import Card, { CardHeader, CardContent } from '../ui/Card'
import DashboardCard from './DashboardCard'

interface TeamMetricsProps {
  data: {
    total_members: number
    active_projects: number
    completed_projects: number
    project_completion_rate: number
    skill_coverage: Record<string, number>
    team_strengths: Array<{
      skill: string
      average_score: number
      coverage: number
    }>
    team_weaknesses: Array<{
      skill: string
      average_score: number
      coverage: number
    }>
  }
  className?: string
}

const TeamMetrics: React.FC<TeamMetricsProps> = ({ data, className }) => {
  const skillCoverageData: ChartData = {
    labels: Object.keys(data.skill_coverage),
    datasets: [
      {
        label: 'Average Skill Level',
        data: Object.values(data.skill_coverage),
        backgroundColor: [
          'rgba(30, 64, 175, 0.8)',
          'rgba(59, 130, 246, 0.8)',
          'rgba(147, 197, 253, 0.8)',
          'rgba(34, 197, 94, 0.8)',
          'rgba(251, 191, 36, 0.8)',
          'rgba(239, 68, 68, 0.8)',
        ],
        borderColor: [
          'rgba(30, 64, 175, 1)',
          'rgba(59, 130, 246, 1)',
          'rgba(147, 197, 253, 1)',
          'rgba(34, 197, 94, 1)',
          'rgba(251, 191, 36, 1)',
          'rgba(239, 68, 68, 1)',
        ],
        borderWidth: 1,
      },
    ],
  }

  const strengthsData: ChartData = {
    labels: data.team_strengths.slice(0, 5).map(s => s.skill),
    datasets: [
      {
        label: 'Score',
        data: data.team_strengths.slice(0, 5).map(s => s.average_score),
        backgroundColor: 'rgba(34, 197, 94, 0.8)',
        borderColor: 'rgba(34, 197, 94, 1)',
        borderWidth: 1,
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
        max: 100,
      },
    },
  }

  return (
    <div className={className}>
      {/* Overview Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-6">
        <DashboardCard
          title="Team Members"
          value={data.total_members}
          icon={Users}
          iconColor="text-blue-600"
        />
        <DashboardCard
          title="Active Projects"
          value={data.active_projects}
          icon={TrendingUp}
          iconColor="text-green-600"
        />
        <DashboardCard
          title="Completed Projects"
          value={data.completed_projects}
          icon={Award}
          iconColor="text-purple-600"
        />
        <DashboardCard
          title="Completion Rate"
          value={`${data.project_completion_rate.toFixed(1)}%`}
          icon={AlertTriangle}
          iconColor="text-orange-600"
        />
      </div>

      {/* Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card>
          <CardHeader title="Skill Coverage" />
          <CardContent>
            <div className="h-64">
              <DoughnutChart data={skillCoverageData} />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader title="Team Strengths" />
          <CardContent>
            <div className="h-64">
              <BarChart data={strengthsData} options={chartOptions} />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Strengths and Weaknesses */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mt-6">
        <Card>
          <CardHeader title="Top Skills" />
          <CardContent>
            <div className="space-y-3">
              {data.team_strengths.slice(0, 5).map((strength, index) => (
                <div key={strength.skill} className="flex items-center justify-between">
                  <div className="flex items-center">
                    <span className="text-sm font-medium text-gray-900">
                      {strength.skill}
                    </span>
                    <span className="text-xs text-gray-500 ml-2">
                      ({strength.coverage} members)
                    </span>
                  </div>
                  <div className="flex items-center">
                    <div className="w-20 bg-gray-200 rounded-full h-2 mr-2">
                      <div
                        className="bg-green-500 h-2 rounded-full"
                        style={{ width: `${strength.average_score}%` }}
                      />
                    </div>
                    <span className="text-sm font-medium text-gray-900">
                      {strength.average_score.toFixed(0)}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader title="Skills to Improve" />
          <CardContent>
            <div className="space-y-3">
              {data.team_weaknesses.slice(0, 5).map((weakness, index) => (
                <div key={weakness.skill} className="flex items-center justify-between">
                  <div className="flex items-center">
                    <span className="text-sm font-medium text-gray-900">
                      {weakness.skill}
                    </span>
                    <span className="text-xs text-gray-500 ml-2">
                      ({weakness.coverage} members)
                    </span>
                  </div>
                  <div className="flex items-center">
                    <div className="w-20 bg-gray-200 rounded-full h-2 mr-2">
                      <div
                        className="bg-red-500 h-2 rounded-full"
                        style={{ width: `${weakness.average_score}%` }}
                      />
                    </div>
                    <span className="text-sm font-medium text-gray-900">
                      {weakness.average_score.toFixed(0)}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}

export default TeamMetrics

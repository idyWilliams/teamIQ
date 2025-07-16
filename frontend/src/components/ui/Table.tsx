import React from 'react'
import { ChevronUp, ChevronDown } from 'lucide-react'
import { cn } from '../../lib/utils'
import { TableColumn, TableProps } from '../../types'
import LoadingSpinner from './LoadingSpinner'

const Table: React.FC<TableProps> = ({
  columns,
  data,
  loading = false,
  sortBy,
  sortOrder,
  onSort,
  onRowClick,
  className,
}) => {
  const handleSort = (column: string) => {
    if (onSort) {
      onSort(column)
    }
  }

  if (loading) {
    return (
      <div className="flex justify-center items-center py-8">
        <LoadingSpinner size="md" />
      </div>
    )
  }

  if (data.length === 0) {
    return (
      <div className="text-center py-8 text-gray-500">
        <p>No data available</p>
      </div>
    )
  }

  return (
    <div className={cn('overflow-x-auto', className)}>
      <table className="min-w-full divide-y divide-gray-200">
        <thead className="bg-gray-50">
          <tr>
            {columns.map((column) => (
              <th
                key={column.key}
                className={cn(
                  'px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider',
                  column.sortable && 'cursor-pointer hover:bg-gray-100',
                  column.className
                )}
                onClick={() => column.sortable && handleSort(column.key)}
              >
                <div className="flex items-center space-x-1">
                  <span>{column.label}</span>
                  {column.sortable && (
                    <span className="flex flex-col">
                      <ChevronUp
                        className={cn(
                          'h-3 w-3',
                          sortBy === column.key && sortOrder === 'asc'
                            ? 'text-primary-600'
                            : 'text-gray-400'
                        )}
                      />
                      <ChevronDown
                        className={cn(
                          'h-3 w-3 -mt-1',
                          sortBy === column.key && sortOrder === 'desc'
                            ? 'text-primary-600'
                            : 'text-gray-400'
                        )}
                      />
                    </span>
                  )}
                </div>
              </th>
            ))}
          </tr>
        </thead>
        <tbody className="bg-white divide-y divide-gray-200">
          {data.map((row, index) => (
            <tr
              key={index}
              className={cn(
                'hover:bg-gray-50 transition-colors',
                onRowClick && 'cursor-pointer'
              )}
              onClick={() => onRowClick && onRowClick(row)}
            >
              {columns.map((column) => (
                <td
                  key={column.key}
                  className={cn(
                    'px-6 py-4 whitespace-nowrap text-sm text-gray-900',
                    column.className
                  )}
                >
                  {column.render
                    ? column.render(row[column.key], row)
                    : row[column.key]}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

export default Table

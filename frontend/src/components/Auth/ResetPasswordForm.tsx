import React, { useState } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import { Mail, Lock, Eye, EyeOff } from 'lucide-react'
import { authApi } from '../../lib/api'
import Button from '../ui/Button'
import Input from '../ui/Input'
import { isValidEmail, isValidPassword, getPasswordStrength } from '../../lib/utils'
import toast from 'react-hot-toast'

const ResetPasswordForm: React.FC = () => {
  const [searchParams] = useSearchParams()
  const token = searchParams.get('token')
  const [step, setStep] = useState<'request' | 'confirm'>(token ? 'confirm' : 'request')
  
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [showPassword, setShowPassword] = useState(false)
  const [showConfirmPassword, setShowConfirmPassword] = useState(false)
  
  const [errors, setErrors] = useState<Record<string, string>>({})
  const [loading, setLoading] = useState(false)

  const validateEmail = (): boolean => {
    const newErrors: Record<string, string> = {}

    if (!email) {
      newErrors.email = 'Email is required'
    } else if (!isValidEmail(email)) {
      newErrors.email = 'Please enter a valid email address'
    }

    setErrors(newErrors)
    return Object.keys(newErrors).length === 0
  }

  const validatePassword = (): boolean => {
    const newErrors: Record<string, string> = {}

    if (!password) {
      newErrors.password = 'Password is required'
    } else if (!isValidPassword(password)) {
      newErrors.password = 'Password must be at least 8 characters with uppercase, lowercase, and number'
    }

    if (!confirmPassword) {
      newErrors.confirmPassword = 'Please confirm your password'
    } else if (password !== confirmPassword) {
      newErrors.confirmPassword = 'Passwords do not match'
    }

    setErrors(newErrors)
    return Object.keys(newErrors).length === 0
  }

  const handleRequestReset = async (e: React.FormEvent) => {
    e.preventDefault()
    
    if (!validateEmail()) return

    setLoading(true)
    try {
      await authApi.requestPasswordReset(email)
      toast.success('Password reset link sent to your email')
      setStep('confirm')
    } catch (error: any) {
      toast.error(error.message || 'Failed to send reset link')
    } finally {
      setLoading(false)
    }
  }

  const handleConfirmReset = async (e: React.FormEvent) => {
    e.preventDefault()
    
    if (!validatePassword()) return
    if (!token) {
      toast.error('Invalid reset token')
      return
    }

    setLoading(true)
    try {
      await authApi.confirmPasswordReset(token, password)
      toast.success('Password reset successfully')
      // Redirect to login
      window.location.href = '/login'
    } catch (error: any) {
      toast.error(error.message || 'Failed to reset password')
    } finally {
      setLoading(false)
    }
  }

  const passwordStrength = getPasswordStrength(password)

  if (step === 'request') {
    return (
      <form onSubmit={handleRequestReset} className="space-y-6">
        <div>
          <Input
            type="email"
            name="email"
            label="Email address"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            error={errors.email}
            icon={<Mail />}
            placeholder="Enter your email"
            required
          />
        </div>

        <Button
          type="submit"
          variant="primary"
          size="lg"
          loading={loading}
          className="w-full"
        >
          Send Reset Link
        </Button>

        <div className="text-center">
          <Link
            to="/login"
            className="font-medium text-primary-600 hover:text-primary-500"
          >
            Back to Sign In
          </Link>
        </div>
      </form>
    )
  }

  return (
    <form onSubmit={handleConfirmReset} className="space-y-6">
      <div>
        <div className="relative">
          <Input
            type={showPassword ? 'text' : 'password'}
            name="password"
            label="New Password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            error={errors.password}
            icon={<Lock />}
            placeholder="Enter new password"
            required
          />
          <button
            type="button"
            className="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-400 hover:text-gray-600"
            onClick={() => setShowPassword(!showPassword)}
          >
            {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
          </button>
        </div>
        
        {password && (
          <div className="mt-2">
            <div className="flex items-center space-x-2">
              <div className="flex-1 bg-gray-200 rounded-full h-2">
                <div
                  className={`h-2 rounded-full transition-all ${
                    passwordStrength.score <= 2 ? 'bg-red-500' :
                    passwordStrength.score <= 3 ? 'bg-yellow-500' :
                    'bg-green-500'
                  }`}
                  style={{ width: `${(passwordStrength.score / 5) * 100}%` }}
                />
              </div>
              <span className="text-xs text-gray-500">
                {passwordStrength.score <= 2 ? 'Weak' :
                 passwordStrength.score <= 3 ? 'Medium' :
                 'Strong'}
              </span>
            </div>
          </div>
        )}
      </div>

      <div>
        <div className="relative">
          <Input
            type={showConfirmPassword ? 'text' : 'password'}
            name="confirmPassword"
            label="Confirm New Password"
            value={confirmPassword}
            onChange={(e) => setConfirmPassword(e.target.value)}
            error={errors.confirmPassword}
            icon={<Lock />}
            placeholder="Confirm new password"
            required
          />
          <button
            type="button"
            className="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-400 hover:text-gray-600"
            onClick={() => setShowConfirmPassword(!showConfirmPassword)}
          >
            {showConfirmPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
          </button>
        </div>
      </div>

      <Button
        type="submit"
        variant="primary"
        size="lg"
        loading={loading}
        className="w-full"
      >
        Reset Password
      </Button>

      <div className="text-center">
        <Link
          to="/login"
          className="font-medium text-primary-600 hover:text-primary-500"
        >
          Back to Sign In
        </Link>
      </div>
    </form>
  )
}

export default ResetPasswordForm

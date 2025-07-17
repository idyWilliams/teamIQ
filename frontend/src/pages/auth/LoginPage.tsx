import React from "react";
import { Navigate } from "react-router-dom";
import { Shield } from "lucide-react";

import LoadingSpinner from "../../components/ui/LoadingSpinner";
import LoginForm from "../../components/Auth/LoginForm";
import { useAuth } from "../../hooks/useAuth";

const LoginPage: React.FC = () => {
  const { user, isLoading } = useAuth();

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <LoadingSpinner size="lg" />
      </div>
    );
  }

  if (user) {
    return <Navigate to="/" replace />;
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-md w-full space-y-8">
        <div>
          <div className="flex justify-center">
            <div className="bg-primary-600 rounded-lg p-3">
              <Shield className="h-8 w-8 text-white" />
            </div>
          </div>
          <h2 className="mt-6 text-center text-3xl font-extrabold text-gray-900">
            Welcome to iSentry TeamIQ
          </h2>
          <p className="mt-2 text-center text-sm text-gray-600">
            AI-Powered Team Intelligence Platform
          </p>
        </div>

        <div className="bg-white py-8 px-6 shadow-lg rounded-lg">
          <LoginForm />
        </div>

        <div className="text-center">
          <p className="text-sm text-gray-600">
            Don't have an account?{" "}
            <a
              href="#"
              className="font-medium text-primary-600 hover:text-primary-500"
            >
              Contact your administrator
            </a>
          </p>
        </div>
      </div>
    </div>
  );
};

export default LoginPage;

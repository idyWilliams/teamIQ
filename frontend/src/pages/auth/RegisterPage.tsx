import React from 'react';
import RegisterForm from '../../components/Auth/RegisterForm';

const RegisterPage: React.FC = () => {
  return (
    <div className="flex items-center justify-center min-h-screen bg-gray-100">
      <div className="w-full max-w-md p-8 space-y-8 bg-white rounded-lg shadow-md">
        <h2 className="text-2xl font-bold text-center text-gray-900">
          Create your account
        </h2>
        <RegisterForm />
      </div>
    </div>
  );
};

export default RegisterPage;
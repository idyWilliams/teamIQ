import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '../services/api';
import { toast } from 'react-hot-toast';

interface UseApiOptions {
  onSuccess?: (data: any) => void;
  onError?: (error: any) => void;
  showSuccessToast?: boolean;
  showErrorToast?: boolean;
}

export const useApi = () => {
  const queryClient = useQueryClient();

  const useGet = (key: string[], endpoint: string, options: UseApiOptions = {}) => {
    return useQuery({
      queryKey: key,
      queryFn: async () => {
        const response = await api.get(endpoint);
        return response.data;
      },
      onSuccess: (data) => {
        if (options.onSuccess) {
          options.onSuccess(data);
        }
      },
      onError: (error: any) => {
        if (options.showErrorToast !== false) {
          toast.error(error.response?.data?.detail || 'An error occurred');
        }
        if (options.onError) {
          options.onError(error);
        }
      },
    });
  };

  const usePost = (endpoint: string, options: UseApiOptions = {}) => {
    return useMutation({
      mutationFn: async (data: any) => {
        const response = await api.post(endpoint, data);
        return response.data;
      },
      onSuccess: (data) => {
        if (options.showSuccessToast !== false) {
          toast.success('Operation completed successfully');
        }
        if (options.onSuccess) {
          options.onSuccess(data);
        }
      },
      onError: (error: any) => {
        if (options.showErrorToast !== false) {
          toast.error(error.response?.data?.detail || 'An error occurred');
        }
        if (options.onError) {
          options.onError(error);
        }
      },
    });
  };

  const usePut = (endpoint: string, options: UseApiOptions = {}) => {
    return useMutation({
      mutationFn: async (data: any) => {
        const response = await api.put(endpoint, data);
        return response.data;
      },
      onSuccess: (data) => {
        if (options.showSuccessToast !== false) {
          toast.success('Updated successfully');
        }
        if (options.onSuccess) {
          options.onSuccess(data);
        }
      },
      onError: (error: any) => {
        if (options.showErrorToast !== false) {
          toast.error(error.response?.data?.detail || 'Update failed');
        }
        if (options.onError) {
          options.onError(error);
        }
      },
    });
  };

  const useDelete = (endpoint: string, options: UseApiOptions = {}) => {
    return useMutation({
      mutationFn: async (id: string | number) => {
        const response = await api.delete(`${endpoint}/${id}`);
        return response.data;
      },
      onSuccess: (data) => {
        if (options.showSuccessToast !== false) {
          toast.success('Deleted successfully');
        }
        if (options.onSuccess) {
          options.onSuccess(data);
        }
      },
      onError: (error: any) => {
        if (options.showErrorToast !== false) {
          toast.error(error.response?.data?.detail || 'Delete failed');
        }
        if (options.onError) {
          options.onError(error);
        }
      },
    });
  };

  const invalidateQueries = (queryKey: string[]) => {
    queryClient.invalidateQueries({ queryKey });
  };

  return {
    useGet,
    usePost,
    usePut,
    useDelete,
    invalidateQueries,
  };
};

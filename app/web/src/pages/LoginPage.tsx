import { useState } from 'react';
import { useNavigationStore } from '../stores/navigationStore';
import { useAuthStore } from '../stores/authStore';

export function LoginPage() {
  const { setCurrentPage } = useNavigationStore();
  const { login } = useAuthStore();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  const handleBackToLanding = () => {
    setCurrentPage('landing');
    setError('');
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setIsLoading(true);

    try {
      const result = await login(email, password);
      if (result.success) {
        setCurrentPage('learn');
      } else {
        setError(result.error || 'Login failed');
      }
    } catch (err) {
      setError('An error occurred. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleDemoLogin = async () => {
    setEmail('demo@hackaton.ia');
    setPassword('demo123!');
    setError('');
    setIsLoading(true);

    try {
      const result = await login('demo@hackaton.ia', 'demo123!');
      if (result.success) {
        setCurrentPage('learn');
      } else {
        setError(result.error || 'Login failed');
      }
    } catch (err) {
      setError('An error occurred. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 flex items-center justify-center p-4">
      <div className="w-full max-w-md">
        {/* Header */}
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold text-gray-900 mb-2">Ensenia</h1>
          <p className="text-gray-600">Ingresa a tu cuenta</p>
        </div>

        {/* Login Card */}
        <div className="bg-white rounded-lg shadow-lg p-8 mb-6">
          <form onSubmit={handleSubmit} className="space-y-4">
            {/* Email Input */}
            <div>
              <label htmlFor="email" className="block text-sm font-medium text-gray-700 mb-2">
                Correo Electrónico
              </label>
              <input
                id="email"
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="ejemplo@correo.com"
                disabled={isLoading}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500 disabled:bg-gray-100"
                required
              />
            </div>

            {/* Password Input */}
            <div>
              <label htmlFor="password" className="block text-sm font-medium text-gray-700 mb-2">
                Contraseña
              </label>
              <input
                id="password"
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••"
                disabled={isLoading}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500 disabled:bg-gray-100"
                required
              />
            </div>

            {/* Error Message */}
            {error && (
              <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg text-sm">
                {error}
              </div>
            )}

            {/* Login Button */}
            <button
              type="submit"
              disabled={isLoading}
              className="w-full bg-indigo-600 hover:bg-indigo-700 disabled:bg-indigo-400 text-white font-bold py-2 px-4 rounded-lg transition mt-6"
            >
              {isLoading ? 'Ingresando...' : 'Ingresar'}
            </button>
          </form>

          {/* Demo Login */}
          <div className="mt-6 pt-6 border-t border-gray-200">
            <p className="text-sm text-gray-600 text-center mb-3">Credenciales de demostración:</p>
            <div className="bg-gray-50 rounded-lg p-3 text-xs text-gray-700 mb-4 space-y-1">
              <p>
                <span className="font-semibold">Correo:</span> demo@hackaton.ia
              </p>
              <p>
                <span className="font-semibold">Contraseña:</span> demo123!
              </p>
            </div>
            <button
              onClick={handleDemoLogin}
              disabled={isLoading}
              className="w-full bg-gray-200 hover:bg-gray-300 disabled:bg-gray-100 text-gray-800 font-semibold py-2 px-4 rounded-lg transition"
            >
              Usar Credenciales de Demo
            </button>
          </div>
        </div>

        {/* Back Button */}
        <button
          onClick={handleBackToLanding}
          className="w-full text-center text-indigo-600 hover:text-indigo-700 font-semibold transition"
        >
          ← Volver a Inicio
        </button>
      </div>
    </div>
  );
}

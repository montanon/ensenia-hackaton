export const EvaluacionPage = () => {
  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-50 via-white to-indigo-50 p-8">
      <div className="max-w-4xl mx-auto">
        <h1 className="text-4xl font-bold text-gray-800 mb-4">Evaluación</h1>
        <p className="text-lg text-gray-600 mb-8">
          Evalúa tus conocimientos y obtén retroalimentación personalizada.
        </p>

        <div className="bg-white rounded-xl shadow-lg p-8 border border-purple-100">
          <div className="text-center py-12">
            <div className="w-20 h-20 mx-auto mb-6 bg-purple-100 rounded-full flex items-center justify-center">
              <svg className="w-10 h-10 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4" />
              </svg>
            </div>
            <h2 className="text-2xl font-semibold text-gray-800 mb-2">
              Evaluaciones Personalizadas
            </h2>
            <p className="text-gray-600">
              Próximamente podrás realizar evaluaciones adaptadas a tu nivel de aprendizaje
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

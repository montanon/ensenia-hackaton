import { useNavigationStore } from '../stores/navigationStore';

export function LandingPage() {
  const { setCurrentPage } = useNavigationStore();

  const handleGetStarted = () => {
    setCurrentPage('login');
  };

  return (
    <div className="min-h-screen bg-white flex flex-col items-center justify-center px-4 relative overflow-visible">
      {/* Bottom Left Image - Background */}
      <img
        src="/8598879.jpg"
        alt="Decorative"
        className="absolute -bottom-16 left-0 h-96 md:h-[420px] lg:h-[70vh] object-cover opacity-90 z-0 scale-x-[-1]"
      />

      <div className="text-center w-full relative z-10 -translate-y-32">
        {/* Title */}
        <h1 className="text-8xl md:text-9xl lg:text-[140px] font-bold tracking-tight mb-6 md:mb-8 leading-none">
          Enseñ<span className="text-blue-600">IA</span>
        </h1>

        {/* Subtitle */}
        <p className="text-3xl md:text-4xl lg:text-5xl text-gray-700 font-medium leading-tight mb-6 md:mb-8">
          Aprende, Practica, Repasa, Evalúa...
        </p>

        {/* CTA Button */}
        <button
          onClick={handleGetStarted}
          className="bg-blue-600 hover:bg-blue-700 text-white font-semibold py-5 px-20 md:py-6 md:px-24 rounded-lg transition duration-200 hover:shadow-lg text-2xl md:text-3xl"
        >
          Pruébala!
        </button>
      </div>
    </div>
  );
}

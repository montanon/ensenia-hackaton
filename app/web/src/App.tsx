import { useEffect } from 'react';
import { Sidebar } from './components/layout/Sidebar';
import { BubbleAssistant } from './components/bubble/BubbleAssistant';
import { BubbleChatWindow } from './components/bubble/BubbleChatWindow';
import { LearnPage } from './pages/LearnPage';
import { PracticePage } from './pages/PracticePage';
import { ReviewPage } from './pages/ReviewPage';
import { EvaluacionPage } from './pages/EvaluacionPage';
import { LandingPage } from './pages/LandingPage';
import { LoginPage } from './pages/LoginPage';
import { useNavigationStore } from './stores/navigationStore';
import { useAuthStore } from './stores/authStore';
import { useSessionStore } from './stores/sessionStore';

function App() {
  const { currentPage, setCurrentPage } = useNavigationStore();
  const { isAuthenticated, initializeAuth } = useAuthStore();
  const { clearSession } = useSessionStore();

  // Initialize app state on load
  useEffect(() => {
    // Initialize auth from localStorage
    initializeAuth();

    // Check if user has valid auth token
    const hasAuthToken = !!localStorage.getItem('authToken');

    // Clear any stale session data and navigate to valid initial state
    clearSession();

    // Set initial page based on auth status
    if (hasAuthToken) {
      setCurrentPage('learn');
    } else {
      setCurrentPage('landing');
    }
  }, []);

  // Reset page to landing if user logs out
  useEffect(() => {
    if (!isAuthenticated && (currentPage === 'learn' || currentPage === 'practice' || currentPage === 'review' || currentPage === 'evaluacion')) {
      setCurrentPage('landing');
    }
  }, [isAuthenticated, currentPage, setCurrentPage]);

  const renderPage = () => {
    // If not authenticated, only show landing or login pages
    if (!isAuthenticated) {
      switch (currentPage) {
        case 'login':
          return <LoginPage />;
        case 'landing':
        default:
          return <LandingPage />;
      }
    }

    // If authenticated, show main app pages
    switch (currentPage) {
      case 'learn':
        return <LearnPage />;
      case 'practice':
        return <PracticePage />;
      case 'review':
        return <ReviewPage />;
      case 'evaluacion':
        return <EvaluacionPage />;
      case 'landing':
      case 'login':
        return <LearnPage />; // Redirect to learn if already logged in
      default:
        return <LearnPage />;
    }
  };

  // For authenticated users, show full app layout with sidebar
  if (isAuthenticated && (currentPage === 'learn' || currentPage === 'practice' || currentPage === 'review' || currentPage === 'evaluacion')) {
    return (
      <div className="flex h-screen overflow-hidden">
        {/* Sidebar - always visible */}
        <Sidebar />

        {/* Main content area */}
        <main className="flex-1 overflow-hidden flex flex-col relative">
          {renderPage()}
          <BubbleAssistant />
        </main>

        {/* Chat panel */}
        <BubbleChatWindow />
      </div>
    );
  }

  // For unauthenticated users, show full screen pages
  return renderPage();
}

export default App;

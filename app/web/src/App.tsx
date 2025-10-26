import { useEffect } from 'react';
import { AppLayout } from './components/layout/AppLayout';
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

function App() {
  const { currentPage, setCurrentPage } = useNavigationStore();
  const { isAuthenticated, initializeAuth } = useAuthStore();

  // Initialize auth state from localStorage on app load
  useEffect(() => {
    initializeAuth();
  }, [initializeAuth]);

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

  // For authenticated users, show full app layout
  if (isAuthenticated && (currentPage === 'learn' || currentPage === 'practice' || currentPage === 'review' || currentPage === 'evaluacion')) {
    return (
      <div className="flex h-screen overflow-hidden">
        <div className="flex-1 overflow-auto relative">
          <AppLayout>
            {renderPage()}
          </AppLayout>
          <BubbleAssistant />
        </div>
        <BubbleChatWindow />
      </div>
    );
  }

  // For unauthenticated users, show full screen pages
  return renderPage();
}

export default App;

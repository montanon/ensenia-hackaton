import { AppLayout } from './components/layout/AppLayout';
import { BubbleAssistant } from './components/bubble/BubbleAssistant';
import { BubbleChatWindow } from './components/bubble/BubbleChatWindow';
import { LearnPage } from './pages/LearnPage';
import { PracticePage } from './pages/PracticePage';
import { ReviewPage } from './pages/ReviewPage';
import { EvaluacionPage } from './pages/EvaluacionPage';
import { useNavigationStore } from './stores/navigationStore';

function App() {
  const { currentPage } = useNavigationStore();

  const renderPage = () => {
    switch (currentPage) {
      case 'learn':
        return <LearnPage />;
      case 'practice':
        return <PracticePage />;
      case 'review':
        return <ReviewPage />;
      case 'evaluacion':
        return <EvaluacionPage />;
      default:
        return <LearnPage />;
    }
  };

  return (
    <div className="flex h-screen bg-gray-50">
      <AppLayout>
        {renderPage()}
      </AppLayout>
      <BubbleAssistant />
      <BubbleChatWindow />
    </div>
  );
}

export default App;

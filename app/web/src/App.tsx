import { AppLayout } from './components/layout/AppLayout';
import { BubbleAssistant } from './components/bubble/BubbleAssistant';
import { BubbleChatWindow } from './components/bubble/BubbleChatWindow';
import { LearnPage } from './pages/LearnPage';
import { PracticePage } from './pages/PracticePage';
import { ReviewPage } from './pages/ReviewPage';
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
      default:
        return <LearnPage />;
    }
  };

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

export default App;

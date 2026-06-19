import { useState } from 'react';
import { AnimatePresence, motion } from 'framer-motion';
import { DashboardLayout } from './components/Layout/DashboardLayout';
import { ChatPage } from './pages/ChatPage';
import { DocumentsPage } from './pages/DocumentsPage';
import { SettingsPage } from './pages/SettingsPage';

const pageTransition = {
  initial: { opacity: 0, y: 8 },
  animate: { opacity: 1, y: 0 },
  exit: { opacity: 0, y: -8 },
  transition: { duration: 0.2, ease: 'easeOut' as const },
};

function App() {
  const [activeTab, setActiveTab] = useState<string>('chat');

  const renderActivePage = () => {
    switch (activeTab) {
      case 'chat':
        return <ChatPage />;
      case 'documents':
        return <DocumentsPage />;
      case 'settings':
        return <SettingsPage />;
      default:
        return <ChatPage />;
    }
  };

  return (
    <DashboardLayout activeTab={activeTab} setActiveTab={setActiveTab}>
      <AnimatePresence mode="wait">
        <motion.div
          key={activeTab}
          className="flex-1 flex flex-col h-full overflow-hidden"
          {...pageTransition}
        >
          {renderActivePage()}
        </motion.div>
      </AnimatePresence>
    </DashboardLayout>
  );
}

export default App;

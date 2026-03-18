import AppLayout from './components/layout/AppLayout'
import ChatContainer from './components/chat/ChatContainer'
import DataPreviewPanel from './components/data/DataPreviewPanel'
import SecurityBadge from './components/security/SecurityBadge'

export default function App() {
  return (
    <>
      <AppLayout rightPanel={<DataPreviewPanel />}>
        <ChatContainer />
      </AppLayout>
      <SecurityBadge />
    </>
  )
}

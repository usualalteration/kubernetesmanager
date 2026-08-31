import ChatInterface from "@/components/dashboard/ChatInterface";
import Header from "@/components/Header";

const Chat = () => {
  return (
    <div className="min-h-screen bg-background flex flex-col">
      <Header />

      {/* Chat Interface - full height below header */}
      <div className="flex-1 overflow-hidden">
        <ChatInterface />
      </div>
    </div>
  );
};

export default Chat;
